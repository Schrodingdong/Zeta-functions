#!/bin/bash

# Install CloudNativePG
kubectl apply \
  --server-side \
  -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.29/releases/cnpg-1.29.1.yaml

kubectl rollout status deployment \
  -n cnpg-system cnpg-controller-manager

kubectl create -f db-cluster.yaml