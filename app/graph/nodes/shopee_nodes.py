"""
Nós do grafo relacionados à integração com a Shopee.
"""
import os
from typing import Dict, Any
import logging
from app.graph.state import GraphState
from app.integrations.shopee.client import ShopeeClient
from app.services.offer_selector import OfferSelector
from app.services.state_store import get_recently_published_ids

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
        selector = OfferSelector(
            min_rating=float(os.getenv("MIN_RATING", 4.0)),
            min_discount=float(os.getenv("MIN_DISCOUNT", 30.0)),
            min_commission=float(os.getenv("MIN_COMMISSION", 5.0)),
        )
        raw_offers = state.get("raw_offers", [])

        if not raw_offers:
            logger.warning(f"[{state['execution_id']}] Nenhuma oferta bruta disponível")
            return {
                "step": "no_offers",
                "error": "Nenhuma oferta disponível para seleção"
            }

        # Filtra produtos já publicados nos últimos 7 dias
        published_ids = get_recently_published_ids(days=7)
        if published_ids:
            before = len(raw_offers)
            raw_offers = [o for o in raw_offers if str(o.get("itemId", "")) not in published_ids]
            logger.info(f"[{state['execution_id']}] {before - len(raw_offers)} oferta(s) ignorada(s) por duplicata")

        if not raw_offers:
            logger.warning(f"[{state['execution_id']}] Todas as ofertas já foram publicadas recentemente")
            return {
                "step": "no_offers",
                "error": "Nenhuma oferta nova disponível (todas já publicadas nos últimos 7 dias)"
            }

        selected = selector.select_best_offers(raw_offers, limit=1)

        # Gera short links para as ofertas selecionadas
        client = ShopeeClient()
        for offer in selected:
            if offer.get("product_url"):
                short_link = client.generate_short_link(
                    origin_url=offer["product_url"],
                    sub_ids=["instagram"]
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
