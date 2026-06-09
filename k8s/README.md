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
  - This will also port forward the k8s services
  - You will have the credentials for each service, to populate the .env
    ````terminaloutput
    <ouput-truncated>
    
    === Exported Variables ===
    DB_NAME:         ...
    DB_USERNAME:     ...
    DB_PASSWORD:     ...
    MINIO_USERNAME:  ...
    MINIO_PASSWORD:  ...
    RABBIT_USERNAME: ...
    RABBIT_PASSWORD: ...
    
    <ouput-truncated>
    ````
- Create a `.env` file in the k8s root folder
  ```shell
  # zeta-functions/k8s/.env

  # Database Configuration
  SPRING_DATASOURCE_URL=jdbc:postgresql://localhost:5432/<DB_NAME>
  SPRING_DATASOURCE_USERNAME=<DB_NAME>
  SPRING_DATASOURCE_PASSWORD=<DB_USERNAME>

  # RabbitMQ Configuration
  SPRING_RABBITMQ_HOST=localhost
  SPRING_RABBITMQ_PORT=5672
  SPRING_RABBITMQ_USERNAME=<RABBIT_USERNAME>
  SPRING_RABBITMQ_PASSWORD=<RABBIT_PASSWORD>
  SPRING_RABBITMQ_QUEUES_DEPLOYMENT=zeta.deployments
  SPRING_RABBITMQ_QUEUES_DELETE=zeta.delete

  # Object Storage (MinIO)
  APP_OBJECT_STORAGE_SERVICEURL=http://localhost:9000
  APP_OBJECT_STORAGE_USERNAME=<MINIO_USERNAME>
  APP_OBJECT_STORAGE_PASSWORD=<MINIO_PASSWORD>
  APP_OBJECT_STORAGE_BUCKET=zeta

  # Registry Configuration
  APP_REGISTRY_SERVICEURL=http://localhost:5000

  # Runner Configuration TODO needs to be displayed with the ./dev-k8s.sh output
  APP_RUNNER_BASE_IMAGE=localhost:5000/zeta-base-runner-python:0.0.1
  
  # Shared config
  APP_NAMESPACE=zeta
  ```
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