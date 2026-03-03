"""
Define o estado compartilhado entre os nós do grafo LangGraph.
"""
from typing import TypedDict, List, Optional, Dict, Any
from datetime import datetime


class ProductOffer(TypedDict):
    """Representa uma oferta de produto da Shopee."""
    product_id: str
    name: str
    price: float
    original_price: Optional[float]
    discount_percentage: Optional[float]
    rating: Optional[float]
    image_url: str
    product_url: str
    affiliate_link: Optional[str]
    commission: Optional[float]
    category: Optional[str]
    sales: Optional[int]
    shop_name: Optional[str]
    shop_type: Optional[str]
    commission_value: Optional[float]


class InstagramPost(TypedDict):
    """Representa um post do Instagram."""
    post_id: Optional[str]
    image_url: str
    caption: str
    published_at: Optional[datetime]
    product_link: str


class Comment(TypedDict):
    """Representa um comentário no Instagram."""
    comment_id: str
    user_id: str
    username: str
    text: str
    timestamp: datetime
    processed: bool


class GraphState(TypedDict):
    """
    Estado global do grafo LangGraph.

    Este estado é passado entre todos os nós e contém toda
    a informação necessária para orquestrar o fluxo completo.
    """
    # Ofertas da Shopee
    raw_offers: Optional[List[Dict[str, Any]]]
    selected_offers: Optional[List[ProductOffer]]
    current_offer: Optional[ProductOffer]

    # Conteúdo do Instagram
    post_content: Optional[InstagramPost]

    # Comentários e interações
    comments: Optional[List[Comment]]
    current_comment: Optional[Comment]

    # Status e controle de fluxo
    step: str  # etapa atual do processo
    error: Optional[str]
    retry_count: int

    # Metadados
    execution_id: str
    started_at: datetime
    metadata: Optional[Dict[str, Any]]


def create_initial_state() -> GraphState:
    """Cria o estado inicial do grafo."""
    return GraphState(
        raw_offers=None,
        selected_offers=None,
        current_offer=None,
        post_content=None,
        comments=None,
        current_comment=None,
        step="init",
        error=None,
        retry_count=0,
        execution_id=f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        started_at=datetime.now(),
        metadata={}
    )
