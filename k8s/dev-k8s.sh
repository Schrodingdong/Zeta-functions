#!/bin/bash

wait_for_components() {
  echo
  echo "waiting for components..."
  rabbit_status=$(kubectl get -n zeta pods rabbit-cluster-server-0 -o jsonpath="{.status.phase}")
  db_status=$(kubectl get -n zeta pods db-1 -o jsonpath="{.status.phase}")
  minio_status=$(kubectl get -n zeta pods -l app=minio -o jsonpath="{.items[0].status.phase}")
  registry_status=$(kubectl get -n zeta pods -l app=registry -o jsonpath="{.items[0].status.phase}")
  [ "$rabbit_status" = "Running" ]  && \
    [ "$db_status" = "Running" ]    && \
    [ "$minio_status" = "Running" ] && \
    [ "$registry_status" = "Running" ]
}

echo "Initializing k8s dev env..."

# Init NS
kubectl create -f ./manifests/namespace.yaml

# Deploy dependent services
PWD=$(pwd)
for component in db minio rabbit registry; do
    echo
    echo "> deploying $component"
    (
        cd "$PWD/manifests/$component" || exit 1
        ./init.sh
    )
done
until wait_for_components
do
  sleep 5
done

# Deploying zeta services
echo
echo "=== deploying zeta-image-engine ==="
docker build -t schrodi/zeta-image-engine:latest "$PWD/zeta-image-engine"
kubectl create -f "$PWD/zeta-image-engine"
for service in "zeta-image-engine"; do
    echo
    echo "> deploying $service"
    (
        cd "$PWD/zeta-$service/k8s-manifests" || exit 1
        ./init.sh
    )
done

echo
echo "=== Exported Variables ==="
echo "DB_NAME:         $(kubectl get secret -n zeta db-app -o jsonpath="{.data.dbname}" | base64 --decode)"
echo "DB_USERNAME:     $(kubectl get secret -n zeta db-app -o jsonpath="{.data.username}" | base64 --decode)"
echo "DB_PASSWORD:     $(kubectl get secret -n zeta db-app -o jsonpath="{.data.password}" | base64 --decode)"
echo "MINIO_USERNAME:  $(kubectl get secret -n zeta minio -o jsonpath="{.data.rootUser}" | base64 --decode)"
echo "MINIO_PASSWORD:  $(kubectl get secret -n zeta minio -o jsonpath="{.data.rootPassword}" | base64 --decode)"
echo "RABBIT_USERNAME: $(kubectl get secret -n zeta rabbit-cluster-default-user -o jsonpath="{.data.username}" | base64 --decode)"
echo "RABBIT_PASSWORD: $(kubectl get secret -n zeta rabbit-cluster-default-user -o jsonpath="{.data.password}" | base64 --decode)"


# Port forward
echo
echo "> forwarding svc/db-rw"
kubectl port-forward -n zeta svc/db-rw 5432:5432 &
echo "> forwarding svc/rabbit-cluster"
kubectl port-forward -n zeta svc/rabbit-cluster 5672:5672 &
echo "> forwarding svc/registry"
kubectl port-forward -n zeta svc/registry 5000:5000 &
echo "> forwarding svc/minio"
kubectl port-forward -n zeta svc/minio 9000:9000 &
