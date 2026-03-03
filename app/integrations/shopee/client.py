"""
Cliente para integração com a API de Afiliados da Shopee (GraphQL).
"""
import os
import time
import json
import hashlib
import logging
from typing import List, Dict, Any, Optional
import requests

logger = logging.getLogger(__name__)


class ShopeeAPIError(Exception):
    """Exceção customizada para erros da API da Shopee."""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"Shopee API Error {code}: {message}")


class ShopeeClient:
    """
    Cliente para interagir com a API de Afiliados da Shopee via GraphQL.

    Autenticação via SHA256:
    Header: SHA256 Credential={AppId}, Timestamp={Timestamp}, Signature={Signature}
    Signature = SHA256(AppId + Timestamp + Payload + Secret)
    """

    ERROR_SYSTEM = 10000
    ERROR_PARSE = 10010
    ERROR_INVALID_SIGNATURE = 10020
    ERROR_RATE_LIMIT = 10030
    ERROR_NO_ACCESS = 10035
    ERROR_PARAMS = 11001

    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 2
    RATE_LIMIT_DELAY_SECONDS = 5

    def __init__(self):
        self.app_id = os.getenv("SHOPEE_APP_ID")
        self.secret = os.getenv("SHOPEE_SECRET")
        self.base_url = os.getenv(
            "SHOPEE_API_URL",
            "https://open-api.affiliate.shopee.com.br/graphql"
        )
        self._credentials_configured = bool(self.app_id and self.secret)

        if not self._credentials_configured:
            logger.warning(
                "Credenciais da Shopee Affiliate não configuradas. "
                "Defina SHOPEE_APP_ID e SHOPEE_SECRET. Usando dados mock."
            )

    def _generate_signature(self, timestamp: int, payload: str) -> str:
        """Gera a assinatura SHA256 para autenticação."""
        raw = f"{self.app_id}{timestamp}{payload}{self.secret}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _get_auth_header(self, payload: str) -> Dict[str, str]:
        """Gera os headers de autenticação para a requisição."""
        timestamp = int(time.time())
        signature = self._generate_signature(timestamp, payload)

        return {
            "Content-Type": "application/json",
            "Authorization": (
                f"SHA256 Credential={self.app_id}, "
                f"Timestamp={timestamp}, "
                f"Signature={signature}"
            )
        }

    def _execute_graphql(self, query: str) -> Dict[str, Any]:
        """
        Executa uma query/mutation GraphQL com retry e tratamento de erros.

        Raises:
            ShopeeAPIError: Para erros da API
            requests.RequestException: Para erros de rede
        """
        payload = json.dumps({"query": query}, separators=(",", ":"))

        last_exception = None

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                headers = self._get_auth_header(payload)
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    data=payload,
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()

                if "errors" in data:
                    error = data["errors"][0]
                    ext = error.get("extensions", {})
                    error_code = ext.get("code", error.get("code", 0))
                    error_msg = ext.get("message", error.get("message", "Unknown error"))

                    if error_code == self.ERROR_RATE_LIMIT and attempt < self.MAX_RETRIES:
                        logger.warning(
                            f"Rate limit (tentativa {attempt}/{self.MAX_RETRIES}). "
                            f"Aguardando {self.RATE_LIMIT_DELAY_SECONDS}s..."
                        )
                        time.sleep(self.RATE_LIMIT_DELAY_SECONDS)
                        last_exception = ShopeeAPIError(error_code, error_msg)
                        continue

                    if error_code == self.ERROR_INVALID_SIGNATURE and attempt < self.MAX_RETRIES:
                        logger.warning(
                            f"Assinatura inválida (tentativa {attempt}). Retentando..."
                        )
                        time.sleep(1)
                        last_exception = ShopeeAPIError(error_code, error_msg)
                        continue

                    if error_code == self.ERROR_SYSTEM and attempt < self.MAX_RETRIES:
                        delay = self.RETRY_DELAY_SECONDS * (2 ** (attempt - 1))
                        logger.warning(
                            f"Erro de sistema (tentativa {attempt}). "
                            f"Retentando em {delay}s..."
                        )
                        time.sleep(delay)
                        last_exception = ShopeeAPIError(error_code, error_msg)
                        continue

                    raise ShopeeAPIError(error_code, error_msg)

                return data.get("data", {})

            except requests.RequestException as e:
                logger.warning(
                    f"Erro de rede (tentativa {attempt}/{self.MAX_RETRIES}): {e}"
                )
                last_exception = e
                if attempt < self.MAX_RETRIES:
                    delay = self.RETRY_DELAY_SECONDS * (2 ** (attempt - 1))
                    time.sleep(delay)

        raise last_exception

    def get_daily_deals(
        self,
        limit: int = 50,
        keyword: str = "",
        list_type: int = 1,
        sort_type: int = 5,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Busca ofertas da Shopee via productOfferV2 query.

        Args:
            limit: Número máximo de ofertas (max 50 por página)
            keyword: Palavra-chave de busca (vazio = todas)
            list_type: 0=Recommended, 1=High Commission, 2=Top Performance
            sort_type: 1=Relevance, 2=Sales, 3=High Price, 4=Low Price, 5=Commission
            page: Número da página

        Returns:
            Lista de ofertas brutas da API
        """
        logger.info(f"Buscando até {limit} ofertas do dia...")

        if not self._credentials_configured:
            logger.warning("Usando dados MOCK da Shopee (configure SHOPEE_APP_ID e SHOPEE_SECRET)")
            return self._get_mock_offers(limit)

        query = """
{
  productOfferV2(
    keyword: "%s",
    listType: %d,
    sortType: %d,
    page: %d,
    limit: %d
  ) {
    nodes {
      itemId
      productName
      productLink
      offerLink
      imageUrl
      priceMin
      priceMax
      priceDiscountRate
      sales
      ratingStar
      commissionRate
      sellerCommissionRate
      shopeeCommissionRate
      commission
      shopId
      shopName
      shopType
      periodStartTime
      periodEndTime
    }
    pageInfo {
      page
      limit
      hasNextPage
    }
  }
}
""".strip() % (keyword, list_type, sort_type, page, limit)

        data = self._execute_graphql(query)

        product_offer = data.get("productOfferV2", {})
        nodes = product_offer.get("nodes", [])
        page_info = product_offer.get("pageInfo", {})

        logger.info(
            f"{len(nodes)} ofertas retornadas. "
            f"hasNextPage={page_info.get('hasNextPage', False)}"
        )

        return nodes

    def generate_short_link(
        self,
        origin_url: str,
        sub_ids: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Gera um link curto de afiliado via generateShortLink mutation.

        Args:
            origin_url: URL original do produto Shopee
            sub_ids: Lista de sub-IDs para tracking (ex: ["instagram", "post_123"])

        Returns:
            URL curta ou None se falhar
        """
        if not self._credentials_configured:
            logger.warning("Credenciais não configuradas. Não é possível gerar short link.")
            return None

        sub_ids_str = ""
        if sub_ids:
            formatted = ", ".join(f'"{sid}"' for sid in sub_ids)
            sub_ids_str = f", subIds: [{formatted}]"

        mutation = """
mutation {
  generateShortLink(input: {
    originUrl: "%s"%s
  }) {
    shortLink
  }
}
""".strip() % (origin_url, sub_ids_str)

        try:
            data = self._execute_graphql(mutation)
            short_link = data.get("generateShortLink", {}).get("shortLink")

            if short_link:
                logger.info(f"Short link gerado: {short_link}")
            else:
                logger.warning("Short link retornado vazio pela API")

            return short_link

        except Exception as e:
            logger.error(f"Erro ao gerar short link: {e}")
            return None

    def _get_mock_offers(self, limit: int) -> List[Dict[str, Any]]:
        """Retorna ofertas mock no formato da API de Afiliados GraphQL."""
        mock_offers = [
            {
                "itemId": "12345",
                "productName": "Fone de Ouvido Bluetooth Premium",
                "productLink": "https://shopee.com.br/product/12345",
                "offerLink": "https://shope.ee/abc123",
                "imageUrl": "https://via.placeholder.com/500x500/FF6D00/FFFFFF?text=Fone+Bluetooth",
                "priceMin": 89.90,
                "priceMax": 299.90,
                "priceDiscountRate": 70,
                "sales": 1500,
                "ratingStar": 4.8,
                "commissionRate": 8.5,
                "sellerCommissionRate": 5.0,
                "shopeeCommissionRate": 3.5,
                "commission": 7.64,
                "shopId": "shop001",
                "shopName": "TechStore BR",
                "shopType": "Mall",
                "periodStartTime": None,
                "periodEndTime": None
            },
            {
                "itemId": "67890",
                "productName": "Smartwatch Esportivo",
                "productLink": "https://shopee.com.br/product/67890",
                "offerLink": "https://shope.ee/def456",
                "imageUrl": "https://via.placeholder.com/500x500/FF6D00/FFFFFF?text=Smartwatch",
                "priceMin": 159.90,
                "priceMax": 499.90,
                "priceDiscountRate": 68,
                "sales": 3200,
                "ratingStar": 4.6,
                "commissionRate": 10.0,
                "sellerCommissionRate": 6.0,
                "shopeeCommissionRate": 4.0,
                "commission": 15.99,
                "shopId": "shop002",
                "shopName": "SportGear",
                "shopType": "Preferred",
                "periodStartTime": None,
                "periodEndTime": None
            },
            {
                "itemId": "11111",
                "productName": "Kit 10 Canetas Gel Coloridas",
                "productLink": "https://shopee.com.br/product/11111",
                "offerLink": "https://shope.ee/ghi789",
                "imageUrl": "https://via.placeholder.com/500x500/FF6D00/FFFFFF?text=Canetas",
                "priceMin": 12.90,
                "priceMax": 39.90,
                "priceDiscountRate": 68,
                "sales": 8500,
                "ratingStar": 4.9,
                "commissionRate": 5.0,
                "sellerCommissionRate": 3.0,
                "shopeeCommissionRate": 2.0,
                "commission": 0.65,
                "shopId": "shop003",
                "shopName": "PapelArt",
                "shopType": "Normal",
                "periodStartTime": None,
                "periodEndTime": None
            }
        ]
        return mock_offers[:limit]
