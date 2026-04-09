"""
Serviço para processamento e validação de comentários.
"""
import logging
import re
from typing import Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CommentProcessor:
    """
    Processa comentários para determinar se devem receber resposta automática.
    """

    def __init__(self):
        # Palavras-chave que indicam interesse no produto
        self.interest_keywords = [
            "link",
            "quero",
            "preço",
            "preco",
            "valor",
            "comprar",
            "quanto",
            "enviar",
            "me manda",
            "interessei",
            "queria"
        ]

        # Tempo mínimo entre processamentos do mesmo usuário (em minutos)
        self.cooldown_minutes = 60

        # Cache de usuários processados recentemente
        self._processed_users: Dict[str, datetime] = {}

    def should_process_comment(self, comment: Dict[str, Any]) -> bool:
        """
        Determina se um comentário deve ser processado (receber DM + resposta).

        Args:
            comment: Comentário a avaliar

        Returns:
            True se deve processar, False caso contrário
        """
        # Já foi processado?
        if comment.get("processed", False):
            logger.debug(f"Comentário {comment['comment_id']} já foi processado")
            return False

        # Verifica cooldown do usuário
        if not self._check_user_cooldown(comment["user_id"]):
            logger.info(
                f"Usuário {comment['username']} em cooldown, ignorando comentário"
            )
            return False

        # Verifica se não é spam
        if self._is_spam(comment["text"]):
            logger.warning(f"Comentário identificado como spam: {comment['text']}")
            return False

        logger.info(f"Comentário {comment['comment_id']} será processado")
        return True

    def _check_user_cooldown(self, user_id: str) -> bool:
        """
        Verifica se o usuário pode receber nova mensagem (cooldown).

        Args:
            user_id: ID do usuário

        Returns:
            True se pode processar, False se está em cooldown
        """
        if user_id not in self._processed_users:
            return True

        last_processed = self._processed_users[user_id]
        time_since = datetime.now() - last_processed

        if time_since < timedelta(minutes=self.cooldown_minutes):
            return False

        return True

    def mark_user_processed(self, user_id: str):
        """
        Marca um usuário como processado recentemente.

        Args:
            user_id: ID do usuário
        """
        self._processed_users[user_id] = datetime.now()

        # Limpa cache antigo (mais de 24h)
        cutoff = datetime.now() - timedelta(hours=24)
        self._processed_users = {
            uid: timestamp
            for uid, timestamp in self._processed_users.items()
            if timestamp > cutoff
        }

    def _has_interest_keywords(self, text: str) -> bool:
        """
        Verifica se o comentário contém palavras-chave de interesse.

        Args:
            text: Texto do comentário

        Returns:
            True se contém palavras de interesse
        """
        text_lower = text.lower()

        for keyword in self.interest_keywords:
            if keyword in text_lower:
                return True

        return False

    def _is_spam(self, text: str) -> bool:
        """
        Detecta se um comentário é provavelmente spam.

        Args:
            text: Texto do comentário

        Returns:
            True se parece spam
        """
        # Comentário muito curto (apenas emoji ou 1-2 letras)
        if len(text.strip()) <= 2:
            return True

        # Muitos caracteres repetidos
        if re.search(r'(.)\1{5,}', text):
            return True

        # Muitos emojis consecutivos (mais de 5)
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "]+",
            flags=re.UNICODE
        )
        emojis = emoji_pattern.findall(text)
        if emojis and len(''.join(emojis)) > 5 and len(text.strip()) == len(''.join(emojis)):
            return True

        return False

    def clean_processed_cache(self):
        """Limpa o cache de usuários processados."""
        self._processed_users.clear()
        logger.info("Cache de usuários processados limpo")
