# Zeta functions - K8S
This is a rewrite of the original Zeta Functions project, utilizing the full capabilities of K8S.

## Glossary
- **Zeta / Zeta function** - The FaaS entity
- **Zeta Deployment** - Refers to having:
  - Metadata stored
  - The user's ZIP stored
  - The underlying k8s infra deployed
- **Zeta Deployment Resource** - A K8S resource
- **Zeta Deployment Resource Name (DRN)** - Name of the Zeta Deployment resources 

## Quickstart
- make sure to have HPA added to the cluster
````shell
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
````
- Run `install.sh`
- Port forward the api server 
````shell
kubectl port-forward -n zeta svc/zeta-apiserver 8080:80
````

## User code example
### Python
```python
### fibo.py
def fibo(n):
    memo = [0, 1]
    for i in range(2, n+1):
        memo.append(memo[i-1] + memo[i-2])
    return memo[-1]


### zeta.py
from .fibo import fibo
import json

def zetaHandler(event, context):
    n = event["body"]["n"]
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            "fib": fibo(n)
        })
    }
```