"""
Ponto de entrada principal da aplicação.
"""
import os
import time
import logging
from dotenv import load_dotenv
from app.utils.logger import setup_logging
from app.graph.graph import run_workflow
from app.graph.state import create_initial_state

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


def run_continuous_loop(interval_seconds: int):
    """
    Executa o workflow em loop contínuo.

    Args:
        interval_seconds: Intervalo entre execuções em segundos
    """
    logger.info(f"Iniciando loop com intervalo de {interval_seconds}s")

    iteration = 0

    while True:
        iteration += 1
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Iteração #{iteration}")
        logger.info(f"{'=' * 60}\n")

        try:
            initial_state = create_initial_state()
            final_state = run_workflow(initial_state)

            if final_state.get("error"):
                logger.error(f"Execução #{iteration} finalizada com erro")
            else:
                logger.info(f"Execução #{iteration} finalizada com sucesso")

        except Exception as e:
            logger.exception(f"Erro na iteração #{iteration}: {str(e)}")

        # Aguarda próximo ciclo
        logger.info(f"\nAguardando {interval_seconds}s até próxima execução...")
        time.sleep(interval_seconds)


if __name__ == "__main__":
    main()
