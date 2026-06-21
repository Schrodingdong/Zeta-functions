#!/bin/bash
envsubst < ./image-engine-cm.yaml | kubectl create -f -
kubectl apply -f ./image-engine-deploy.yaml
kubectl apply -f ./image-engine-svc.yaml
