"""
Serviço para geração de conteúdo para Instagram.
"""
import logging
from typing import Dict
from app.graph.state import ProductOffer, InstagramPost
from datetime import datetime

logger = logging.getLogger(__name__)


class ContentGenerator:
    """
    Gera conteúdo otimizado para Instagram a partir de ofertas.
    """

    def __init__(self):
        self.hashtags = [
            "#achadinhos",
            "#shopee",
            "#ofertadodia",
            "#desconto",
            "#economizar",
            "#comprasinteligentes",
            "#promoção",
            "#blackfriday"
        ]

    def create_post_content(self, offer: ProductOffer) -> InstagramPost:
        """
        Cria o conteúdo completo do post (caption + imagem).

        Args:
            offer: Oferta selecionada

        Returns:
            Conteúdo formatado para publicação
        """
        logger.info(f"Gerando conteúdo para oferta: {offer['name']}")

        caption = self._generate_caption(offer)

        product_link = offer.get("affiliate_link") or offer.get("product_url", "")

        post_content = InstagramPost(
            post_id=None,
            image_url=offer["image_url"],
            caption=caption,
            published_at=None,
            product_link=product_link
        )

        return post_content

    def _generate_caption(self, offer: ProductOffer) -> str:
        """
        Gera uma legenda atraente para o post.

        Args:
            offer: Oferta do produto

        Returns:
            Legenda formatada
        """
        # Calcula preços — priceMin/priceMax da Shopee são variantes, não original/atual.
        # Recalcula o preço original a partir do desconto quando são iguais.
        current_price = offer.get("price", 0) or 0
        original_price = offer.get("original_price", 0) or 0
        discount = offer.get("discount_percentage", 0) or 0

        if discount > 0 and current_price > 0 and (not original_price or original_price == current_price):
            original_price = round(current_price / (1 - discount / 100), 2)

        savings = round(original_price - current_price, 2) if original_price > current_price else 0

        # Emoji baseado na categoria (pode ser expandido)
        emoji = self._get_category_emoji(offer.get("category", ""))

        # Monta a legenda
        caption_parts = [
            f"{emoji} ACHADO DO DIA! {emoji}",
            "",
            f"✨ {offer['name']}",
            "",
        ]

        # Adiciona informações de preço
        if offer.get("discount_percentage"):
            discount = int(offer["discount_percentage"])
            caption_parts.append(f"🔥 {discount}% DE DESCONTO!")

        if original_price:
            caption_parts.append(f"💰 De R$ {original_price:.2f} por apenas R$ {current_price:.2f}")
            if savings:
                caption_parts.append(f"💵 Você economiza R$ {savings:.2f}!")
        else:
            caption_parts.append(f"💰 Apenas R$ {current_price:.2f}")

        # Adiciona rating se disponível
        if offer.get("rating"):
            rating = offer["rating"]
            stars = "⭐" * int(rating)
            caption_parts.append(f"\n{stars} Avaliação: {rating}/5.0")

        # Call to action
        caption_parts.extend([
            "",
            "📱 Quer o link? É só comentar aqui embaixo!",
            "📩 Enviamos o link por DM pra você!",
            "",
            "Corre que é por tempo limitado! ⏰",
            ""
        ])

        # Adiciona hashtags
        caption_parts.append(" ".join(self.hashtags))

        return "\n".join(caption_parts)

    def _get_category_emoji(self, category: str) -> str:
        """
        Retorna emoji apropriado baseado na categoria.

        Args:
            category: Nome da categoria

        Returns:
            Emoji representativo
        """
        category_lower = category.lower() if category else ""

        emoji_map = {
            "eletrônicos": "📱",
            "moda": "👗",
            "beleza": "💄",
            "casa": "🏠",
            "esporte": "⚽",
            "livros": "📚",
            "brinquedos": "🧸",
            "alimentos": "🍔",
            "pets": "🐾",
            "saúde": "💊"
        }

        for key, emoji in emoji_map.items():
            if key in category_lower:
                return emoji

        return "🎁"  # Emoji padrão
