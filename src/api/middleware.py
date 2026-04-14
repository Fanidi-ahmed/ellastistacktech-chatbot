"""
Middleware pour limiter le taux de requêtes - Version robuste
"""
import time
from collections import defaultdict
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

# Import sécurisé de Config
try:
    from src.core.config import Config
    config = Config.get_instance()
except Exception as e:
    logger.warning(f"Config non disponible dans middleware: {e}")
    # Fallback : valeurs par défaut
    class DummyConfig:
        RATE_LIMIT_PER_MINUTE = 60
        RATE_LIMIT_PER_DAY = 500
    config = DummyConfig()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware de rate limiting - Sans blocage en cas d'erreur"""
    
    def __init__(self, app):
        super().__init__(app)
        self.requests_per_ip = defaultdict(list)
        logger.info("✅ RateLimitMiddleware activé")

    async def dispatch(self, request: Request, call_next):
        try:
            # Récupérer l'IP du client
            client_ip = request.client.host if request.client else "unknown"
            
            # Nettoyer les anciennes requêtes (plus vieilles que 60 secondes)
            now = time.time()
            self.requests_per_ip[client_ip] = [
                req_time for req_time in self.requests_per_ip[client_ip]
                if now - req_time < 60
            ]
            
            # Vérifier la limite par minute (avec fallback sécurisé)
            limit = getattr(config, 'RATE_LIMIT_PER_MINUTE', 60)
            
            if len(self.requests_per_ip[client_ip]) >= limit:
                logger.warning(f"Rate limit dépassé pour {client_ip}")
                raise HTTPException(
                    status_code=429, 
                    detail=f"Trop de requêtes. Limite: {limit} par minute. Veuillez patienter."
                )
            
            # Enregistrer cette requête
            self.requests_per_ip[client_ip].append(now)
            
        except HTTPException:
            raise
        except Exception as e:
            # En cas d'erreur, on laisse passer (pas de blocage)
            logger.error(f"Erreur rate limiting: {e}")
        
        # Continuer le traitement normal
        response = await call_next(request)
        return response
