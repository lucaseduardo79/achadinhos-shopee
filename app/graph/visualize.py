"""
Script para visualizar o grafo LangGraph.

Este script pode ser usado para gerar uma visualização do grafo em formato Mermaid
ou para imprimir a estrutura do grafo no console.
"""
from app.graph.graph import build_graph


def print_graph_structure():
    """
    Imprime a estrutura do grafo no console.
    """
    print("=" * 60)
    print("ESTRUTURA DO GRAFO LANGGRAPH")
    print("=" * 60)
    print()

    print("NÓS DO GRAFO:")
    print("-" * 60)
    nodes = [
        ("fetch_offers", "Buscar Ofertas da Shopee"),
        ("select_offers", "Selecionar Melhores Ofertas"),
        ("generate_content", "Gerar Conteúdo para Instagram"),
        ("publish_post", "Publicar Post no Instagram"),
        ("monitor_comments", "Monitorar Comentários"),
        ("evaluate_comment", "Avaliar Comentário"),
        ("enviar_dm", "Enviar DM com Link"),
        ("responder_comentario", "Responder Comentário Público"),
        ("log_event", "Registrar Evento"),
        ("handle_error", "Tratar Erro"),
    ]

    for node_id, description in nodes:
        print(f"  • {node_id:25} → {description}")

    print()
    print("FLUXO PRINCIPAL:")
    print("-" * 60)
    flow = [
        "START",
        "  ↓",
        "fetch_offers (Buscar Ofertas)",
        "  ↓",
        "select_offers (Selecionar)",
        "  ↓",
        "generate_content (Gerar Conteúdo)",
        "  ↓",
        "publish_post (Publicar)",
        "  ↓",
        "monitor_comments (Monitorar)",
        "  ↓",
        "evaluate_comment (Avaliar)",
        "  ↓",
        "[DECISÃO: Há comentário para processar?]",
        "  ↓ SIM                    ↓ NÃO",
        "enviar_dm              log_event",
        "  ↓",
        "responder_comentario",
        "  ↓",
        "[Volta para evaluate_comment]",
        "  ↓",
        "log_event",
        "  ↓",
        "END"
    ]

    for line in flow:
        print(f"  {line}")

    print()
    print("CONDIÇÕES:")
    print("-" * 60)
    print("  1. should_continue_monitoring:")
    print("     • Comentário para processar → enviar_dm")
    print("     • Sem comentários novos → log_event")
    print("     • Erro → handle_error")
    print()
    print("  2. should_retry:")
    print("     • retry_count < 3 → fetch_offers (recomeça)")
    print("     • retry_count >= 3 → log_event (desiste)")
    print()

    print("=" * 60)


def generate_mermaid_diagram():
    """
    Gera um diagrama Mermaid do grafo.

    O diagrama pode ser copiado e colado em:
    - GitHub Markdown
    - Mermaid Live Editor (https://mermaid.live)
    """
    mermaid = """
```mermaid
graph TD
    START([INÍCIO])
    START --> A[fetch_offers<br/>Buscar Ofertas Shopee]

    A --> B[select_offers<br/>Selecionar Melhores Ofertas]
    B --> C[generate_content<br/>Gerar Conteúdo Instagram]
    C --> D[publish_post<br/>Publicar Post]
    D --> E[monitor_comments<br/>Monitorar Comentários]

    E --> F{evaluate_comment<br/>Avaliar Comentário}

    F -->|Processar| G[enviar_dm<br/>Enviar DM]
    F -->|Sem novos| LOG[log_event<br/>Registrar Evento]

    G --> H[responder_comentario<br/>Responder Público]
    H --> F

    LOG --> END([FIM])

    A -.Erro.-> ERR[handle_error<br/>Tratar Erro]
    B -.Erro.-> ERR
    C -.Erro.-> ERR
    D -.Erro.-> ERR
    E -.Erro.-> ERR
    F -.Erro.-> ERR

    ERR -->|Retry < 3| A
    ERR -->|Retry >= 3| LOG

    style START fill:#90EE90
    style END fill:#FFB6C1
    style ERR fill:#FFD700
    style F fill:#87CEEB
```
    """

    print("=" * 60)
    print("DIAGRAMA MERMAID DO GRAFO")
    print("=" * 60)
    print()
    print("Copie o código abaixo e cole em:")
    print("  • README.md do GitHub")
    print("  • https://mermaid.live para visualizar")
    print()
    print(mermaid)
    print()
    print("=" * 60)


def main():
    """
    Função principal - executa visualizações.
    """
    print_graph_structure()
    print()
    generate_mermaid_diagram()


if __name__ == "__main__":
    main()
