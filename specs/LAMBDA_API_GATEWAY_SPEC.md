# Spécification : Création et Déploiement des Lambdas & API Gateway

Ce document définit les standards pour l'automatisation du cycle de vie des Lambdas Novialoom.

## 1. Naming & Repositories

### 1.1 Naming AWS (Ressources)
Format : `novialoom-{service}-{env}`
*   `service` : Le nom du microservice (ex: `analysis`, `order`).
*   `env` : `dev`, `staging`, ou `prod`.

*Exemple : `novialoom-analysis-prod`*

### 1.2 Repositories Docker (ECR)
Chaque microservice possède son propre dépôt ECR pour isoler les images.
*   URI : `{aws_account_id}.dkr.ecr.eu-west-3.amazonaws.com/novialoom-{service}`

## 2. Template Docker Lambda (Python 3.12)

Nous utilisons l'image de base officielle AWS Lambda. Le code source du service est monté dans `/var/task`.

### Template : `infrastructure/templates/Dockerfile.lambda`
```dockerfile
FROM public.ecr.aws/lambda/python:3.12

# 1. Installation des dépendances système si nécessaire
# RUN yum install -y gcc ...

# 2. Copie des requirements et installation
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copie du code source du microservice
COPY . ${LAMBDA_TASK_ROOT}

# 4. Handler par défaut pour FastAPI avec Mangum
CMD [ "main.handler" ]
```

## 3. Déploiement Automatique (CI/CD)

Le déploiement est piloté par GitHub Actions et AWS CDK.

### Workflow Logiciel :
1.  **Trigger** : Push sur `main` ou `develop`.
2.  **Build** : GitHub Runner construit l'image Docker du service modifié.
3.  **Push** : Authentification OIDC et push de l'image sur ECR avec le tag `sha-{commit}`.
4.  **Update** : `cdk deploy` met à jour la définition de la Lambda pour pointer vers la nouvelle image.

## 4. Liste Détaillée des Lambdas

| Nom Service | Dossier Source | Type de Charge | Mémoire (Mo) | Timeout |
| :--- | :--- | :--- | :--- | :--- |
| `core` | `core-service/` | CPU (LLM Wrapper) | 512 | 60s |
| `theme` | `theme-service/` | I/O (DB) | 256 | 30s |
| `captation` | `captation-service/` | I/O (APIs) | 512 | 120s |
| `analysis` | `analysis-service/` | CPU (JSON Build) | 1024 | 300s |
| `order` | `order-service/` | I/O (DB) | 256 | 30s |
| `client` | `client-mgmt-service/` | I/O (DB) | 256 | 30s |
| `gateway-b2b`| `b2b-gateway/` | Proxy / Auth | 256 | 30s |
| `gateway-b2c`| `b2c-gateway/` | Proxy / Auth | 256 | 30s |

## 5. API Gateway & Swagger

### 5.1 Structure de l'API Gateway
Une seule **REST API** centralisée (`Novialoom-Central-API`) pour réduire les coûts et simplifier le Swagger.

*   `ANY /b2b/{proxy+}` -> Intégration `gateway-b2b`
*   `ANY /b2c/{proxy+}` -> Intégration `gateway-b2c`

### 5.2 Swagger / OpenAPI
Le Swagger est généré dynamiquement par FastAPI. Cependant, l'API Gateway servira un portail de documentation unifié :
1.  Chaque Lambda Gateway expose son propre `/docs`.
2.  L'API Gateway centralise ces définitions via un `OpenAPI Definition Body` dans CDK ou via une ressource dédiée.

#### Accès Swagger Unifié (Portail) :
*   `GET /b2b/docs` : Documentation Interactive pour le module Entreprise.
*   `GET /b2c/docs` : Documentation Interactive pour le Strategic Planner.

#### Configuration OpenAPI (CDK Example) :
```python
# Dans ComputeStack
self.api = apigw.RestApi(
    self, "NovialoomCentralAPI",
    # ...
    inline_definition=apigw.ApiDefinition.from_asset("infrastructure/swagger/openapi.yaml")
)
```

## 6. Handler FastAPI (Standard)

Chaque service doit utiliser `Mangum` dans son `main.py` :

```python
from fastapi import FastAPI
from mangum import Mangum

app = FastAPI(title="Novialoom Analysis Service")

@app.get("/")
def read_root():
    return {"status": "ok"}

# Wrapper pour AWS Lambda
handler = Mangum(app)
```

