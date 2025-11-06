#!/bin/bash

echo "Waiting for MAPDL to start..."
for i in {1..5}; do
    # Capture logs continuously for debugging
    docker logs mapdl > "mapdl_logs_attempt_${i}.log" 2>&1 || true

    # Check container status
    CONTAINER_STATUS=$(docker inspect -f '{{.State.Status}}' mapdl 2>/dev/null || echo "not found")
    echo "Attempt $i/5: Container status: $CONTAINER_STATUS"

    if [ "$CONTAINER_STATUS" = "exited" ]; then
        echo "ERROR: Container has exited!"
        docker logs mapdl 2>&1
        exit 1
    fi

    # Check for ready message in logs
    if docker logs mapdl 2>&1 | grep -q "Server listening on"; then
        echo "MAPDL is ready!"
        echo "=== Final MAPDL logs ==="
        docker logs mapdl 2>&1
        exit 0
    fi

    # Show last 20 lines of logs for debugging
    echo "Latest logs:"
    docker logs --tail 20 mapdl 2>&1 || echo "No logs yet"

    sleep 2
done

echo "MAPDL failed to start within 120 seconds"
echo "=== Container status ==="
docker ps -a
echo "=== Full container logs ==="
docker logs mapdl 2>&1
echo "=== Container inspection ==="
docker inspect mapdl
exit 1
