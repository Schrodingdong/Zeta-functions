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

## Dev Quickstart
### K8S infra
- Run `./dev-k8s.sh` to initialize the k8s infra
  - This will generate a .env following env.template
- Port forward the service by running `./port-forwarding.sh`
- Start the `zeta-runner` and the `zeta-apiserver`
- The user would have to write his Zeta as follows:
  - The entrypoint would be in a `zeta.<ext>` file, defined in `zetaHandler` function
  - Create a zip containing the created files
- Deploy a zeta by hitting the `localhost:8080/zetas` endpoint
  ```sh
  curl --location 'localhost:8080/zetas' \
    --form 'file=@"<path-to-zip>"' \
    --form 'name="<zetaName>"'
  ```


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