#!/bin/bash
set -e # Arrête le script en cas d'erreur

# 1. Aller dans le dossier CDK
cd iac

# 2. Vérifier que Docker tourne
if ! docker info > /dev/null 2>&1; then
  echo "❌ Docker n'est pas démarré. Merci de lancer Docker Desktop."
  exit 1
fi

# 3. Activation de l'environnement virtuel Python
if [ -d ".venv" ]; then
    echo "🐍 Activation de l'environnement virtuel..."
    source .venv/bin/activate
else
    echo "⚠️  Attention : .venv non trouvé. Le déploiement risque d'échouer."
fi

# 4. Déploiement atomique (Build local + Push + Lambda Update)
echo "🏗️  Construction des images et déploiement AWS..."
npx aws-cdk deploy --all --require-approval never

echo "🚀 Production mise à jour !"

