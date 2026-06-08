#!/bin/bash

# Instal CloudNativePG
kubectl apply \
  --server-side \
  -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.29/releases/cnpg-1.29.1.yaml

kubectl rollout status deployment \
  -n cnpg-system cnpg-controller-manager

export DB_USERNAME=${DB_USERNAME:-zeta}
export DB_PASSWORD=${DB_PASSWORD:-zeta}
envsubst < db-secret.yaml | kubectl create -f -
kubectl create -f ./db-cluster.yaml