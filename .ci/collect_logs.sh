#!/bin/bash

echo "=== Initial launch log ==="
cat mapdl_launch.log 2>/dev/null || echo "No launch log found"

echo "=== Initial container log ==="
cat mapdl_initial.log 2>/dev/null || echo "No initial log found"

echo "=== All captured log files ==="
ls -la mapdl_*.log 2>/dev/null || echo "No log files found"

echo "=== Full MAPDL Container Logs (stdout + stderr) ==="
docker logs mapdl 2>&1 || echo "Could not retrieve container logs"

echo "=== Docker Container Status ==="
docker ps -a --filter "name=mapdl"

echo "=== Docker Container Inspection ==="
docker inspect mapdl 2>&1 || echo "Could not inspect container"

echo "=== Docker Container Stats (if running) ==="
docker stats mapdl --no-stream 2>&1 || echo "Container not running"
