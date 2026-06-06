#!/bin/bash

mkdir -p ssl

openssl genrsa -out ssl/ca.key 4096
openssl req -new -x509 -days 1826 -key ssl/ca.key -out ssl/ca.crt -subj "/CN=zeta-registry-ca"

openssl genrsa -out ssl/registry.key 4096
openssl req -new -key ssl/registry.key -out ssl/registry.csr -subj "/CN=registry.zeta.svc.cluster.local"

cat > ssl/registry-ext.cnf << EOF
[SAN]
subjectAltName=DNS:registry.zeta.svc.cluster.local,DNS:localhost,IP:127.0.0.1
EOF

openssl x509 -req -days 365 -in ssl/registry.csr \
  -CA ssl/ca.crt -CAkey ssl/ca.key -CAcreateserial \
  -out ssl/registry.crt -extfile ssl/registry-ext.cnf -extensions SAN

# init registry
export CA_CRT=$(base64 -w 0 ssl/ca.crt)
export TLS_CRT=$(base64 -w 0 ssl/registry.crt)
export TLS_KEY=$(base64 -w 0 ssl/registry.key)
envsubst < registry-ca-secret.yaml | kubectl apply -f -
envsubst < registry-tls-secret.yaml | kubectl apply -f -
kubectl apply -f registry-pvc.yaml
kubectl apply -f registry-deploy.yaml
kubectl apply -f registry-svc.yaml
kubectl apply -f registry-init-job.yaml
