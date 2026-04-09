"""
Nós do grafo relacionados à integração com Instagram.
"""
from typing import Dict, Any
import logging
from app.graph.state import GraphState
from app.integrations.instagram.client import InstagramClient
from app.services.content_generator import ContentGenerator
from app.services.comment_processor import CommentProcessor
from app.services.state_store import save_post, get_offer_for_post, save_processed_comment, is_comment_processed

logger = logging.getLogger(__name__)


def gerar_conteudo_instagram(state: GraphState) -> Dict[str, Any]:
    """
    Gera o conteúdo (caption + imagem) para o post do Instagram.

    Args:
        state: Estado atual do grafo

    Returns:
        Atualização do estado com o conteúdo gerado
    """
    logger.info(f"[{state['execution_id']}] Gerando conteúdo do Instagram...")

    try:
        offer = state.get("current_offer")
        if not offer:
            return {
                "step": "error",
                "error": "Nenhuma oferta selecionada para gerar conteúdo"
            }

        generator = ContentGenerator()
        post_content = generator.create_post_content(offer)

        logger.info(f"[{state['execution_id']}] Conteúdo gerado com sucesso")

        return {
            "post_content": post_content,
            "step": "content_generated",
            "error": None
        }

    except Exception as e:
        logger.error(f"[{state['execution_id']}] Erro ao gerar conteúdo: {str(e)}")
        return {
            "step": "error",
            "error": f"Erro ao gerar conteúdo: {str(e)}"
        }


def publicar_post(state: GraphState) -> Dict[str, Any]:
    """
    Publica o post no Instagram.

    Args:
        state: Estado atual do grafo

    Returns:
        Atualização do estado com o ID do post publicado
    """
    logger.info(f"[{state['execution_id']}] Publicando post no Instagram...")

    try:
        post_content = state.get("post_content")
        if not post_content:
            return {
                "step": "error",
                "error": "Nenhum conteúdo disponível para publicação"
            }

        client = InstagramClient()
        post_id = client.publish_post(
            image_url=post_content["image_url"],
            caption=post_content["caption"]
        )

        post_content["post_id"] = post_id

        logger.info(f"[{state['execution_id']}] Post publicado: {post_id}")

        # Persiste o post e a oferta para monitoramento futuro
        offer = state.get("current_offer")
        if offer:
            save_post(post_id, offer)

        return {
            "post_content": post_content,
            "step": "post_published",
            "error": None
        }

    except Exception as e:
        logger.error(f"[{state['execution_id']}] Erro ao publicar post: {str(e)}")
        return {
            "step": "error",
            "error": f"Erro ao publicar post: {str(e)}"
        }


def monitorar_comentarios(state: GraphState) -> Dict[str, Any]:
    """
    Monitora comentários no post publicado.

    Args:
        state: Estado atual do grafo

    Returns:
        Atualização do estado com a lista de comentários
    """
    logger.info(f"[{state['execution_id']}] Monitorando comentários...")

    try:
        post_content = state.get("post_content")
        if not post_content or not post_content.get("post_id"):
            return {
                "step": "error",
                "error": "Post não encontrado para monitoramento"
            }

        client = InstagramClient()
        comments = client.get_post_comments(post_content["post_id"])

        logger.info(f"[{state['execution_id']}] {len(comments)} comentário(s) encontrado(s)")

        return {
            "comments": comments,
            "step": "comments_monitored",
            "error": None
        }

    except Exception as e:
        logger.error(f"[{state['execution_id']}] Erro ao monitorar comentários: {str(e)}")
        return {
            "step": "error",
            "error": f"Erro ao monitorar comentários: {str(e)}"
        }


def avaliar_comentario(state: GraphState) -> Dict[str, Any]:
    """
    Avalia se um comentário deve ser processado (não foi processado antes).

    Args:
        state: Estado atual do grafo

    Returns:
        Atualização do estado com o comentário atual
    """
    logger.info(f"[{state['execution_id']}] Avaliando comentários...")

    try:
        comments = state.get("comments", [])
        processor = CommentProcessor()

        # Encontra o próximo comentário não processado
        for comment in comments:
            if is_comment_processed(comment["comment_id"]):
                continue
            if not comment.get("processed", False):
                should_process = processor.should_process_comment(comment)

                if should_process:
                    logger.info(f"[{state['execution_id']}] Comentário {comment['comment_id']} será processado")
                    return {
                        "current_comment": comment,
                        "step": "comment_evaluated",
                        "error": None
                    }

        logger.info(f"[{state['execution_id']}] Nenhum comentário novo para processar")
        return {
            "current_comment": None,
            "step": "no_comments_to_process",
            "error": None
        }

    except Exception as e:
        logger.error(f"[{state['execution_id']}] Erro ao avaliar comentários: {str(e)}")
        return {
            "step": "error",
            "error": f"Erro ao avaliar comentários: {str(e)}"
        }


def enviar_dm_com_link(state: GraphState) -> Dict[str, Any]:
    """
    Envia DM ao usuário com o link do produto e mensagem amigável.

    Args:
        state: Estado atual do grafo

    Returns:
        Atualização do estado indicando sucesso do envio
    """
    logger.info(f"[{state['execution_id']}] Enviando DM com link...")

    try:
        comment = state.get("current_comment")
        offer = state.get("current_offer")

        if not comment or not offer:
            return {
                "step": "error",
                "error": "Comentário ou oferta não disponível para envio de DM"
            }

        client = InstagramClient()

        # Se a oferta em memória não tem link, tenta carregar do estado persistido
        post_id = (state.get("post_content") or {}).get("post_id")
        if post_id and not (offer.get("affiliate_link") or offer.get("product_url")):
            stored_offer = get_offer_for_post(post_id)
            if stored_offer:
                offer = stored_offer

        link = offer.get("affiliate_link") or offer.get("product_url", "")
        message = (
            f"Oi! 👋 Vi seu comentário e já te mandei o link do produto com desconto.\n\n"
            f"🔗 Link: {link}\n\n"
            f"Qualquer dúvida é só me chamar!"
        )

        client.send_dm(
            user_id=comment["user_id"],
            message=message
        )

        logger.info(f"[{state['execution_id']}] DM enviado para {comment['username']}")

        return {
            "step": "dm_sent",
            "error": None
        }

    except Exception as e:
        logger.warning(f"[{state['execution_id']}] DM não enviada ({str(e)}). Seguindo para resposta pública.")
        return {
            "step": "dm_skipped",
            "error": None
        }


def responder_comentario_publico(state: GraphState) -> Dict[str, Any]:
    """
    Responde publicamente ao comentário avisando que o link foi enviado por DM.

    Args:
        state: Estado atual do grafo

    Returns:
        Atualização do estado indicando sucesso da resposta
    """
    logger.info(f"[{state['execution_id']}] Respondendo comentário publicamente...")

    try:
        comment = state.get("current_comment")

        if not comment:
            return {
                "step": "error",
                "error": "Comentário não disponível para resposta pública"
            }

        client = InstagramClient()
        reply_text = "Te enviamos o link do produto por DM 😉"

        client.reply_to_comment(
            comment_id=comment["comment_id"],
            message=reply_text
        )

        # Marca o comentário como processado (em memória e persistido)
        comment["processed"] = True
        save_processed_comment(comment["comment_id"])

        logger.info(f"[{state['execution_id']}] Comentário respondido: {comment['comment_id']}")

        return {
            "current_comment": comment,
            "step": "comment_replied",
            "error": None
        }

    except Exception as e:
        logger.error(f"[{state['execution_id']}] Erro ao responder comentário: {str(e)}")
        return {
            "step": "error",
            "error": f"Erro ao responder comentário: {str(e)}"
        }
