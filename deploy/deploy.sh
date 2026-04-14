#!/bin/bash
# Déploiement en production

set -e  # Stop si erreur

echo "📦 Déploiement du chatbot"

# Pull les dernières modifications
git pull origin main 2>/dev/null || echo "Pas de git, continue..."

# Nettoyage complet avant déploiement
./scripts/cleanup.sh

# Reconstruire ce qui est nécessaire
if command -v docker &> /dev/null; then
    docker-compose -f config/docker-compose.yml build
    docker-compose -f config/docker-compose.yml up -d
else
    echo "Docker non trouvé, déploiement local"
    python src/core/startup.py &
fi

echo "✅ Déploiement terminé"
