#!/bin/sh

echo
echo "> forwarding svc/db-rw"
kubectl port-forward -n zeta svc/db-rw 5432:5432 &
echo "> forwarding svc/rabbit-cluster"
kubectl port-forward -n zeta svc/rabbit-cluster 5672:5672 &
echo "> forwarding svc/registry"
kubectl port-forward -n zeta svc/registry 5000:5000 &
echo "> forwarding svc/minio"
kubectl port-forward -n zeta svc/minio 9000:9000 &

echo "> forwarding svc/image-engine	"
kubectl port-forward -n zeta svc/image-engine	6969:6969 &
