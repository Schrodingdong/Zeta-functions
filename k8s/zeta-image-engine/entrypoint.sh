#!/bin/sh
set -e

echo "====== Updating SSL certs ======"
update-ca-certificates

echo "====== Starting dockerd ======"
dockerd-entrypoint.sh &
echo "Waiting for Docker daemon..."
until docker info >/dev/null 2>&1; do
    sleep 1
done
echo "Docker daemon is ready"

echo "====== Run app ======"
/image-engine