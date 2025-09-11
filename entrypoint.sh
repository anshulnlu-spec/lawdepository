#!/bin/bash
# entrypoint.sh - ensures $PORT expands correctly and starts uvicorn
set -euo pipefail

PORT="${PORT:-8080}"
HOST="${HOST:-0.0.0.0}"

# Optional: run lightweight startup checks here (db availability, migrations, etc.)
# e.g. python -m alembic upgrade head || true

exec uvicorn main:app --host "${HOST}" --port "${PORT}"
