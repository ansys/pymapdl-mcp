
docker run \
    --name mapdl \
    --restart always \
    -e ANSYSLMD_LICENSE_FILE=1055@${LICENSE_SERVER} \
    -e ANSYS_LOCK="OFF" \
    -e VERSION=252 \
    -e P_SCHEMA=/ansys_inc/v252/ansys/ac4/schema \
    -e ANS_BYPASS_CHECK_NUM_PROCESSES=1 \
    -e OMPI_ALLOW_RUN_AS_ROOT=1 \
    -e OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1 \
    -p ${PYMAPDL_PORT}:50052 \
    --shm-size=2gb \
    -e I_MPI_SHM_LMT=shm \
    -w /jobs \
    -u=0:0 \
    --memory=6656MB \
    --memory-swap=16896MB \
    --mount type=bind,source="$(pwd)/entrypoint.sh",target=/entrypoint.sh,readonly \
    ${MAPDL_IMAGE} \
    /bin/bash /entrypoint.sh
