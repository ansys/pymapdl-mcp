#!/bin/bash
echo "Starting MAPDL container with verbose logging..."
docker run --name mapdl -d \
    -p ${PYMAPDL_PORT}:50052 \
    --entrypoint /bin/bash \
    --env ANSYSLMD_LICENSE_FILE=1055@${LICENSE_SERVER} \
    --env ANSYS_LOCK='OFF' \
    --env ANS_BYPASS_CHECK_NUM_PROCESSES=1 \
    --env ANSYS_MAPDL_GRPC_TRANSPORT=insecure \
    --shm-size=2gb \
    ${MAPDL_IMAGE} \
    ansys -grpc -smp -np 2 > mapdl_launch.log 2>&1

echo "Container started. Container ID:"
docker ps -a --filter "name=mapdl" --format "{{.ID}} {{.Status}} {{.Command}}"

echo "Capturing initial container logs..."
docker logs mapdl > mapdl_initial.log 2>&1 || true
cat mapdl_initial.log
