"""
Testes para o ShopeeClient (API de Afiliados GraphQL).
"""
import hashlib
from unittest.mock import patch, MagicMock
import pytest
from app.integrations.shopee.client import ShopeeClient, ShopeeAPIError


class TestShopeeClientAuth:
    """Testes de autenticação."""

    @patch.dict("os.environ", {
        "SHOPEE_APP_ID": "test_app_id",
        "SHOPEE_SECRET": "test_secret"
    })
    def test_generate_signature(self):
        """Verifica que a assinatura SHA256 é gerada corretamente."""
        client = ShopeeClient()
        timestamp = 1700000000
        payload = '{"query":"{ test }"}'

        expected_raw = f"test_app_id{timestamp}{payload}test_secret"
        expected_sig = hashlib.sha256(expected_raw.encode("utf-8")).hexdigest()

        actual_sig = client._generate_signature(timestamp, payload)
        assert actual_sig == expected_sig

    @patch.dict("os.environ", {
        "SHOPEE_APP_ID": "myapp",
        "SHOPEE_SECRET": "mysecret"
    })
    def test_auth_header_format(self):
        """Verifica o formato do header Authorization."""
        client = ShopeeClient()
        headers = client._get_auth_header('{"query":"test"}')

        assert "Authorization" in headers
        auth = headers["Authorization"]
        assert auth.startswith("SHA256 Credential=myapp, Timestamp=")
        assert ", Signature=" in auth
        assert headers["Content-Type"] == "application/json"


class TestShopeeClientMock:
    """Testes com dados mock (sem credenciais)."""

    @patch.dict("os.environ", {}, clear=True)
    def test_falls_back_to_mock_without_credentials(self):
        """Sem credenciais, retorna dados mock."""
        client = ShopeeClient()
        offers = client.get_daily_deals(limit=2)

        assert len(offers) == 2
        assert "itemId" in offers[0]
        assert "offerLink" in offers[0]
        assert "priceDiscountRate" in offers[0]
        assert "ratingStar" in offers[0]
        assert "commissionRate" in offers[0]

    @patch.dict("os.environ", {}, clear=True)
    def test_mock_offers_have_all_required_fields(self):
        """Mock ofertas contêm todos os campos necessários."""
        client = ShopeeClient()
        offers = client.get_daily_deals()

        required_fields = [
            "itemId", "productName", "productLink", "offerLink",
            "imageUrl", "priceMin", "priceMax", "priceDiscountRate",
            "ratingStar", "commissionRate", "commission"
        ]

        for offer in offers:
            for field in required_fields:
                assert field in offer, f"Campo {field} ausente no mock"

    @patch.dict("os.environ", {}, clear=True)
    def test_generate_short_link_returns_none_without_credentials(self):
        """Sem credenciais, generate_short_link retorna None."""
        client = ShopeeClient()
        result = client.generate_short_link("https://shopee.com.br/product/123")
        assert result is None


class TestShopeeClientRetry:
    """Testes de retry e tratamento de erros."""

    @patch.dict("os.environ", {
        "SHOPEE_APP_ID": "app",
        "SHOPEE_SECRET": "secret"
    })
    @patch("app.integrations.shopee.client.requests.post")
    def test_retries_on_rate_limit(self, mock_post):
        """Verifica retry em rate limit (10030)."""
        rate_limit_response = MagicMock()
        rate_limit_response.status_code = 200
        rate_limit_response.json.return_value = {
            "errors": [{"extensions": {"code": 10030, "message": "Rate limit"}}]
        }
        rate_limit_response.raise_for_status = MagicMock()

        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "data": {"productOfferV2": {"nodes": [], "pageInfo": {}}}
        }
        success_response.raise_for_status = MagicMock()

        mock_post.side_effect = [rate_limit_response, success_response]

        client = ShopeeClient()
        client.RATE_LIMIT_DELAY_SECONDS = 0
        result = client.get_daily_deals()

        assert result == []
        assert mock_post.call_count == 2

    @patch.dict("os.environ", {
        "SHOPEE_APP_ID": "app",
        "SHOPEE_SECRET": "secret"
    })
    @patch("app.integrations.shopee.client.requests.post")
    def test_raises_on_non_retryable_error(self, mock_post):
        """Verifica que erros não-retentáveis levantam exceção."""
        error_response = MagicMock()
        error_response.status_code = 200
        error_response.json.return_value = {
            "errors": [{"extensions": {"code": 11001, "message": "Invalid params"}}]
        }
        error_response.raise_for_status = MagicMock()

        mock_post.return_value = error_response

        client = ShopeeClient()
        with pytest.raises(ShopeeAPIError) as exc_info:
            client.get_daily_deals()

        assert exc_info.value.code == 11001

    @patch.dict("os.environ", {
        "SHOPEE_APP_ID": "app",
        "SHOPEE_SECRET": "secret"
    })
    @patch("app.integrations.shopee.client.requests.post")
    def test_generate_short_link_success(self, mock_post):
        """Verifica geração de short link com sucesso."""
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "data": {
                "generateShortLink": {
                    "shortLink": "https://shope.ee/abc123"
                }
            }
        }
        success_response.raise_for_status = MagicMock()

        mock_post.return_value = success_response

        client = ShopeeClient()
        result = client.generate_short_link(
            "https://shopee.com.br/product/123",
            sub_ids=["instagram"]
        )

        assert result == "https://shope.ee/abc123"

    @patch.dict("os.environ", {
        "SHOPEE_APP_ID": "app",
        "SHOPEE_SECRET": "secret"
    })
    @patch("app.integrations.shopee.client.requests.post")
    def test_generate_short_link_returns_none_on_error(self, mock_post):
        """Verifica que generate_short_link retorna None em caso de erro."""
        mock_post.side_effect = Exception("Network error")

        client = ShopeeClient()
        result = client.generate_short_link("https://shopee.com.br/product/123")

        assert result is None
