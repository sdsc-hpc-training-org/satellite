#!/bin/bash
# Build image with podman/docker
# additional args are passed directl to podman/docker build.
# use --no-cache to force an os image upgrade.
cd $(dirname $0)
podman build -f ./Dockerfile --tag satellite:latest  "$@"


