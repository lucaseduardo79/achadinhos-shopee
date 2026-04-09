"""
Ponto de entrada principal da aplicação.
"""
import os
import time
import logging
from dotenv import load_dotenv
from app.utils.logger import setup_logging
from app.graph.graph import run_workflow, run_monitor_workflow
from app.graph.state import create_initial_state, GraphState
from app.services.state_store import load_last_post, load_recent_posts

logger = logging.getLogger(__name__)


def main():
    """
    Função principal que inicia o sistema.
    """
    # Carrega variáveis de ambiente
    load_dotenv()

    # Configura logging
    log_level = os.getenv("LOG_LEVEL", "INFO")
    setup_logging(level=log_level)

    logger.info("=" * 60)
    logger.info("Iniciando Sistema de Automação Shopee + Instagram")
    logger.info("=" * 60)

    # Modo de operação
    mode = os.getenv("OPERATION_MODE", "once")  # once, loop, scheduled

    if mode == "once":
        # Executa uma vez e finaliza
        logger.info("Modo: Execução única")
        run_single_execution()

    elif mode == "loop":
        # Loop contínuo com intervalo
        logger.info("Modo: Loop contínuo")
        interval = int(os.getenv("LOOP_INTERVAL_SECONDS", "3600"))
        run_continuous_loop(interval)

    elif mode == "monitor":
        # Monitora comentários uma única vez
        logger.info("Modo: Monitoramento único")
        run_monitor_execution()

    elif mode == "monitor_loop":
        # Monitora comentários continuamente em intervalo curto
        logger.info("Modo: Monitoramento contínuo")
        interval = int(os.getenv("MONITOR_INTERVAL_SECONDS", "300"))
        run_monitor_loop(interval)

    elif mode == "scheduled":
        # Execução agendada (requer biblioteca de scheduling)
        logger.info("Modo: Agendado")
        logger.warning("Modo 'scheduled' ainda não implementado. Use 'loop' ou 'once'.")
        run_single_execution()

    else:
        logger.error(f"Modo desconhecido: {mode}")
        logger.info("Modos válidos: once, loop, scheduled")


def run_single_execution():
    """Executa o workflow uma única vez."""
    try:
        initial_state = create_initial_state()
        final_state = run_workflow(initial_state)

        # Verifica resultado
        if final_state.get("error"):
            logger.error(f"Execução finalizada com erro: {final_state['error']}")
            exit(1)
        else:
            logger.info("Execução finalizada com sucesso!")
            logger.info(f"Status final: {final_state.get('step')}")

    except Exception as e:
        logger.exception(f"Erro fatal durante execução: {str(e)}")
        exit(1)


def run_monitor_execution():
    """Monitora comentários do último post publicado sem publicar um novo."""
    last = load_last_post()
    if not last:
        logger.error("Nenhum post salvo encontrado. Execute no modo 'once' primeiro.")
        exit(1)

    post_id = last["post_id"]
    offer = last["offer"]
    logger.info(f"Monitorando post {post_id} — {offer.get('name', '')}")

    from datetime import datetime
    initial_state = create_initial_state()
    initial_state["current_offer"] = offer
    initial_state["post_content"] = {
        "post_id": post_id,
        "image_url": offer.get("image_url", ""),
        "caption": "",
        "published_at": last.get("published_at"),
        "product_link": offer.get("affiliate_link") or offer.get("product_url", ""),
    }
    initial_state["step"] = "post_published"

    final_state = run_monitor_workflow(initial_state)

    if final_state.get("error"):
        logger.error(f"Monitoramento finalizado com erro: {final_state['error']}")
    else:
        logger.info("Monitoramento finalizado com sucesso!")


def run_monitor_loop(interval_seconds: int):
    """
    Monitora comentários de todos os posts recentes em loop contínuo.

    Args:
        interval_seconds: Intervalo entre verificações (padrão: 300s = 5min)
    """
    logger.info(f"Monitoramento contínuo a cada {interval_seconds}s")

    while True:
        recent_posts = load_recent_posts(days=7)
        if not recent_posts:
            logger.info("Nenhum post publicado ainda. Aguardando...")
            time.sleep(interval_seconds)
            continue

        for post in recent_posts:
            try:
                post_id = post["post_id"]
                offer = post["offer"]
                logger.info(f"Verificando comentários: post {post_id}")

                initial_state = create_initial_state()
                initial_state["current_offer"] = offer
                initial_state["post_content"] = {
                    "post_id": post_id,
                    "image_url": offer.get("image_url", ""),
                    "caption": "",
                    "published_at": post.get("published_at"),
                    "product_link": offer.get("affiliate_link") or offer.get("product_url", ""),
                }
                initial_state["step"] = "post_published"

                run_monitor_workflow(initial_state)

            except Exception as e:
                logger.exception(f"Erro ao monitorar post {post.get('post_id')}: {e}")

        time.sleep(interval_seconds)


def run_continuous_loop(interval_seconds: int):
    """
    Executa o workflow em loop contínuo, respeitando o intervalo desde a última publicação.

    Args:
        interval_seconds: Intervalo mínimo entre publicações em segundos
    """
    logger.info(f"Iniciando loop com intervalo de {interval_seconds}s entre publicações")

    iteration = 0

    while True:
        # Verifica se já passou tempo suficiente desde a última publicação
        last = load_last_post()
        if last:
            from datetime import datetime
            last_published = datetime.fromisoformat(last["published_at"])
            elapsed = (datetime.now() - last_published).total_seconds()
            remaining = interval_seconds - elapsed

            if remaining > 0:
                logger.info(
                    f"Última publicação há {int(elapsed/3600)}h{int((elapsed%3600)/60)}m. "
                    f"Próxima em {int(remaining/3600)}h{int((remaining%3600)/60)}m."
                )
                time.sleep(min(remaining, 3600))  # Acorda no máximo a cada 1h para checar
                continue

        iteration += 1
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Publicação #{iteration}")
        logger.info(f"{'=' * 60}\n")

        try:
            initial_state = create_initial_state()
            final_state = run_workflow(initial_state)

            if final_state.get("error"):
                logger.error(f"Publicação #{iteration} finalizada com erro")
            else:
                logger.info(f"Publicação #{iteration} finalizada com sucesso")

        except Exception as e:
            logger.exception(f"Erro na publicação #{iteration}: {str(e)}")

        logger.info(f"Aguardando {interval_seconds}s até próxima publicação...")
        time.sleep(interval_seconds)


if __name__ == "__main__":
    main()
