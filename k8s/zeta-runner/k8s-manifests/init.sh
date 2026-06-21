#!/bin/bash
envsubst < ./runner-cm.yaml | kubectl apply -f -
kubectl apply -f ./runner-deploy.yaml
kubectl apply -f ./runner-svc.yaml