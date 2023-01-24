#!/bin/bash
cd $(dirname $0)

if [[ ! -f container-envs.conf ]]; then
  echo "Missing $(pwd)/container-envs.conf" 1>&2
  exit 1
fi
source container-envs.conf

PERSIST_BASE_DIR=/var/persistent/satthing-persistent
BIND_DIRS=( \
  "${PERSIST_BASE_DIR}/logs" \
  "${PERSIST_BASE_DIR}/secrets" \
  "${PERSIST_BASE_DIR}/secrets/satellite-state" )

for B in "${BIND_DIRS[@]}"; do
  if [[ ! -d "${B}" ]]; then
    umask 0033
    mkdir -p "${B}"
    printf "Created: %s\n" "${B}"
  fi
done

TLS_FILES=( \
  "${PERSIST_BASE_DIR}/secrets/http-server.pem" \
  "${PERSIST_BASE_DIR}/secrets/http-server.privkey" \
  "${PERSIST_BASE_DIR}/secrets/http-server.chain" )
TLS_OOPS=0
for T in "${TLS_FILES[@]}"; do
  if [[ ! -f "${T}" ]]; then
    echo "Missing file: ${T}" 1>&2
    TLS_OOPS=1
  fi
done
if [[ "${TLS_OOPS}" -ne 0 ]];  then
  echo "Missing critical files, no action taken." 1>&2
  exit 1
fi  
  
umask 0022

podman create \
  --user=0 \
  --cap-drop=all \
  --cap-add=CHOWN \
  --cap-add=KILL \
  --cap-add=NET_BIND_SERVICE \
  --cap-add=NET_ADMIN \
  --cap-add=SETGID \
  --cap-add=SETUID \
  --cap-add=SETPCAP \
  --cap-add=DAC_OVERRIDE \
  --cap-add=SYS_CHROOT \
  --read-only=false \
  --mount=type=bind,src=/dev/log,destination=/dev/log \
  --mount=type=tmpfs,tmpfs-size=100M,tmpfs-mode=0755,destination=/var/lib/satellite-revssh \
  --mount=type=tmpfs,tmpfs-size=100M,tmpfs-mode=0755,destination=/var/run \
  --mount=type=bind,src=${PERSIST_BASE_DIR}/logs,destination=/var/log \
  --mount=type=bind,src=${PERSIST_BASE_DIR}/secrets,destination=/var/secrets \
  --env SAT_CONFIG_TGTIPMASK \
  --env SAT_CONFIG_JOBSTATEIPMASK \
  --env SAT_CONFIG_TTL_SECS \
  --env SAT_CONFIG_EXTPORT \
  --env SAT_CONFIG_EXTBASENAME \
  --network ${NETWORK} \
  --ip ${IP} \
  --subuidname=ssakai \
  --subgidname=ssakai \
  --replace  \
  --shm-size=2g \
  --name=satthing \
  --hostname=satthing \
  --entrypoint '["/usr/bin/tini", "/entrypoint"]' \
  satellite:latest 


