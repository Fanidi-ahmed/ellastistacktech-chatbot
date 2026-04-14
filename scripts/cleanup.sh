#!/bin/bash
# Nettoyage simple et fiable - SANS elif

LOG_FILE="logs/cleanup.log"
mkdir -p logs 2>/dev/null

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "🧹 Début du nettoyage"

# 1. Caches Python
log "Suppression des caches..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null

# 2. Logs (garde les 3 derniers)
if [ -d "logs" ]; then
    log "Nettoyage des logs anciens..."
    cd logs || exit
    ls -t *.log 2>/dev/null | tail -n +4 | xargs rm -f 2>/dev/null
    cd - >/dev/null || exit
fi

# 3. Conversations (garde les 10 dernières)
if [ -d "data/conversations" ]; then
    log "Nettoyage des conversations..."
    cd data/conversations || exit
    total=$(ls -1 *.json 2>/dev/null | wc -l)
    if [ "$total" -gt 10 ]; then
        ls -t *.json 2>/dev/null | tail -n +11 | xargs rm -f
        log "Conservé 10 conversations (sur $total)"
    fi
    cd - >/dev/null || exit
fi

# 4. Rapports de tests
rm -rf htmlcov/ 2>/dev/null
rm -f .coverage 2>/dev/null

log "✅ Nettoyage terminé"
