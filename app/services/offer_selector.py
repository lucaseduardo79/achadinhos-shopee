"""
Serviço para seleção e filtragem de ofertas da Shopee.
"""
import logging
from typing import List, Dict, Any
from app.graph.state import ProductOffer

logger = logging.getLogger(__name__)


class OfferSelector:
    """
    Seleciona as melhores ofertas com base em critérios configuráveis.
    """

    def __init__(
        self,
        min_rating: float = 4.0,
        min_discount: float = 30.0,
        min_commission: float = 5.0,
        allowed_categories: List[str] = None
    ):
        """
        Args:
            min_rating: Rating mínimo do produto
            min_discount: Desconto mínimo em porcentagem
            min_commission: Comissão mínima em porcentagem
            allowed_categories: Não suportado pela API de Afiliados (ignorado)
        """
        self.min_rating = min_rating
        self.min_discount = min_discount
        self.min_commission = min_commission
        self.allowed_categories = allowed_categories

        if allowed_categories:
            logger.warning(
                "allowed_categories configurado, mas a API de Afiliados da Shopee "
                "não retorna category_id. Filtro de categorias será ignorado. "
                "Use SHOPEE_SEARCH_KEYWORD para filtrar por palavras-chave."
            )

    def select_best_offers(
        self,
        offers: List[Dict[str, Any]],
        limit: int = 1
    ) -> List[ProductOffer]:
        """
        Filtra e seleciona as melhores ofertas.

        Args:
            offers: Lista de ofertas brutas da API
            limit: Número máximo de ofertas a retornar

        Returns:
            Lista de ofertas selecionadas e formatadas
        """
        logger.info(f"Selecionando ofertas de {len(offers)} candidatas...")

        filtered = []

        for offer in offers:
            if self._should_include_offer(offer):
                formatted = self._format_offer(offer)
                filtered.append(formatted)

        # Ordena por score (desconto * rating * comissão)
        filtered.sort(key=self._calculate_score, reverse=True)

        selected = filtered[:limit]

        logger.info(
            f"{len(selected)} oferta(s) selecionada(s) de {len(filtered)} "
            f"que passaram nos filtros"
        )

        return selected

    def _should_include_offer(self, offer: Dict[str, Any]) -> bool:
        """Verifica se uma oferta atende aos critérios mínimos."""

        # Valida rating
        rating = float(offer.get("ratingStar") or 0)
        if rating < self.min_rating:
            return False

        # Valida desconto
        discount = self._extract_discount_percentage(offer)
        if discount < self.min_discount:
            return False

        # Valida comissão
        commission = float(offer.get("commissionRate") or 0)
        if commission < self.min_commission:
            return False

        return True

    def _extract_discount_percentage(self, offer: Dict[str, Any]) -> float:
        """Extrai a porcentagem de desconto de uma oferta."""
        # A API de Afiliados retorna priceDiscountRate como número
        if "priceDiscountRate" in offer:
            try:
                return float(offer["priceDiscountRate"])
            except (ValueError, TypeError):
                pass

        # Fallback: calcula a partir de priceMin e priceMax
        price = offer.get("priceMin", 0)
        original_price = offer.get("priceMax", 0)

        if original_price and price:
            discount = ((original_price - price) / original_price) * 100
            return round(discount, 2)

        return 0.0

    def _calculate_score(self, offer: ProductOffer) -> float:
        """
        Calcula um score para ranquear ofertas.

        Score = desconto * rating * comissão
        """
        discount = offer.get("discount_percentage", 0) or 0
        rating = offer.get("rating", 0) or 0
        commission = offer.get("commission", 0) or 0

        return discount * rating * commission

    def _format_offer(self, raw_offer: Dict[str, Any]) -> ProductOffer:
        """
        Converte oferta bruta da API GraphQL para o formato tipado.

        Args:
            raw_offer: Oferta bruta da API de Afiliados

        Returns:
            Oferta formatada
        """
        discount = self._extract_discount_percentage(raw_offer)

        return ProductOffer(
            product_id=str(raw_offer.get("itemId", "")),
            name=raw_offer.get("productName", "Produto sem nome"),
            price=float(raw_offer.get("priceMin") or 0),
            original_price=float(raw_offer.get("priceMax") or 0) or None,
            discount_percentage=discount,
            rating=float(raw_offer.get("ratingStar") or 0),
            image_url=raw_offer.get("imageUrl", ""),
            product_url=raw_offer.get("offerLink", ""),
            affiliate_link=None,
            commission=float(raw_offer.get("commissionRate") or 0),
            category=None,
            sales=int(raw_offer.get("sales") or 0),
            shop_name=raw_offer.get("shopName"),
            shop_type=raw_offer.get("shopType"),
            commission_value=float(raw_offer.get("commission") or 0),
        )
