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
echo "> deploying zeta-image-engine"
docker build -t schrodi/zeta-image-engine:latest "$PWD/zeta-image-engine"
(
    cd "$PWD/zeta-image-engine/k8s-manifests" || exit 1
    ./init.sh
)

echo
echo "> Exported Variables"
export DB_NAME="$(kubectl get secret -n zeta db-app -o jsonpath='{.data.dbname}' | base64 --decode)"
export DB_USERNAME="$(kubectl get secret -n zeta db-app -o jsonpath='{.data.username}' | base64 --decode)"
export DB_PASSWORD="$(kubectl get secret -n zeta db-app -o jsonpath='{.data.password}' | base64 --decode)"
export MINIO_USERNAME="$(kubectl get secret -n zeta minio -o jsonpath='{.data.rootUser}' | base64 --decode)"
export MINIO_PASSWORD="$(kubectl get secret -n zeta minio -o jsonpath='{.data.rootPassword}' | base64 --decode)"
export RABBIT_USERNAME="$(kubectl get secret -n zeta rabbit-cluster-default-user -o jsonpath='{.data.username}' | base64 --decode)"
export RABBIT_PASSWORD="$(kubectl get secret -n zeta rabbit-cluster-default-user -o jsonpath='{.data.password}' | base64 --decode)"
export REGISTRY_CLUSTERIP="$(kubectl get svc -n zeta registry -o jsonpath="{.spec.clusterIP}")"
echo "DB_NAME:            $DB_NAME"
echo "DB_USERNAME:        $DB_USERNAME"
echo "DB_PASSWORD:        $DB_PASSWORD"
echo "MINIO_USERNAME:     $MINIO_USERNAME"
echo "MINIO_PASSWORD:     $MINIO_PASSWORD"
echo "RABBIT_USERNAME:    $RABBIT_USERNAME"
echo "RABBIT_PASSWORD:    $RABBIT_PASSWORD"
echo "REGISTRY_CLUSTERIP: $REGISTRY_CLUSTERIP"

echo
echo "> Generating .env file"
envsubst < ./env.template > .env

echo
echo "> Port forward the services by running: ./port-forwarding.sh"