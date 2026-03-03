"""
Testes para o OfferSelector.
"""
import pytest
from app.services.offer_selector import OfferSelector


class TestOfferSelector:
    """Testes do seletor de ofertas."""

    def test_select_best_offers_filters_by_rating(self):
        """Testa que ofertas com rating baixo são filtradas."""
        selector = OfferSelector(min_rating=4.0)

        offers = [
            {
                "itemId": "1",
                "productName": "Produto Bom",
                "ratingStar": 4.5,
                "priceDiscountRate": 50,
                "commissionRate": 10.0,
                "priceMin": 50.0,
                "priceMax": 100.0,
                "imageUrl": "url",
                "offerLink": "url"
            },
            {
                "itemId": "2",
                "productName": "Produto Ruim",
                "ratingStar": 3.0,
                "priceDiscountRate": 50,
                "commissionRate": 10.0,
                "priceMin": 50.0,
                "priceMax": 100.0,
                "imageUrl": "url",
                "offerLink": "url"
            }
        ]

        selected = selector.select_best_offers(offers, limit=10)

        assert len(selected) == 1
        assert selected[0]["product_id"] == "1"

    def test_select_best_offers_filters_by_discount(self):
        """Testa que ofertas com desconto baixo são filtradas."""
        selector = OfferSelector(min_discount=30.0)

        offers = [
            {
                "itemId": "1",
                "productName": "Produto Com Desconto",
                "ratingStar": 4.5,
                "priceDiscountRate": 50,
                "commissionRate": 10.0,
                "priceMin": 50.0,
                "priceMax": 100.0,
                "imageUrl": "url",
                "offerLink": "url"
            },
            {
                "itemId": "2",
                "productName": "Produto Sem Desconto",
                "ratingStar": 4.5,
                "priceDiscountRate": 10,
                "commissionRate": 10.0,
                "priceMin": 90.0,
                "priceMax": 100.0,
                "imageUrl": "url",
                "offerLink": "url"
            }
        ]

        selected = selector.select_best_offers(offers, limit=10)

        assert len(selected) == 1
        assert selected[0]["product_id"] == "1"

    def test_select_best_offers_respects_limit(self):
        """Testa que o limite de ofertas é respeitado."""
        selector = OfferSelector()

        offers = [
            {
                "itemId": str(i),
                "productName": f"Produto {i}",
                "ratingStar": 4.5,
                "priceDiscountRate": 50,
                "commissionRate": 10.0,
                "priceMin": 50.0,
                "priceMax": 100.0,
                "imageUrl": "url",
                "offerLink": "url"
            }
            for i in range(10)
        ]

        selected = selector.select_best_offers(offers, limit=3)

        assert len(selected) == 3

    def test_format_offer_maps_affiliate_link(self):
        """Testa que offerLink é mapeado para product_url."""
        selector = OfferSelector()

        offers = [
            {
                "itemId": "999",
                "productName": "Produto Teste",
                "ratingStar": 4.5,
                "priceDiscountRate": 60,
                "commissionRate": 8.0,
                "priceMin": 40.0,
                "priceMax": 100.0,
                "imageUrl": "https://img.shopee.com/test.jpg",
                "offerLink": "https://shope.ee/affiliate123",
                "sales": 500,
                "shopName": "TestShop",
                "shopType": "Mall",
                "commission": 3.20
            }
        ]

        selected = selector.select_best_offers(offers, limit=1)

        assert len(selected) == 1
        offer = selected[0]
        assert offer["product_id"] == "999"
        assert offer["product_url"] == "https://shope.ee/affiliate123"
        assert offer["price"] == 40.0
        assert offer["original_price"] == 100.0
        assert offer["discount_percentage"] == 60
        assert offer["shop_name"] == "TestShop"
        assert offer["commission_value"] == 3.20

    def test_discount_extraction_from_price_discount_rate(self):
        """Testa extração de desconto do campo priceDiscountRate."""
        selector = OfferSelector()
        offer = {"priceDiscountRate": 45}
        assert selector._extract_discount_percentage(offer) == 45.0

    def test_discount_extraction_fallback_to_price_calculation(self):
        """Testa fallback de cálculo de desconto quando priceDiscountRate ausente."""
        selector = OfferSelector()
        offer = {"priceMin": 60.0, "priceMax": 100.0}
        assert selector._extract_discount_percentage(offer) == 40.0

    def test_filters_by_commission(self):
        """Testa que ofertas com comissão baixa são filtradas."""
        selector = OfferSelector(min_commission=8.0)

        offers = [
            {
                "itemId": "1",
                "productName": "Alta Comissão",
                "ratingStar": 4.5,
                "priceDiscountRate": 50,
                "commissionRate": 10.0,
                "priceMin": 50.0,
                "priceMax": 100.0,
                "imageUrl": "url",
                "offerLink": "url"
            },
            {
                "itemId": "2",
                "productName": "Baixa Comissão",
                "ratingStar": 4.5,
                "priceDiscountRate": 50,
                "commissionRate": 3.0,
                "priceMin": 50.0,
                "priceMax": 100.0,
                "imageUrl": "url",
                "offerLink": "url"
            }
        ]

        selected = selector.select_best_offers(offers, limit=10)

        assert len(selected) == 1
        assert selected[0]["product_id"] == "1"
