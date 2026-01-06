# Novialoom Infrastructure AWS

Ce dépôt contient toute l'Infrastructure as Code (IaC) et les spécifications nécessaires au déploiement de Novialoom sur AWS (eu-west-3).

## 📂 Structure du Dépôt

*   **`iac/`** : Projet **AWS CDK** en Python définissant les Stacks (Network, Storage, Compute).
*   **`specs/`** : Documents de conception détaillés pour la migration AWS.
*   **`templates/`** : Templates Docker optimisés pour AWS Lambda.
*   **`swagger/`** : Définition OpenAPI centralisée pour l'API Gateway.
*   **`deploy.yml`** : Workflow GitHub Actions pour le déploiement automatique.

## 🚀 Déploiement

### Prérequis
*   AWS CLI configuré.
*   Node.js & npm (pour CDK).
*   Python 3.12+.

### Installation
1.  `cd iac`
2.  `pip install -r requirements.txt`
3.  `cdk synth`
4.  `cdk deploy --all`

## 🛠️ Stacks CDK

1.  **NetworkStack** : VPC, Sous-réseaux, NAT Gateway.
2.  **StorageStack** : S3 Buckets, RDS PostgreSQL (t4g.micro), SQS Queues.
3.  **ComputeStack** : Lambdas Docker et API Gateway centralisée.

---
*Dernière mise à jour : Janvier 2026*

