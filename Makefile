.PHONY: help install synth deploy local-test

# Couleurs pour le terminal
BLUE := \033[36m
RESET := \033[0m

help: ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(BLUE)%-20s$(RESET) %s\n", $$1, $$2}'

install: ## Installe les dépendances (Python & CDK)
	cd iac && [ -d .venv ] || python3 -m venv .venv
	cd iac && . .venv/bin/activate && pip install -r requirements.txt
	cd iac && npm install --legacy-peer-deps

synth: ## Build les images Docker localement et génère les templates CloudFormation
	cd iac && npx aws-cdk synth

deploy: ## Déploie l'infrastructure complète sur AWS (Build local + Push)
	./deploy-prod.sh

local-test: ## Vérifie que Docker est prêt pour le build
	@docker info > /dev/null 2>&1 && echo "✅ Docker est opérationnel" || echo "❌ Docker n'est pas démarré"

