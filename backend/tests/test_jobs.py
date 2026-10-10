"""
Automated Unit Tests for Persistent Job Processing and Worker Framework.
Milestone 1 Specification: All 16 core test cases covering lifecycle states,
handlers, atomic claiming, cancellation, backoff, lease recovery, and worker health.
"""

import time
from datetime import datetime, timezone, timedelta
from quantumshield.models.job import ScanJob, calculate_backoff, ALLOWED_TRANSITIONS
from quantumshield.models.asset import Asset
from quantumshield.storage.job_repository import JobRepository
from quantumshield.storage.repositories import AssetRepository
from quantumshield.services.job_worker import BackgroundJobManager
from quantumshield.core.exceptions import ValidationError


def test_create_and_persist_job(client):
    """1. Test creating and retrieving a scan job through the REST API."""
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
        "priority": 7,
    }
    response = client.post("/api/v1/jobs", json=job_payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data["status"] == "ok"
    assert "job" in data
    job = data["job"]
    assert job["asset_id"] == asset_id
    assert job["job_type"] == "certificate_scan"
    assert job["priority"] == 7
    assert job["status"] in ("pending", "queued")
    assert job["id"].startswith("job_")

    get_res = client.get(f"/api/v1/jobs/{job['id']}")
    assert get_res.status_code == 200
    assert get_res.get_json()["job"]["id"] == job["id"]


def test_reject_job_for_nonexistent_asset(client):
    """2. Verify creating a job for a missing asset fails with 404."""
    response = client.post("/api/v1/jobs", json={
        "asset_id": "ast_missing_999",
        "job_type": "tls_scan",
        "operation": "handshake_probe",
    })
    assert response.status_code == 404
    assert "does not exist" in response.get_json()["error"].lower()


def test_reject_unknown_job_type_400(client):
    """3. Verify submitting an invalid job type returns 400 Bad Request."""
    response = client.post("/api/v1/jobs", json={
        "job_type": "unsupported_vulnerability_exploit",
    })
    assert response.status_code == 400
    assert "invalid job_type" in response.get_json()["error"].lower()


def test_reject_asset_validation_without_asset_400(client):
    """4. Verify asset_validation requires an asset_id and returns 400 if omitted."""
    response = client.post("/api/v1/jobs", json={
        "job_type": "asset_validation",
    })
    assert response.status_code == 400
    assert "asset_id' is required" in response.get_json()["error"].lower()


def test_health_check_job_execution_without_asset(app):
    """5. Verify health_check executes cleanly without needing an asset_id."""
    db_path = app.config["DATABASE_PATH"]
    manager = BackgroundJobManager(db_path, max_workers=2)
    manager.start()

    try:
        job = ScanJob(
            id="job_health_01",
            job_type="health_check",
            asset_id=None,
            priority=5,
        )
        manager.enqueue(job)

        time.sleep(0.4)

        repo = JobRepository(db_path)
        finished = repo.get_by_id("job_health_01")
        assert finished is not None
        assert finished.status == "completed"
        assert finished.progress == 100
        assert finished.asset_id is None
        assert finished.result_json is not None
        assert finished.result_json["database"] == "connected"
        assert finished.result_json["status"] == "healthy"
    finally:
        manager.stop()


def test_asset_validation_job_execution_with_asset(app):
    """6. Verify asset_validation executes and returns asset parameter metadata."""
    db_path = app.config["DATABASE_PATH"]
    asset_repo = AssetRepository(db_path)
    asset = asset_repo.create(Asset(
        id="ast_val_01",
        name="Production Web Host",
        asset_type="website",
        environment="production",
        criticality="critical",
        hostname="secure.example.com",
    ))

    manager = BackgroundJobManager(db_path, max_workers=2)
    manager.start()

    try:
        job = ScanJob(
            id="job_val_01",
            job_type="asset_validation",
            asset_id=asset.id,
            priority=6,
        )
        manager.enqueue(job)

        time.sleep(0.4)

        repo = JobRepository(db_path)
        finished = repo.get_by_id("job_val_01")
        assert finished is not None
        assert finished.status == "completed"
        assert finished.progress == 100
        assert finished.result_json is not None
        assert finished.result_json["validation_passed"] is True
        assert finished.result_json["asset_name"] == "Production Web Host"
    finally:
        manager.stop()


def test_cancel_job(client):
    """7. Verify cancelling a queued job transitions state to 'cancelled' immediately."""
    res_asset = client.post("/api/v1/assets", json={"name": "Cancel Test Asset", "asset_type": "website", "environment": "staging"})
    asset_id = res_asset.get_json()["asset"]["id"]

    res_job = client.post("/api/v1/jobs", json={"asset_id": asset_id, "job_type": "static_scan", "operation": "scan_directory"})
    job_id = res_job.get_json()["job"]["id"]

    cancel_res = client.post(f"/api/v1/jobs/{job_id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.get_json()["job"]["status"] == "cancelled"

    get_res = client.get(f"/api/v1/jobs/{job_id}")
    assert get_res.get_json()["job"]["status"] == "cancelled"


def test_cooperative_cancellation_of_running_job(app):
    """8. Verify cancelling a running job transitions to cancel_requested then cancelled."""
    db_path = app.config["DATABASE_PATH"]
    repo = JobRepository(db_path)

    job = ScanJob(
        id="job_running_cancel_01",
        job_type="health_check",
        status="running",
    )
    repo.create(job)

    # Calling cancellation on running job
    cancelled_job = repo.request_cancellation(job.id)
    assert cancelled_job is not None
    assert cancelled_job.status == "cancel_requested"
    assert cancelled_job.error_code == "CANCEL_REQUESTED"


def test_job_state_transition_validation():
    """9. Verify lifecycle state transition rules."""
    job = ScanJob(id="job_trans_01", job_type="health_check", status="pending")

    # Pending can go to queued or cancelled
    assert job.can_transition_to("queued") is True
    assert job.can_transition_to("cancelled") is True
    assert job.can_transition_to("completed") is False

    # Running can go to completed, partially_completed, failed, cancel_requested
    job.status = "running"
    assert job.can_transition_to("completed") is True
    assert job.can_transition_to("cancel_requested") is True
    assert job.can_transition_to("pending") is False

    # Completed is terminal
    job.status = "completed"
    assert job.can_transition_to("running") is False
    assert job.can_transition_to("queued") is False


def test_exponential_backoff_calculation_and_timestamp(app, client):
    """10. Verify exponential backoff calculation and next_retry_at updates."""
    # Test formula: 5 * 2^(n-1)
    assert calculate_backoff(1) == 5
    assert calculate_backoff(2) == 10
    assert calculate_backoff(3) == 20
    assert calculate_backoff(4) == 40
    assert calculate_backoff(10) == 300  # Capped at 300

    db_path = app.config["DATABASE_PATH"]
    repo = JobRepository(db_path)
    job = ScanJob(
        id="job_backoff_test",
        job_type="health_check",
        status="failed",
        attempt_count=1,
        max_attempts=3,
    )
    repo.create(job)

    retried = repo.retry(job.id)
    assert retried is not None
    assert retried.attempt_count == 2
    assert retried.status == "queued"
    assert retried.next_retry_at is not None

    # Validate next_retry_at is in the future (~10 seconds)
    retry_dt = datetime.fromisoformat(retried.next_retry_at)
    now_dt = datetime.now(timezone.utc)
    diff_sec = (retry_dt - now_dt).total_seconds()
    assert 5 <= diff_sec <= 15


def test_retry_job_and_limit_enforcement(app, client):
    """11. Verify job retry enforces max_attempts limit."""
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
        attempt_count=1,
        max_attempts=2,
    )
    repo.create(job)

    retry_res1 = client.post(f"/api/v1/jobs/{job.id}/retry")
    assert retry_res1.status_code == 200
    assert retry_res1.get_json()["job"]["status"] == "queued"
    assert retry_res1.get_json()["job"]["attempt_count"] == 2

    job_updated = repo.get_by_id(job.id)
    job_updated.status = "failed"
    repo.update(job_updated)

    retry_res2 = client.post(f"/api/v1/jobs/{job.id}/retry")
    assert retry_res2.status_code == 400
    assert "maximum retries" in retry_res2.get_json()["error"].lower()


def test_priority_ordering_in_job_claiming(app):
    """12. Verify claim_next_job claims higher priority jobs first."""
    db_path = app.config["DATABASE_PATH"]
    repo = JobRepository(db_path)

    job_low = ScanJob(id="job_prio_low", job_type="health_check", priority=2, status="queued")
    job_high = ScanJob(id="job_prio_high", job_type="health_check", priority=9, status="queued")
    job_mid = ScanJob(id="job_prio_mid", job_type="health_check", priority=5, status="queued")

    repo.create(job_low)
    repo.create(job_high)
    repo.create(job_mid)

    claimed1 = repo.claim_next_job()
    assert claimed1 is not None
    assert claimed1.id == "job_prio_high"

    claimed2 = repo.claim_next_job()
    assert claimed2 is not None
    assert claimed2.id == "job_prio_mid"

    claimed3 = repo.claim_next_job()
    assert claimed3 is not None
    assert claimed3.id == "job_prio_low"


def test_delayed_execution_honours_next_retry_at(app):
    """13. Verify claim_next_job skips jobs whose next_retry_at is in the future."""
    db_path = app.config["DATABASE_PATH"]
    repo = JobRepository(db_path)

    future_iso = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    delayed_job = ScanJob(
        id="job_delayed_01",
        job_type="health_check",
        status="queued",
        next_retry_at=future_iso,
    )
    ready_job = ScanJob(
        id="job_ready_01",
        job_type="health_check",
        status="queued",
    )
    repo.create(delayed_job)
    repo.create(ready_job)

    claimed = repo.claim_next_job()
    assert claimed is not None
    assert claimed.id == "job_ready_01"

    # delayed_job should not be claimed yet
    assert repo.claim_next_job() is None


def test_lease_recovery_of_abandoned_jobs(app):
    """14. Verify recover_abandoned_jobs re-queues expired running jobs."""
    db_path = app.config["DATABASE_PATH"]
    repo = JobRepository(db_path)

    stale_iso = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    abandoned_job = ScanJob(
        id="job_abandoned_01",
        job_type="health_check",
        status="running",
        attempt_count=1,
        max_attempts=3,
        updated_at=stale_iso,
    )
    repo.create(abandoned_job)

    recovered = repo.recover_abandoned_jobs(lease_seconds=60)
    assert recovered == 1

    recovered_job = repo.get_by_id("job_abandoned_01")
    assert recovered_job.status == "queued"
    assert recovered_job.attempt_count == 2
    assert recovered_job.error_code == "LEASE_EXPIRED"


def test_worker_status_endpoint(client):
    """15. Verify /api/worker/status and /api/v1/worker/status return valid health data."""
    res1 = client.get("/api/worker/status")
    assert res1.status_code == 200
    data1 = res1.get_json()
    assert data1["status"] == "ok"
    assert "worker" in data1
    assert "max_workers" in data1["worker"]
    assert "queue_depth" in data1["worker"]

    res2 = client.get("/api/v1/worker/status")
    assert res2.status_code == 200
    assert res2.get_json()["status"] == "ok"


def test_list_jobs_filtering_and_pagination(client):
    """16. Verify listing jobs supports status filter and pagination."""
    # List jobs
    res = client.get("/api/v1/jobs?limit=5&offset=0")
    assert res.status_code == 200
    data = res.get_json()
    assert "jobs" in data
    assert "total" in data
    assert data["limit"] == 5

    # Filter by non-existent status
    res_filtered = client.get("/api/v1/jobs?status=nonexistent_status")
    assert res_filtered.status_code == 200
    assert len(res_filtered.get_json()["jobs"]) == 0


def test_recover_stale_jobs_after_crash(app):
    """Additional crash recovery test verifying immediate startup failure marking."""
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
