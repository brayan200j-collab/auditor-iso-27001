#!/bin/sh
# Keeps the mounted virtualenv in sync with uv.lock before running any command.
set -e
if [ -f uv.lock ]; then
  uv sync --frozen --quiet
else
  uv sync --quiet
fi
exec "$@"
