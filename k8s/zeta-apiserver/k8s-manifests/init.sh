#!/bin/bash
envsubst < ./apiserver-cm.yaml | kubectl apply -f -
kubectl apply -f ./apiserver-deploy.yaml
kubectl apply -f ./apiserver-svc.yaml
