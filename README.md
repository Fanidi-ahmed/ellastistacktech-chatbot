# 🤖 IntellistackTech Chatbot

Assistant virtuel intelligent pour IntellistackTech, spécialisé en DevOps, Intelligence Artificielle et Cloud AWS.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](https://www.docker.com/)

## 🚀 **Installation rapide**

### **Prérequis**
- Python 3.11
- Docker (optionnel)
- 4GB RAM minimum

### **Installation locale**


# Créer l'environnement virtuel
python3.11 -m venv .venv
source .venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'API
uvicorn src.api.rest_api:app --reload --host 0.0.0.0 --port 8001

# Dans un autre terminal, lancer l'interface web
cd interfaces/web
python3 -m http.server 8082
Accès
Interface web : http://localhost:8082

API : http://localhost:8001

Documentation API : http://localhost:8001/docs

🐳 Déploiement Docker
bash
# Construction de l'image
docker build -t intellistack-chatbot .

# Lancement
docker run -d -p 8001:8001 --name chatbot intellistack-chatbot

# Avec docker-compose
docker-compose up -d

📁 Structure du projet
text
mon_chatbot/
├── src/                    # Code source
│   ├── api/                # API REST (FastAPI)
│   ├── core/               # Configuration et utilitaires
│   ├── dialogue/           # Gestion des conversations
│   ├── knowledge/          # Base de connaissances vectorielle
│   └── nlp/                # Traitement du langage
├── interfaces/             # Points d'entrée
│   └── web/                # Interface web
│       ├── css/            # Styles
│       ├── js/             # JavaScript
│       └── images/         # Logos et assets
├── data/                   # Données
│   ├── conversations/      # Historique
│   ├── knowledge_base/     # Documents
│   └── intents.json        # Intentions
├── models/                 # Modèles sauvegardés
├── scripts/                # Scripts utilitaires
├── tests/                  # Tests unitaires
├── deploy/                 # Scripts de déploiement
├── config/                 # Fichiers de configuration
├── requirements.txt        # Dépendances
├── Dockerfile              # Image Docker
├── docker-compose.yml      # Orchestration
└── README.md               # Documentation













