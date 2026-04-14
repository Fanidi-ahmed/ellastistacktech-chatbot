#!/bin/bash
# Exécuté automatiquement au démarrage

echo "🚀 Démarrage du chatbot..."

# Nettoyage léger (garde tout l'essentiel)
./scripts/cleanup.sh

# Vérification des dossiers essentiels
mkdir -p data/conversations logs models/vector_store

echo "✅ Prêt à démarrer"
