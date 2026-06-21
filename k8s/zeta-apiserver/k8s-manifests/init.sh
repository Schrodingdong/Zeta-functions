#!/bin/bash

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
export APP_RUNNER_BASE_IMAGE="registry.zeta.svc.cluster.local:5000/zeta-base-runner-python:0.0.1"
export APP_NAMESPACE="zeta"

envsubst < ./apiserver-cm.yaml | kubectl apply -f -
kubectl apply -f ./apiserver-deploy.yaml
kubectl apply -f ./apiserver-svc.yaml
