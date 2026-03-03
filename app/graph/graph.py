"""
Define e constrói o grafo LangGraph que orquestra todo o fluxo.
"""
from langgraph.graph import StateGraph, END
from app.graph.state import GraphState, create_initial_state
from app.graph.nodes.shopee_nodes import (
    buscar_ofertas_shopee,
    selecionar_ofertas_do_dia
)
from app.graph.nodes.instagram_nodes import (
    gerar_conteudo_instagram,
    publicar_post,
    monitorar_comentarios,
    avaliar_comentario,
    enviar_dm_com_link,
    responder_comentario_publico
)
from app.graph.nodes.observability_nodes import logar_evento, handle_error
import logging

logger = logging.getLogger(__name__)


def should_continue_monitoring(state: GraphState) -> str:
    """
    Decide se deve continuar monitorando comentários ou finalizar.

    Args:
        state: Estado atual do grafo

    Returns:
        Nome do próximo nó ou END
    """
    step = state.get("step")

    # Se há comentários para processar, continua
    if step == "comment_evaluated" and state.get("current_comment"):
        return "enviar_dm"

    # Se não há mais comentários, pode finalizar ou aguardar
    if step == "no_comments_to_process":
        return "end"

    # Se houve erro, vai para tratamento
    if step == "error":
        return "handle_error"

    # Continua o fluxo normal
    return "monitor_comments"


def should_retry(state: GraphState) -> str:
    """
    Decide se deve tentar novamente após erro ou finalizar.

    Args:
        state: Estado atual do grafo

    Returns:
        Nome do próximo nó ou END
    """
    step = state.get("step")

    if step == "retry":
        return "fetch_offers"  # Recomeça do início
    elif step == "failed":
        return "end"
    else:
        return "log_event"


def build_graph() -> StateGraph:
    """
    Constrói o grafo LangGraph completo.

    Returns:
        Grafo compilado e pronto para execução
    """
    logger.info("Construindo grafo LangGraph...")

    # Cria o grafo com o tipo de estado
    workflow = StateGraph(GraphState)

    # === FASE 1: Curadoria de Ofertas ===
    workflow.add_node("fetch_offers", buscar_ofertas_shopee)
    workflow.add_node("select_offers", selecionar_ofertas_do_dia)

    # === FASE 2: Publicação no Instagram ===
    workflow.add_node("generate_content", gerar_conteudo_instagram)
    workflow.add_node("publish_post", publicar_post)

    # === FASE 3: Monitoramento e Interação ===
    workflow.add_node("monitor_comments", monitorar_comentarios)
    workflow.add_node("evaluate_comment", avaliar_comentario)
    workflow.add_node("enviar_dm", enviar_dm_com_link)
    workflow.add_node("responder_comentario", responder_comentario_publico)

    # === FASE 4: Observabilidade ===
    workflow.add_node("log_event", logar_evento)
    workflow.add_node("handle_error", handle_error)

    # === DEFINIÇÃO DO FLUXO ===

    # Ponto de entrada
    workflow.set_entry_point("fetch_offers")

    # Fluxo principal: Shopee → Instagram → Monitoramento
    workflow.add_edge("fetch_offers", "select_offers")
    workflow.add_edge("select_offers", "generate_content")
    workflow.add_edge("generate_content", "publish_post")
    workflow.add_edge("publish_post", "monitor_comments")

    # Fluxo de monitoramento de comentários
    workflow.add_edge("monitor_comments", "evaluate_comment")

    # Decisão condicional: processar comentário ou finalizar
    workflow.add_conditional_edges(
        "evaluate_comment",
        should_continue_monitoring,
        {
            "enviar_dm": "enviar_dm",
            "end": "log_event",
            "handle_error": "handle_error",
            "monitor_comments": "monitor_comments"
        }
    )

    # Fluxo de processamento de comentário
    workflow.add_edge("enviar_dm", "responder_comentario")

    # Após responder, volta a avaliar próximo comentário
    workflow.add_edge("responder_comentario", "evaluate_comment")

    # Fluxo de erro e retry
    workflow.add_conditional_edges(
        "handle_error",
        should_retry,
        {
            "fetch_offers": "fetch_offers",
            "end": "log_event",
            "log_event": "log_event"
        }
    )

    # Logging antes de finalizar
    workflow.add_edge("log_event", END)

    # Compila o grafo
    app = workflow.compile()

    logger.info("Grafo construído com sucesso")
    return app


def run_workflow(initial_state: GraphState = None):
    """
    Executa o workflow completo.

    Args:
        initial_state: Estado inicial (opcional, cria um novo se não fornecido)

    Returns:
        Estado final após execução
    """
    if initial_state is None:
        initial_state = create_initial_state()

    logger.info(f"Iniciando workflow {initial_state['execution_id']}")

    app = build_graph()
    final_state = app.invoke(initial_state)

    logger.info(f"Workflow {initial_state['execution_id']} finalizado")
    logger.info(f"Status final: {final_state.get('step')}")

    return final_state
