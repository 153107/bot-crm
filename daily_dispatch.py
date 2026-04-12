#!/usr/bin/env python3
"""
Growth Ops Copilot — Daily Intelligence Dispatcher
Script standalone pra enviar Daily Intelligence via GitHub Actions/Lambda/cron.
Não usa Socket Mode — apenas HTTP API do Slack.

Uso:
  python daily_dispatch.py                    # Envia pra Banking (default)
  python daily_dispatch.py --area Banking     # Envia pra Banking
  python daily_dispatch.py --area all         # Envia pra todas as áreas com Daily
  python daily_dispatch.py --dry-run          # Só gera o relatório, não envia

Variáveis de ambiente:
  SLACK_BOT_TOKEN         Token do bot Slack (xoxb-...)
  MONDAY_API_TOKEN        Token da API Monday.com
  MONDAY_BOARD_ID         ID do board de campanhas
  DATABRICKS_HOST         Host do Databricks (https://xxx.cloud.databricks.com)
  DATABRICKS_TOKEN        PAT do Databricks (dapi...) — usado em CI
  DATABRICKS_WAREHOUSE_ID ID do SQL Warehouse
"""
import os
import sys
import argparse
import logging
from datetime import datetime

# Configura logging antes de importar módulos do projeto
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("daily-dispatch")

# Carrega .env se existir (pra dev local)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # Em CI, usa env vars direto


def check_env_vars():
    """Verifica variáveis de ambiente obrigatórias."""
    required = ["SLACK_BOT_TOKEN", "MONDAY_API_TOKEN", "MONDAY_BOARD_ID"]
    missing = [v for v in required if not os.environ.get(v)]
    
    # Databricks: precisa de PAT OU OAuth configurado
    has_databricks = (
        os.environ.get("DATABRICKS_TOKEN") or 
        os.environ.get("DATABRICKS_HOST")  # OAuth usa host + profile
    )
    if not has_databricks:
        missing.append("DATABRICKS_TOKEN ou DATABRICKS_HOST")
    
    if missing:
        logger.error(f"Variáveis faltando: {', '.join(missing)}")
        sys.exit(1)


def get_channel_id(slack_client, channel_name: str) -> str | None:
    """Busca channel ID pelo nome (suporta público e privado)."""
    for channel_type in ["public_channel", "private_channel"]:
        try:
            result = slack_client.conversations_list(types=channel_type, limit=1000)
            for ch in result.get("channels", []):
                if ch["name"] == channel_name:
                    return ch["id"]
        except Exception as e:
            logger.warning(f"Erro listando {channel_type}: {e}")
    return None


def send_daily(area: str, dry_run: bool = False) -> bool:
    """Gera e envia Daily Intelligence pra uma área."""
    from slack_sdk import WebClient
    from daily import generate_daily_banking
    from config import SLACK_CHANNELS, AREAS_DAILY
    
    if area not in AREAS_DAILY:
        logger.warning(f"Área '{area}' não tem Daily automático configurado")
        return False
    
    # Só Banking implementado por enquanto
    if area != "Banking":
        logger.info(f"Daily de {area} ainda não implementado — pulando")
        return True
    
    channel_name = SLACK_CHANNELS.get(area)
    if not channel_name:
        logger.error(f"Canal Slack não configurado pra {area}")
        return False
    
    logger.info(f"Gerando Daily Intelligence — {area}...")
    
    try:
        blocks = generate_daily_banking()
        logger.info(f"Relatório gerado: {len(blocks)} blocos")
    except Exception as e:
        logger.error(f"Erro gerando relatório: {e}", exc_info=True)
        return False
    
    if dry_run:
        logger.info("[DRY RUN] Relatório gerado mas não enviado")
        # Mostra preview dos títulos
        for b in blocks:
            if b.get("type") == "section" and b.get("text", {}).get("type") == "mrkdwn":
                text = b["text"]["text"][:100]
                if text.startswith("*"):
                    logger.info(f"  {text[:80]}...")
        return True
    
    # Envia pro Slack
    client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
    
    channel_id = get_channel_id(client, channel_name)
    if not channel_id:
        logger.error(f"Canal #{channel_name} não encontrado")
        return False
    
    try:
        result = client.chat_postMessage(channel=channel_id, blocks=blocks)
        if result["ok"]:
            logger.info(f"✅ Daily enviado pra #{channel_name} ({area})")
            return True
        else:
            logger.error(f"Falha ao enviar: {result.get('error')}")
            return False
    except Exception as e:
        logger.error(f"Erro enviando mensagem: {e}", exc_info=True)
        return False


def main():
    parser = argparse.ArgumentParser(description="Daily Intelligence Dispatcher")
    parser.add_argument(
        "--area",
        default="Banking",
        help="Área pra enviar (Banking, Payments, Segmentos, ou 'all')"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Gera o relatório mas não envia"
    )
    args = parser.parse_args()
    
    print(f"""
╔═══════════════════════════════════════════════════════╗
║       Growth Ops Copilot — Daily Dispatcher           ║
║       {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                          ║
╚═══════════════════════════════════════════════════════╝
    """)
    
    check_env_vars()
    
    from config import AREAS_DAILY
    
    areas_to_send = list(AREAS_DAILY) if args.area.lower() == "all" else [args.area]
    
    success_count = 0
    for area in areas_to_send:
        if send_daily(area, dry_run=args.dry_run):
            success_count += 1
    
    total = len(areas_to_send)
    logger.info(f"Resultado: {success_count}/{total} Daily(s) enviados")
    
    sys.exit(0 if success_count == total else 1)


if __name__ == "__main__":
    main()
