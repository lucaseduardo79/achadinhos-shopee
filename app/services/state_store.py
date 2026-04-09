"""
Persistência de estado entre execuções.

Salva posts publicados e suas ofertas em data/posts.json para que
o monitoramento de comentários funcione mesmo após reinicializações.
"""
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Set

logger = logging.getLogger(__name__)

STATE_FILE = Path(__file__).parent.parent.parent / "data" / "posts.json"


def save_post(post_id: str, offer: Dict[str, Any]):
    """
    Salva post publicado com os dados da oferta.

    Args:
        post_id: ID do post no Instagram
        offer: Oferta publicada (com affiliate_link ou product_url)
    """
    posts = _load_all()

    entry = {
        "post_id": post_id,
        "published_at": datetime.now().isoformat(),
        "offer": {
            "product_id": offer.get("product_id"),
            "name": offer.get("name"),
            "price": offer.get("price"),
            "original_price": offer.get("original_price"),
            "discount_percentage": offer.get("discount_percentage"),
            "affiliate_link": offer.get("affiliate_link"),
            "product_url": offer.get("product_url"),
            "image_url": offer.get("image_url"),
        }
    }

    posts.append(entry)

    STATE_FILE.parent.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(posts, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"Estado salvo: post {post_id}")


def load_last_post() -> Optional[Dict[str, Any]]:
    """
    Retorna o último post publicado com seus dados de oferta.

    Returns:
        Dict com post_id e offer, ou None se não houver posts salvos.
    """
    posts = _load_all()
    if not posts:
        return None
    return posts[-1]


def get_offer_for_post(post_id: str) -> Optional[Dict[str, Any]]:
    """
    Retorna a oferta associada a um post específico.

    Args:
        post_id: ID do post

    Returns:
        Dados da oferta ou None
    """
    posts = _load_all()
    for post in reversed(posts):
        if post.get("post_id") == post_id:
            return post.get("offer")
    return None


def load_recent_posts(days: int = 7) -> list:
    """
    Retorna todos os posts publicados nos últimos N dias.
    """
    posts = _load_all()
    cutoff = datetime.now() - timedelta(days=days)
    recent = []
    for post in posts:
        try:
            if datetime.fromisoformat(post["published_at"]) >= cutoff:
                recent.append(post)
        except Exception:
            pass
    return recent


def get_recently_published_ids(days: int = 7) -> Set[str]:
    """
    Retorna os product_ids publicados nos últimos N dias.

    Args:
        days: Janela de deduplicação em dias

    Returns:
        Set de product_ids recentemente publicados
    """
    posts = _load_all()
    cutoff = datetime.now() - timedelta(days=days)
    ids = set()
    for post in posts:
        try:
            published_at = datetime.fromisoformat(post["published_at"])
            if published_at >= cutoff:
                product_id = post.get("offer", {}).get("product_id")
                if product_id:
                    ids.add(str(product_id))
        except Exception:
            pass
    return ids


def save_processed_comment(comment_id: str):
    """Registra um comentário como já respondido."""
    data = _load_meta()
    processed = data.get("processed_comments", [])
    if comment_id not in processed:
        processed.append(comment_id)
    data["processed_comments"] = processed
    _save_meta(data)


def is_comment_processed(comment_id: str) -> bool:
    """Verifica se um comentário já foi respondido."""
    data = _load_meta()
    return comment_id in data.get("processed_comments", [])


def _load_meta() -> dict:
    meta_file = STATE_FILE.parent / "meta.json"
    if not meta_file.exists():
        return {}
    try:
        return json.loads(meta_file.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_meta(data: dict):
    meta_file = STATE_FILE.parent / "meta.json"
    meta_file.parent.mkdir(exist_ok=True)
    meta_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _load_all() -> list:
    if not STATE_FILE.exists():
        return []
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning(f"Erro ao carregar state file: {e}")
        return []
