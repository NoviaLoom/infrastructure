# Guide de Migration Code : Adaptation vers AWS native

## 1. Stockage : Passage à AWS S3 (`boto3`)

Actuellement, le projet utilise un mix de stockage local et Scaleway S3. La migration vers AWS S3 doit se faire via la bibliothèque officielle `boto3`.

### 🛠️ Installation
```bash
pip install boto3
```

### 📝 Exemple d'adaptation (Service Storage)
Remplacez les clients S3 génériques par un client `boto3` configuré pour AWS.

```python
import boto3
import os

class S3StorageService:
    def __init__(self):
        self.s3 = boto3.client('s3')
        self.bucket_name = os.getenv('AWS_S3_BUCKET_NAME')

    def upload_report(self, file_path, object_name):
        self.s3.upload_file(file_path, self.bucket_name, object_name)
        
    def get_presigned_url(self, object_name, expiration=3600):
        return self.s3.generate_presigned_url('get_object',
                                              Params={'Bucket': self.bucket_name,
                                                      'Key': object_name},
                                              ExpiresIn=expiration)
```

## 2. Variables d'Environnement AWS

Lors de l'exécution sur Lambda ou ECS, les credentials AWS sont automatiquement gérés par l'IAM Role associé. **Ne stockez jamais de clés statiques (`AWS_ACCESS_KEY_ID`) dans le code ou les variables d'env.**

Variables à ajouter dans le `.env` de production :
*   `AWS_REGION=eu-west-3`
*   `AWS_S3_BUCKET_NAME=novialoom-reports-prod`
*   `DATABASE_URL=postgresql+asyncpg://user:pass@rds-endpoint:5432/novialoom`

## 3. Base de Données (RDS)

L'utilisation de `SQLAlchemy` avec `asyncpg` reste identique. Il suffira de mettre à jour l'URL de connexion vers l'endpoint RDS fourni par la stack Terraform/CDK.

## 4. Messaging (SQS vs RabbitMQ)

Pour les services utilisant Celery, il faut changer le broker URL pour pointer vers SQS.

```python
# Dans Celery config
broker_url = 'sqs://'
broker_transport_options = {
    'region': 'eu-west-3',
    'predefined_queues': {
        'llm-generation': {
            'url': 'https://sqs.eu-west-3.amazonaws.com/123456789012/llm-generation'
        }
    }
}
```

## 5. Logging Centralisé

AWS CloudWatch est utilisé par défaut. Assurez-vous que vos logs utilisent la bibliothèque standard `logging` de Python sans formattage complexe de fichiers locaux.

