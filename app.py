"""
Growth Ops Copilot — Main Entry Point
Roda via Slack Socket Mode (não precisa de URL pública)
"""
import logging
import threading
import schedule
import time
from datetime import datetime

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from config import SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET, SLACK_APP_TOKEN
from handlers import register_handlers
from daily import post_daily_to_channels

# ── Logging ────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("growth-bot")

# ── App Slack ──────────────────────────────────────────────
app = App(
    token=SLACK_BOT_TOKEN,
    signing_secret=SLACK_SIGNING_SECRET,
)

# Registra handlers
register_handlers(app)

# ── Scheduler (Daily Intelligence às 09h) ─────────────────
def _run_scheduler():
    """Thread do scheduler — roda o Daily Intelligence no horário."""
    schedule.every().day.at("09:00").do(post_daily_to_channels, app)
    logger.info("📰 Daily Intelligence agendado para 09:00 (horário da máquina)")
    
    while True:
        schedule.run_pending()
        time.sleep(60)


# ── Main ───────────────────────────────────────────────────
if __name__ == "__main__":
    print("""
    ==========================================
      Growth Ops Copilot v3.2
      Slack Bot - CRM Growth Intelligence
      Socket Mode: ON
      Areas: Banking - Payments - Seg - Cross
    ==========================================
    """)
    
    # Inicia scheduler em background
    scheduler_thread = threading.Thread(target=_run_scheduler, daemon=True)
    scheduler_thread.start()
    logger.info("Scheduler thread started")
    
    # Inicia Socket Mode
    logger.info(f"Starting Socket Mode... (App Token: {SLACK_APP_TOKEN[:20]}...)")
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()
