"""
Nós do grafo relacionados a logging e observabilidade.
"""
from typing import Dict, Any
import logging
from datetime import datetime
from app.graph.state import GraphState

logger = logging.getLogger(__name__)


def logar_evento(state: GraphState) -> Dict[str, Any]:
    """
    Registra eventos importantes do fluxo para auditoria e debugging.

    Args:
        state: Estado atual do grafo

    Returns:
        Estado sem alterações (apenas logging)
    """
    execution_id = state.get("execution_id", "unknown")
    step = state.get("step", "unknown")
    error = state.get("error")

    log_entry = {
        "execution_id": execution_id,
        "step": step,
        "timestamp": datetime.now().isoformat(),
        "error": error,
        "offers_count": len(state.get("selected_offers") or []),
        "comments_count": len(state.get("comments") or [])
    }

    if error:
        logger.error(f"[{execution_id}] Evento: {log_entry}")
    else:
        logger.info(f"[{execution_id}] Evento: {log_entry}")

    # Aqui você pode adicionar integração com sistemas de observabilidade
    # como Datadog, New Relic, CloudWatch, etc.

    return {
        "step": step,  # Mantém o step atual
        "error": error
    }


def handle_error(state: GraphState) -> Dict[str, Any]:
    """
    Manipula erros no fluxo, decidindo se deve tentar novamente ou falhar.

    Args:
        state: Estado atual do grafo

    Returns:
        Atualização do estado com decisão de retry ou falha definitiva
    """
    execution_id = state.get("execution_id", "unknown")
    retry_count = state.get("retry_count", 0)
    max_retries = 3

    logger.warning(f"[{execution_id}] Handling error. Retry count: {retry_count}/{max_retries}")

    if retry_count < max_retries:
        logger.info(f"[{execution_id}] Tentando novamente...")
        return {
            "retry_count": retry_count + 1,
            "step": "retry",
            "error": None
        }
    else:
        logger.error(f"[{execution_id}] Máximo de tentativas atingido. Falha definitiva.")
        return {
            "step": "failed",
            "error": state.get("error", "Erro desconhecido")
        }
