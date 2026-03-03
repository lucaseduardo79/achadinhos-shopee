"""
Cliente para integração com a API do Instagram (Meta Graph API).
"""
import os
import logging
from typing import List, Dict, Any
import requests
from datetime import datetime

logger = logging.getLogger(__name__)


class InstagramClient:
    """
    Cliente para interagir com a Meta Graph API (Instagram).

    Documentação: https://developers.facebook.com/docs/instagram-api
    """

    def __init__(self):
        self.access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        self.instagram_account_id = os.getenv("INSTAGRAM_ACCOUNT_ID")
        self.api_version = os.getenv("INSTAGRAM_API_VERSION", "v18.0")
        self.base_url = f"https://graph.facebook.com/{self.api_version}"

        if not all([self.access_token, self.instagram_account_id]):
            logger.warning("Credenciais do Instagram não configuradas completamente")

    def _get_params(self) -> Dict[str, str]:
        """Retorna parâmetros base para requisições."""
        return {"access_token": self.access_token}

    def publish_post(self, image_url: str, caption: str) -> str:
        """
        Publica um post no Instagram.

        Args:
            image_url: URL da imagem (deve ser acessível publicamente)
            caption: Legenda do post

        Returns:
            ID do post publicado

        Referência: https://developers.facebook.com/docs/instagram-api/guides/content-publishing
        """
        logger.info("Publicando post no Instagram...")

        try:
            # Passo 1: Criar container de mídia
            create_endpoint = f"{self.base_url}/{self.instagram_account_id}/media"
            create_params = {
                **self._get_params(),
                "image_url": image_url,
                "caption": caption
            }

            create_response = requests.post(create_endpoint, params=create_params)
            create_response.raise_for_status()
            container_id = create_response.json().get("id")

            logger.info(f"Container criado: {container_id}")

            # Passo 2: Publicar o container
            publish_endpoint = f"{self.base_url}/{self.instagram_account_id}/media_publish"
            publish_params = {
                **self._get_params(),
                "creation_id": container_id
            }

            publish_response = requests.post(publish_endpoint, params=publish_params)
            publish_response.raise_for_status()
            post_id = publish_response.json().get("id")

            logger.info(f"Post publicado com sucesso: {post_id}")
            return post_id

        except requests.RequestException as e:
            logger.error(f"Erro ao publicar post: {str(e)}")
            raise

    def get_post_comments(self, post_id: str) -> List[Dict[str, Any]]:
        """
        Busca comentários de um post.

        Args:
            post_id: ID do post

        Returns:
            Lista de comentários
        """
        logger.info(f"Buscando comentários do post {post_id}...")

        try:
            endpoint = f"{self.base_url}/{post_id}/comments"
            params = {
                **self._get_params(),
                "fields": "id,username,text,timestamp,from"
            }

            response = requests.get(endpoint, params=params)
            response.raise_for_status()

            comments_data = response.json().get("data", [])

            # Formata os comentários para o formato esperado
            comments = [
                {
                    "comment_id": comment["id"],
                    "user_id": comment.get("from", {}).get("id", "unknown"),
                    "username": comment.get("username", "unknown"),
                    "text": comment.get("text", ""),
                    "timestamp": datetime.fromisoformat(comment["timestamp"].replace("Z", "+00:00")),
                    "processed": False
                }
                for comment in comments_data
            ]

            logger.info(f"{len(comments)} comentários encontrados")
            return comments

        except requests.RequestException as e:
            logger.error(f"Erro ao buscar comentários: {str(e)}")
            raise

    def reply_to_comment(self, comment_id: str, message: str) -> str:
        """
        Responde a um comentário publicamente.

        Args:
            comment_id: ID do comentário
            message: Mensagem de resposta

        Returns:
            ID da resposta
        """
        logger.info(f"Respondendo ao comentário {comment_id}...")

        try:
            endpoint = f"{self.base_url}/{comment_id}/replies"
            params = {
                **self._get_params(),
                "message": message
            }

            response = requests.post(endpoint, params=params)
            response.raise_for_status()

            reply_id = response.json().get("id")
            logger.info(f"Resposta enviada: {reply_id}")
            return reply_id

        except requests.RequestException as e:
            logger.error(f"Erro ao responder comentário: {str(e)}")
            raise

    def send_dm(self, user_id: str, message: str) -> str:
        """
        Envia mensagem direta (DM) para um usuário.

        Args:
            user_id: ID do usuário (Instagram Scoped ID)
            message: Mensagem a enviar

        Returns:
            ID da mensagem enviada

        NOTA: Envio de DMs requer permissões especiais e aprovação do Instagram.
        Referência: https://developers.facebook.com/docs/messenger-platform/instagram/features/send-message
        """
        logger.info(f"Enviando DM para usuário {user_id}...")

        try:
            # IMPORTANTE: Esta implementação requer Instagram Messaging API
            # e permissões específicas aprovadas pela Meta

            endpoint = f"{self.base_url}/me/messages"
            payload = {
                "recipient": {"id": user_id},
                "message": {"text": message}
            }
            params = self._get_params()

            response = requests.post(endpoint, params=params, json=payload)
            response.raise_for_status()

            message_id = response.json().get("message_id")
            logger.info(f"DM enviada: {message_id}")
            return message_id

        except requests.RequestException as e:
            logger.error(f"Erro ao enviar DM: {str(e)}")
            logger.warning(
                "ATENÇÃO: Envio de DMs via API requer aprovação da Meta. "
                "Verifique se você tem as permissões necessárias."
            )
            raise

    def get_account_info(self) -> Dict[str, Any]:
        """
        Busca informações da conta Instagram.

        Returns:
            Dados da conta
        """
        logger.info("Buscando informações da conta...")

        try:
            endpoint = f"{self.base_url}/{self.instagram_account_id}"
            params = {
                **self._get_params(),
                "fields": "id,username,followers_count,follows_count,media_count"
            }

            response = requests.get(endpoint, params=params)
            response.raise_for_status()

            return response.json()

        except requests.RequestException as e:
            logger.error(f"Erro ao buscar informações da conta: {str(e)}")
            raise
