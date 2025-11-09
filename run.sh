#!/usr/bin/env bash
# Small helper to run the server.
# Usage:
#   PORT=5000 ./run.sh
PORT=${CHAT_PORT:-4000}
echo "Starting server on port $PORT..."
CHAT_PORT=$PORT python3 server.py --port $PORT
