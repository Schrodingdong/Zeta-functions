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
echo "> creating namespace"
kubectl create -f ./manifests/namespace.yaml

echo "> creating SA, Role and RoleBinding"
kubectl create -f ./manifests/zeta-sa.yaml
kubectl create -f ./manifests/zeta-role.yaml
kubectl create -f ./manifests/zeta-rb.yaml

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
export SPRING_DATASOURCE_URL="jdbc:postgresql://db-rw.zeta.svc.cluster.local:5432/zeta"
export SPRING_DATASOURCE_USERNAME="$(kubectl get secret -n zeta db-app -o jsonpath='{.data.username}' | base64 --decode)"
export SPRING_DATASOURCE_PASSWORD="$(kubectl get secret -n zeta db-app -o jsonpath='{.data.password}' | base64 --decode)"

export SPRING_RABBITMQ_HOST="rabbit-cluster.zeta.svc.cluster.local"
export SPRING_RABBITMQ_PORT="5672"
export SPRING_RABBITMQ_USERNAME="$(kubectl get secret -n zeta rabbit-cluster-default-user -o jsonpath='{.data.username}' | base64 --decode)"
export SPRING_RABBITMQ_PASSWORD="$(kubectl get secret -n zeta rabbit-cluster-default-user -o jsonpath='{.data.password}' | base64 --decode)"
export SPRING_RABBITMQ_QUEUES_DEPLOYMENT="zeta.deployments"
export SPRING_RABBITMQ_QUEUES_DELETE="zeta.delete"

export APP_OBJECT_STORAGE_SERVICEURL="http://minio.zeta.svc.cluster.local:9000"
export APP_OBJECT_STORAGE_USERNAME="$(kubectl get secret -n zeta minio -o jsonpath='{.data.rootUser}' | base64 --decode)"
export APP_OBJECT_STORAGE_PASSWORD="$(kubectl get secret -n zeta minio -o jsonpath='{.data.rootPassword}' | base64 --decode)"
export APP_OBJECT_STORAGE_BUCKET="zeta"

export APP_RUNNER_VERSION="0.0.1"
export APP_RUNNER_BASE_IMAGE="registry.zeta.svc.cluster.local:5000/zeta-base-runner-python:0.0.1"
export APP_NAMESPACE="zeta"
export APP_IMAGE_ENGINE_URL="http://zeta-image-engine.zeta.svc.cluster.local:6969"

export APP_REGISTRY_CLUSTERIP="$(kubectl get svc -n zeta registry -o jsonpath="{.spec.clusterIP}")"
export APP_REGISTRY_PORT=5000

export REGISTRY_URL="registry.zeta.svc.cluster.local:5000"
export IMAGE_VERSION="0.0.1"

echo
echo "> deploying zeta-image-engine"
docker build -t schrodi/zeta-image-engine:latest "$PWD/zeta-image-engine"
(
    cd "$PWD/zeta-image-engine/k8s-manifests" || exit 1
    ./init.sh
)

echo
echo "> deploying zeta-apiserver"
docker build -t schrodi/zeta-apiserver:0.0.1 "$PWD/zeta-apiserver"
(
    cd "$PWD/zeta-apiserver/k8s-manifests" || exit 1
    ./init.sh
)

echo
echo "> deploying zeta-runner"
docker build -t schrodi/zeta-runner:0.0.1 "$PWD/zeta-runner"
(
    cd "$PWD/zeta-runner/k8s-manifests" || exit 1
    ./init.sh
)