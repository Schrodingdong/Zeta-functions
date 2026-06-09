#!/bin/bash

# TODO have it extracted from CMs of zeta runner service
export REGISTRY_URL="registry.zeta.svc.cluster.local:5000"
export IMAGE_VERSION="0.0.1"

envsubst < ./image-engine-cm.yaml | kubectl create -f -
kubectl apply -f ./image-engine-deploy.yaml
kubectl apply -f ./image-engine-svc.yaml
