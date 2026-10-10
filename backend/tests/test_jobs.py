"""
Automated Unit Tests for Persistent Job Processing and Worker Framework.
"""

import time
from quantumshield.models.job import ScanJob
from quantumshield.models.asset import Asset
from quantumshield.storage.job_repository import JobRepository
from quantumshield.storage.repositories import AssetRepository
from quantumshield.services.job_worker import BackgroundJobManager


def test_create_and_persist_job(client):
    """Test creating and retrieving a scan job through the REST API."""
    res_asset = client.post("/api/v1/assets", json={
        "name": "Target Server",
        "asset_type": "server",
        "environment": "production",
    })
    asset_id = res_asset.get_json()["asset"]["id"]

    job_payload = {
        "asset_id": asset_id,
        "job_type": "certificate_scan",
        "operation": "inspect_x509_certificate",
    }
    response = client.post("/api/v1/jobs", json=job_payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data["status"] == "ok"
    assert "job" in data
    job = data["job"]
    assert job["asset_id"] == asset_id
    assert job["job_type"] == "certificate_scan"
    assert job["status"] in ("pending", "queued")
    assert job["id"].startswith("job_")

    get_res = client.get(f"/api/v1/jobs/{job['id']}")
    assert get_res.status_code == 200
    assert get_res.get_json()["job"]["id"] == job["id"]


def test_reject_job_for_nonexistent_asset(client):
    """Verify creating a job for a missing asset fails with 404."""
    response = client.post("/api/v1/jobs", json={
        "asset_id": "ast_missing_999",
        "job_type": "tls_scan",
        "operation": "handshake_probe",
    })
    assert response.status_code == 404
    assert "does not exist" in response.get_json()["error"].lower()


def test_cancel_job(client):
    """Verify cancelling an eligible job transitions state to 'cancelled'."""
    res_asset = client.post("/api/v1/assets", json={"name": "Cancel Test Asset", "asset_type": "website", "environment": "staging"})
    asset_id = res_asset.get_json()["asset"]["id"]

    res_job = client.post("/api/v1/jobs", json={"asset_id": asset_id, "job_type": "static_scan", "operation": "scan_directory"})
    job_id = res_job.get_json()["job"]["id"]

    cancel_res = client.post(f"/api/v1/jobs/{job_id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.get_json()["job"]["status"] == "cancelled"

    get_res = client.get(f"/api/v1/jobs/{job_id}")
    assert get_res.get_json()["job"]["status"] == "cancelled"


def test_retry_job_and_limit_enforcement(app, client):
    """Verify job retry resets status and enforces max_retries limit."""
    res_asset = client.post("/api/v1/assets", json={"name": "Retry Test Asset", "asset_type": "server", "environment": "development"})
    asset_id = res_asset.get_json()["asset"]["id"]

    db_path = app.config["DATABASE_PATH"]
    repo = JobRepository(db_path)

    job = ScanJob(
        id="job_retry_test_01",
        job_type="tls_scan",
        asset_id=asset_id,
        operation="probe_tls",
        status="failed",
        retry_count=1,
        max_retries=2,
    )
    repo.create(job)

    retry_res1 = client.post(f"/api/v1/jobs/{job.id}/retry")
    assert retry_res1.status_code == 200
    assert retry_res1.get_json()["job"]["status"] == "queued"
    assert retry_res1.get_json()["job"]["retry_count"] == 2

    job_updated = repo.get_by_id(job.id)
    job_updated.status = "failed"
    repo.update(job_updated)

    retry_res2 = client.post(f"/api/v1/jobs/{job.id}/retry")
    assert retry_res2.status_code == 400
    assert "maximum retries" in retry_res2.get_json()["error"].lower()


def test_claim_next_job_atomic_transition(app):
    """Verify claim_next_job atomically transitions oldest pending job to 'running'."""
    db_path = app.config["DATABASE_PATH"]
    asset_repo = AssetRepository(db_path)
    job_repo = JobRepository(db_path)

    test_asset = asset_repo.create(Asset(id="ast_claim_01", name="Claim Asset", asset_type="server", environment="testing"))

    job1 = ScanJob(id="job_atomic_1", job_type="certificate_scan", asset_id=test_asset.id, operation="op1", status="queued")
    job2 = ScanJob(id="job_atomic_2", job_type="certificate_scan", asset_id=test_asset.id, operation="op2", status="queued")
    job_repo.create(job1)
    job_repo.create(job2)

    claimed = job_repo.claim_next_job()
    assert claimed is not None
    assert claimed.id == "job_atomic_1"
    assert claimed.status == "running"
    assert claimed.started_at is not None

    claimed2 = job_repo.claim_next_job()
    assert claimed2 is not None
    assert claimed2.id == "job_atomic_2"

    assert job_repo.claim_next_job() is None


def test_recover_stale_jobs_after_crash(app):
    """Verify stale running jobs from an unexpected shutdown are safely marked failed."""
    db_path = app.config["DATABASE_PATH"]
    asset_repo = AssetRepository(db_path)
    job_repo = JobRepository(db_path)

    test_asset = asset_repo.create(Asset(id="ast_recover_01", name="Crash Asset", asset_type="server", environment="production"))

    stale_job = ScanJob(
        id="job_stale_crash_01",
        job_type="full_orchestrated_scan",
        asset_id=test_asset.id,
        operation="full_scan",
        status="running",
    )
    job_repo.create(stale_job)

    recovered_count = job_repo.recover_stale_jobs()
    assert recovered_count == 1

    recovered_job = job_repo.get_by_id("job_stale_crash_01")
    assert recovered_job.status == "failed"
    assert "unexpected worker or server restart" in recovered_job.error_message


def test_background_worker_execution(app):
    """Verify BackgroundJobManager executes queued jobs asynchronously."""
    db_path = app.config["DATABASE_PATH"]
    asset_repo = AssetRepository(db_path)
    job_repo = JobRepository(db_path)
    test_asset = asset_repo.create(Asset(id="ast_worker_01", name="Worker Asset", asset_type="website", environment="production"))

    manager = BackgroundJobManager(db_path, max_workers=2)

    execution_flag = {"executed": False}

    def custom_handler(job: ScanJob):
        execution_flag["executed"] = True
        return {"scanned_keys": 4, "quantum_vulnerable": True}

    manager.register_handler("certificate_scan", custom_handler)
    manager.start()

    try:
        job = ScanJob(
            id="job_async_exec_01",
            job_type="certificate_scan",
            asset_id=test_asset.id,
            operation="inspect_certs",
            status="queued",
        )
        manager.enqueue(job)

        # Wait briefly for worker thread to process
        time.sleep(0.5)

        finished_job = job_repo.get_by_id("job_async_exec_01")
        assert finished_job.status == "completed"
        assert finished_job.progress == 100
        assert finished_job.completed_at is not None
        assert execution_flag["executed"] is True
        assert finished_job.result_data["scanned_keys"] == 4
    finally:
        manager.stop()
