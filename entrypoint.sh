#!/bin/bash
set -e

# Install dependencies if requirements.txt is present
if [ -f "requirements.txt" ]; then
    python3 -m pip install --no-cache-dir -r requirements.txt
fi

# Execute the command passed to the container
exec "$@"

