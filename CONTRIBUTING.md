# Contributing to QuantumShield

Thank you for contributing to QuantumShield.

## Development Workflow

1. **Incremental Milestones**: We develop in incremental stages (Stage 1 through Stage 12).
2. **Git Commit Conventions**: Follow Conventional Commits:
   - `chore: initialize QuantumShield web application`
   - `feat: implement database and asset inventory`
   - `test: add unit and integration test coverage`
3. **Automated Testing**: All backend pytest tests must pass before opening PRs:
   ```bash
   python -m pytest backend/tests/ -v
   ```
4. **Code Quality**: Ensure TypeScript compiles cleanly without errors:
   ```bash
   cd frontend
   npm run build
   ```
