"""
Cliente para integração com a API do Instagram (Meta Graph API).
"""
import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Any
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

ENV_FILE = Path(__file__).parent.parent.parent.parent / ".env"

# Subcódigos de token expirado/inválido da Meta Graph API
_TOKEN_EXPIRED_SUBCODES = {463, 467}


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

    def _is_token_expired(self, response: requests.Response) -> bool:
        """Verifica se a resposta indica token expirado ou inválido."""
        try:
            body = response.json()
            error = body.get("error", {})
            code = error.get("code")
            subcode = error.get("error_subcode")
            return code == 190 and subcode in _TOKEN_EXPIRED_SUBCODES
        except Exception:
            return False

    def _refresh_token(self) -> bool:
        """
        Renova o token de longa duração via fb_exchange_token.
        Atualiza self.access_token e o arquivo .env.

        Returns:
            True se renovado com sucesso, False caso contrário.
        """
        app_id = os.getenv("META_EXCHANGE_APP_ID")
        app_secret = os.getenv("META_EXCHANGE_APP_SECRET")

        if not all([app_id, app_secret]):
            logger.error(
                "META_EXCHANGE_APP_ID e META_EXCHANGE_APP_SECRET não configurados. "
                "Não é possível renovar o token automaticamente."
            )
            return False

        logger.info("Token expirado. Tentando renovação automática...")

        try:
            resp = requests.get(
                f"https://graph.facebook.com/{self.api_version}/oauth/access_token",
                params={
                    "grant_type": "fb_exchange_token",
                    "client_id": app_id,
                    "client_secret": app_secret,
                    "fb_exchange_token": self.access_token,
                },
                timeout=15,
            )
            data = resp.json()

            if "error" in data:
                logger.error(f"Falha ao renovar token: {data['error']['message']}")
                return False

            new_token = data["access_token"]
            expires_days = data.get("expires_in", 0) // 86400

            self.access_token = new_token
            self._update_env_token(new_token)

            logger.info(f"Token renovado com sucesso. Expira em ~{expires_days} dias.")
            return True

        except Exception as e:
            logger.error(f"Erro inesperado ao renovar token: {e}")
            return False

    def _update_env_token(self, new_token: str):
        """Atualiza INSTAGRAM_ACCESS_TOKEN no arquivo .env."""
        try:
            content = ENV_FILE.read_text(encoding="utf-8")
            updated = re.sub(
                r"^(INSTAGRAM_ACCESS_TOKEN=).*$",
                rf"\g<1>{new_token}",
                content,
                flags=re.MULTILINE,
            )
            ENV_FILE.write_text(updated, encoding="utf-8")
        except Exception as e:
            logger.warning(f"Não foi possível atualizar o .env: {e}")

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Executa uma requisição HTTP com detecção e renovação automática de token expirado.
        Retenta a requisição uma vez após renovação bem-sucedida.
        """
        resp = getattr(requests, method)(url, **kwargs)

        if self._is_token_expired(resp):
            if self._refresh_token():
                # Atualiza o token nos kwargs e retenta
                if "params" in kwargs and "access_token" in kwargs["params"]:
                    kwargs["params"]["access_token"] = self.access_token
                if "data" in kwargs and "access_token" in kwargs["data"]:
                    kwargs["data"]["access_token"] = self.access_token
                resp = getattr(requests, method)(url, **kwargs)
            else:
                logger.error("Renovação do token falhou. Verifique as credenciais.")

        return resp

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
            create_data = {
                **self._get_params(),
                "image_url": image_url,
                "caption": caption
            }

            create_response = self._request("post", create_endpoint, data=create_data)
            create_response.raise_for_status()
            container_id = create_response.json().get("id")

            logger.info(f"Container criado: {container_id}")

            # Passo 2: Publicar o container
            publish_endpoint = f"{self.base_url}/{self.instagram_account_id}/media_publish"
            publish_data = {
                **self._get_params(),
                "creation_id": container_id
            }

            publish_response = self._request("post", publish_endpoint, data=publish_data)
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

            response = self._request("get", endpoint, params=params)

            # Post inaccessível (publicado com outro token/app) — ignora sem crash
            if response.status_code == 400:
                body = response.json()
                msg = body.get("error", {}).get("message", "")
                logger.warning(f"Post {post_id} inacessível (400): {msg}. Ignorando.")
                return []

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
            reply_data = {
                **self._get_params(),
                "message": message
            }

            response = self._request("post", endpoint, data=reply_data)
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

            endpoint = f"https://graph.instagram.com/{self.api_version}/me/messages"
            payload = {
                "recipient": {"id": user_id},
                "message": {"text": message},
            }
            headers = {"Authorization": f"Bearer {self.access_token}"}

            response = self._request("post", endpoint, json=payload, headers=headers)
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

            response = self._request("get", endpoint, params=params)
            response.raise_for_status()

            return response.json()

        except requests.RequestException as e:
            logger.error(f"Erro ao buscar informações da conta: {str(e)}")
            raise
