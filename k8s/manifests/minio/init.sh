#!/bin/bash
helm repo add minio https://charts.min.io/
helm repo update

helm install minio minio/minio \
  -f minio-values.yaml \
  -n zeta