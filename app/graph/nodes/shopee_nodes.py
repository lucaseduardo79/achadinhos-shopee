"""
Nós do grafo relacionados à integração com a Shopee.
"""
import os
from typing import Dict, Any
import logging
from app.graph.state import GraphState
from app.integrations.shopee.client import ShopeeClient
from app.services.offer_selector import OfferSelector

logger = logging.getLogger(__name__)


def buscar_ofertas_shopee(state: GraphState) -> Dict[str, Any]:
    """
    Busca ofertas do dia na Shopee via API de Afiliados GraphQL.

    Args:
        state: Estado atual do grafo

    Returns:
        Atualização do estado com as ofertas brutas
    """
    logger.info(f"[{state['execution_id']}] Buscando ofertas da Shopee...")

    try:
        client = ShopeeClient()

        keyword = (state.get("metadata") or {}).get(
            "search_keyword",
            os.getenv("SHOPEE_SEARCH_KEYWORD", "")
        )

        offers = client.get_daily_deals(keyword=keyword)

        logger.info(f"[{state['execution_id']}] {len(offers)} ofertas encontradas")

        return {
            "raw_offers": offers,
            "step": "offers_fetched",
            "error": None
        }

    except Exception as e:
        logger.error(f"[{state['execution_id']}] Erro ao buscar ofertas: {str(e)}")
        return {
            "step": "error",
            "error": f"Erro ao buscar ofertas da Shopee: {str(e)}"
        }


def selecionar_ofertas_do_dia(state: GraphState) -> Dict[str, Any]:
    """
    Filtra e seleciona as melhores ofertas para publicação.

    Critérios:
    - Rating >= 4.0
    - Desconto >= 30%
    - Comissão >= 5%

    Args:
        state: Estado atual do grafo

    Returns:
        Atualização do estado com as ofertas selecionadas
    """
    logger.info(f"[{state['execution_id']}] Selecionando ofertas...")

    try:
        selector = OfferSelector()
        raw_offers = state.get("raw_offers", [])

        if not raw_offers:
            logger.warning(f"[{state['execution_id']}] Nenhuma oferta bruta disponível")
            return {
                "step": "no_offers",
                "error": "Nenhuma oferta disponível para seleção"
            }

        selected = selector.select_best_offers(raw_offers, limit=1)

        # Gera short links para as ofertas selecionadas
        client = ShopeeClient()
        for offer in selected:
            if offer.get("product_url"):
                short_link = client.generate_short_link(
                    origin_url=offer["product_url"],
                    sub_ids=["instagram", state.get("execution_id", "unknown")]
                )
                if short_link:
                    offer["affiliate_link"] = short_link

        logger.info(f"[{state['execution_id']}] {len(selected)} oferta(s) selecionada(s)")

        return {
            "selected_offers": selected,
            "current_offer": selected[0] if selected else None,
            "step": "offers_selected",
            "error": None
        }

    except Exception as e:
        logger.error(f"[{state['execution_id']}] Erro ao selecionar ofertas: {str(e)}")
        return {
            "step": "error",
            "error": f"Erro ao selecionar ofertas: {str(e)}"
        }
