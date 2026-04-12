"""
Growth Ops Copilot — Config
Carrega variáveis de ambiente do .env
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Slack ──────────────────────────────────────────────
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET", "")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN", "")

# Canais por BU (somente as 3 áreas no escopo)
SLACK_CHANNELS = {
    "Banking": os.getenv("SLACK_CHANNEL_BANKING", "sfpf-banking-growth-crm"),
    "Segmentos": os.getenv("SLACK_CHANNEL_SEGMENTOS", "sfpf-segmentos-growth-crm"),
    "Payments": os.getenv("SLACK_CHANNEL_PAYMENTS", "sfpf-payments-growth-crm"),
}

# Inferir área pelo nome do canal Slack (reverso de SLACK_CHANNELS)
SLACK_CHANNEL_TO_AREA = {v: k for k, v in SLACK_CHANNELS.items()}

# ── Monday.com ─────────────────────────────────────────
MONDAY_API_TOKEN = os.environ.get("MONDAY_API_TOKEN", "")
MONDAY_BOARD_ID = os.environ.get("MONDAY_BOARD_ID", "")
MONDAY_API_URL = "https://api.monday.com/v2"

# Mapa de áreas → index da coluna color_mkv9c29w
MONDAY_AREA_MAP = {
    "Payments": 0,
    "Banking": 1,
    "Segmentos": 2,
    "Cross": 3,
    "CRM": 4,
}

# ── Databricks ─────────────────────────────────────────
# OAuth U2M configurado via: databricks auth login --profile picpay
# Config agora está no databricks_client.py (não precisa mais de .env)
# Mantém só o mapeamento de BUs pra outros arquivos usarem

# Mapa BU Databricks → Monday
BU_MAP = {
    "SFPF Banking": "Banking",
    "SFPF Payments": "Payments",
    "SFPF Segmentos": "Segmentos",
    "SFPF Cross": "Cross",
    "SFPF": "CRM",
}

# ═══════════════════════════════════════════════════════════
# ESCOPO — 4 áreas consultáveis (exclui apenas CRM)
# ═══════════════════════════════════════════════════════════
# Cross é consultável em todos os comandos manuais,
# mas NÃO recebe Daily automático (sem canal Slack próprio).
AREAS_ALLOWED = {"Banking", "Payments", "Segmentos", "Cross"}

# Áreas com Daily automático às 09h (têm canal Slack dedicado)
AREAS_DAILY = {"Banking", "Payments", "Segmentos"}

# Mapa área → BU Databricks (todas as consultáveis)
AREA_TO_BU = {
    "Banking": "SFPF Banking",
    "Payments": "SFPF Payments",
    "Segmentos": "SFPF Segmentos",
    "Cross": "SFPF Cross",
}

# ═══════════════════════════════════════════════════════════
# MAPEAMENTO DE 14 CANAIS (Monday → Databricks → Taxonomia)
# ═══════════════════════════════════════════════════════════
# Monday tem 16 labels nos subitems. Descartamos 2:
#   - "" (vazio)
#   - "Banner" (não gera disparo no Databricks)
# Sobram 14 canais válidos → consolidados em 7 canais Databricks.

# Monday label → canal Databricks (None = ignorar)
CHANNEL_MONDAY_TO_DB = {
    # --- INAPP (3 variantes) ---
    "In-App Full": "INAPP",
    "In-App Modal": "INAPP",
    "In-App Slide": "INAPP",
    # --- PUSH (6 variantes criativas, mesmo canal Databricks) ---
    "Push": "PUSH",
    "Push + Central": "PUSH",
    "Push + Imagem": "PUSH",
    "Push + Carrossel": "PUSH",
    "Push + Img + Central": "PUSH",
    "Push + Carr + Central": "PUSH",
    # --- DEMAIS (1:1) ---
    "E-Mail": "EMAIL",
    "D.M.": "DM",
    "WhatsAPP": "WHATSAPP",
    "SMS": "SMS",
    "WebView": "WEBVIEW",       # placeholder — não reportável até existir dados
    # --- IGNORADOS ---
    "Banner": None,             # não gera disparo
    "Central de Notif.": None,  # sem dados no Databricks
    "": None,
    None: None,
}

# Monday label → sigla de taxonomia (usada na properties_sending_name)
CHANNEL_MONDAY_SIGLA = {
    "In-App Full": "inappf",
    "In-App Modal": "inappm",
    "In-App Slide": "inapps",
    "Push": "pushntf",
    "Push + Central": "pushntf",
    "Push + Imagem": "pushntf",
    "Push + Carrossel": "pushntf",
    "Push + Img + Central": "pushntf",
    "Push + Carr + Central": "pushntf",
    "E-Mail": "Email",
    "D.M.": "dms",
    "WhatsAPP": "wap",
    "SMS": "sms",
    "WebView": "webview",
}

# Siglas de taxonomia → canal Databricks (reverso, pra parse de taxonomia)
CHANNEL_TAXONOMY_TO_DB = {
    "inappf": "INAPP",
    "inappm": "INAPP",
    "inapps": "INAPP",
    "pushntf": "PUSH",
    "Push": "PUSH",
    "Email": "EMAIL",
    "dms": "DM",
    "wap": "WHATSAPP",
    "wpp": "WHATSAPP",
    "sms": "SMS",
    "webview": "WEBVIEW",
    "webv": "WEBVIEW",
}

# Labels a DESCARTAR (não geram disparo, não reportáveis)
SKIP_CHANNEL_LABELS = {"Banner", "Central de Notif.", "", None}

# Canais com dados reais no Databricks (exclui WEBVIEW por ora)
REPORTABLE_DB_CHANNELS = {"INAPP", "PUSH", "EMAIL", "DM", "WHATSAPP", "SMS"}

# Emoji por canal Databricks (pra display no Slack)
CHANNEL_EMOJI = {
    "INAPP": "📲",
    "PUSH": "🔔",
    "EMAIL": "✉️",
    "DM": "💬",
    "WHATSAPP": "🟢",
    "SMS": "📩",
    "WEBVIEW": "🌐",
}

# Label amigável por canal Databricks
CHANNEL_DISPLAY_NAME = {
    "INAPP": "In-App",
    "PUSH": "Push",
    "EMAIL": "E-Mail",
    "DM": "Direct Message",
    "WHATSAPP": "WhatsApp",
    "SMS": "SMS",
    "WEBVIEW": "WebView",
}

# ═══════════════════════════════════════════════════════════
# MÉTRICAS POR CANAL — colunas corretas no Databricks
# ═══════════════════════════════════════════════════════════
# INAPP usa colunas exclusivas (inapp_opened_at / inapp_clicked_at)
# opened_at/clicked_at são SEMPRE NULL/0 pra INAPP!
#
# Canais SEM clique (sempre 0): PUSH, WHATSAPP, SMS
# Canal SEM abertura nem clique: SMS (sem dados em Mar/2026)

CHANNELS_NO_CLICK = {"PUSH", "WHATSAPP", "SMS"}  # clicked_at sempre 0
CHANNELS_NO_OPEN = {"SMS"}                         # sem dados de abertura

# Sigla da taxonomia por BU (usado no filtro: campaign_name LIKE '%sfpfban%')
BU_TAXONOMY_SIGLA = {
    "SFPF Banking": "sfpfban",
    "SFPF Payments": "sfpfpay",
    "SFPF Segmentos": "sfpfseg",
    "SFPF Cross": "sfpfcro",
}

# ═══════════════════════════════════════════════════════════
# SEEDLIST — consumer_ids fixos excluídos de todas as queries
# ═══════════════════════════════════════════════════════════
# Esses IDs participam de disparos de teste (seedlist) antes do
# disparo real. São sempre os mesmos — nunca entram novos membros.
# Aplicar em TODAS as queries de disparo via SEEDLIST_FILTER.
SEEDLIST_CONSUMER_IDS = (
    "140307882125168218",
    "334428515250163706",
    "110542583387691346",
    "164032341298786597",
    "177744940880682527",
    "129603751216762637",
    "186354102042317401",
    "223734888742478217",
    "157769491182413978",
    "115782605936524514",
    "199984163564535194",
    "855574196516324388",
    "306199889496343350",
)

# Cláusula SQL pronta pra usar em qualquer query de disparo
SEEDLIST_FILTER = f"AND consumer_id NOT IN ({', '.join(repr(i) for i in SEEDLIST_CONSUMER_IDS)})"


# ═══════════════════════════════════════════════════════════
# LINGUAGEM DIDÁTICA — Tradução de status técnico → humano
# ═══════════════════════════════════════════════════════════
# O time não é técnico. O bot precisa explicar "em que pé está"
# a campanha, não só cuspir o label do Monday.
#
# Fontes dos valores (consultado via API, Mar/2026):
# ── Status & Fluxo de Campanhas ─────────────────────────
# Baseado nos PDFs oficiais:
#   - "Planejamento de Campanhas – Growth/CRM" (Growth flow, 5 abas)
#   - "Criação de Campanhas – CRM" (CRM flow, 3 abas + status detalhado)
#
# Monday columns:
#   - status (Status Campanha): macro-etapa (Backlog → Priorizadas → Concluída)
#   - color_mky1jm7j (Status Andamento CRM): micro-etapa de construção
#
# IMPORTANTE sobre SLA (do PDF Growth):
#   - SLA só é contabilizado quando campanha chega na aba 4 (Criativos)
#   - Abas 1-3 são planejamento e NÃO entram no cálculo de SLA
#   - Botão "Avançar etapa" NÃO reinicia nem ajusta SLA
#   - Após priorização, NÃO é permitido ajustar peças (contorna SLA)

# ── Fluxo Growth (5 abas) ──────────────────────────────
# Abas 1→3: automáticas (preencheu campos? avança)
# Aba 4: manual (botão "Avançar etapa" + validação SLA)
# Aba 5: exceção (fora do prazo → ajustar data ou solicitar exceção)
FLOW_GROWTH_STAGES = [
    {"aba": 1, "nome": "BKLG | Planejado",    "auto": True,  "descricao": "Planejamento inicial e dados operacionais"},
    {"aba": 2, "nome": "BKLG | Objetivos",    "auto": True,  "descricao": "Campos estratégicos e definição da campanha"},
    {"aba": 3, "nome": "BKLG | Touchpoints",  "auto": True,  "descricao": "Detalhamento de canais e touchpoints"},
    {"aba": 4, "nome": "BKLG | Criativos",    "auto": False, "descricao": "Etapa final antes do envio para CRM (valida SLA)"},
    {"aba": 5, "nome": "BKLG | Fora do Prazo", "auto": False, "descricao": "Exceção SLA — ajustar data ou negociar com CRM"},
]

# ── Fluxo CRM (3 abas) ─────────────────────────────────
# Aba 6→7: automáticas (preencheu campos? avança)
# Aba 8: manual (Status Campanha → Concluída move pra board de concluídas)
FLOW_CRM_STAGES = [
    {"aba": 6, "nome": "Prio | Brief | CRM",       "auto": True,  "descricao": "Abertura do Briefing Unificado via Governança"},
    {"aba": 7, "nome": "Prio | Base",               "auto": True,  "descricao": "Criação do segmento e publicação no Marketing Cloud"},
    {"aba": 8, "nome": "Priorizadas | Campanhas",   "auto": False, "descricao": "Construção da campanha, validações e conclusão"},
]

# ── Status Campanha (coluna `status`) ───────────────────
# Ordem do fluxo: Backlog → Priorizadas → Concluída
# Desvios: Teste TCPG (em teste LIFT), Reprovada (teste não passou)
STATUS_CAMPANHA_HUMANO = {
    "Backlog":       "🟡 Backlog — Growth ainda está planejando (abas 1-4)",
    "Priorizadas":   "🟢 Priorizada — CRM já está atuando na campanha",
    "Concluído":     "🟢 Concluída — campanha ativada com sucesso no Marketing Cloud",
    "Concluída":     "🟢 Concluída — campanha ativada com sucesso no Marketing Cloud",
    "Teste TCPG":    "🟠 Em teste LIFT/TCPG — campanha ativada mas aguardando resultado do teste",
    "Reprovada":     "🔴 Reprovada — passou pelo teste TCPG mas não foi aprovada pra ativação final",
}

# ── Status CRM (coluna `color_mky1jm7j`) ───────────────
# Ordem do fluxo (do PDF CRM, p.4):
#   1. Abrir Briefing → auto → 2. Montar Segmento → auto → 3. Montar Jornada
#   → manual → 4. Testes → manual → 5. Em Finalização → manual → 6. Feito
# Desvios: AppSheet (falta aprovação), Com Impedimento (bloqueio)
STATUS_CRM_HUMANO = {
    "Abrir Briefing CRM": "📝 Passo 1/6 — CRM abrindo briefing no monday de Governança",
    "Abrir Briefing":     "📝 Passo 1/6 — CRM abrindo briefing no monday de Governança",
    "Montar Segmento":    "🟡 Passo 2/6 — CRM criando segmento e publicando no Marketing Cloud",
    "Montar Jornada":     "🟡 Passo 3/6 — CRM montando jornada (touchpoints, canais, timing)",
    "Testes":             "🟠 Passo 4/6 — CRM rodando testes e enviando pra aprovação do Growth",
    "Em Finalização":     "🟠 Passo 5/6 — Ajustes finais e QA da campanha",
    "Feito":              "🟢 Passo 6/6 — CRM finalizou, campanha pronta",
    "AppSheet":           "🟠 CRM finalizou, mas falta aprovação da ativação da jornada",
    "Com Impeditivo":     "🔴 Bloqueada — tem impedimento que precisa ser resolvido",
    "Com Impedimento":    "🔴 Bloqueada — tem impedimento que precisa ser resolvido",
}

# Ordem numérica dos Status CRM pra cálculo de progresso
STATUS_CRM_ORDER = {
    "abrir briefing crm": 1, "abrir briefing": 1,
    "montar segmento": 2,
    "montar jornada": 3,
    "testes": 4,
    "em finalização": 5, "em finalizacao": 5,
    "feito": 6,
    "appsheet": 6,  # também é fim (variante)
    "com impeditivo": -1, "com impedimento": -1,  # bloqueio
}

# ── Combinação Status Campanha × Status CRM ────────────
# Cruza macro (campanha) + micro (CRM) → frase única pro Slack
# Chaves: (status_campanha_lower, status_crm_lower)
STATUS_COMBO_HUMANO = {
    # ── Backlog (Growth ainda planejando) ──
    ("backlog", ""):                          "🟡 Backlog — Growth ainda está no planejamento",

    # ── Priorizadas (CRM atuando) ──
    ("priorizadas", ""):                      "🟢 Priorizada — aguardando CRM iniciar",
    ("priorizadas", "abrir briefing crm"):    "📝 Priorizada — CRM abrindo briefing (passo 1/6)",
    ("priorizadas", "abrir briefing"):        "📝 Priorizada — CRM abrindo briefing (passo 1/6)",
    ("priorizadas", "montar segmento"):       "🟡 Priorizada — CRM montando segmento (passo 2/6)",
    ("priorizadas", "montar jornada"):        "🟡 Priorizada — CRM montando jornada (passo 3/6)",
    ("priorizadas", "testes"):                "🟠 Priorizada — CRM rodando testes (passo 4/6)",
    ("priorizadas", "em finalização"):        "🟠 Priorizada — CRM finalizando (passo 5/6)",
    ("priorizadas", "em finalizacao"):        "🟠 Priorizada — CRM finalizando (passo 5/6)",
    ("priorizadas", "feito"):                 "🟢 Priorizada — CRM finalizou, aguardando ativação",
    ("priorizadas", "appsheet"):              "🟠 Priorizada — CRM finalizou, aguardando aprovação de ativação",
    ("priorizadas", "com impeditivo"):        "🔴 Priorizada mas bloqueada — impedimento precisa ser resolvido",
    ("priorizadas", "com impedimento"):       "🔴 Priorizada mas bloqueada — impedimento precisa ser resolvido",

    # ── Concluída (ativada no Marketing Cloud) ──
    ("concluído", ""):                        "🟢 Campanha concluída com sucesso",
    ("concluído", "feito"):                   "🟢 Campanha concluída e ativada no Marketing Cloud",
    ("concluída", ""):                        "🟢 Campanha concluída com sucesso",
    ("concluída", "feito"):                   "🟢 Campanha concluída e ativada no Marketing Cloud",

    # ── Teste TCPG (em teste LIFT) ──
    ("teste tcpg", ""):                       "🟠 Campanha ativada, em teste LIFT/TCPG",
    ("teste tcpg", "feito"):                  "🟠 Campanha ativada, teste LIFT/TCPG em andamento",

    # ── Reprovada ──
    ("reprovada", ""):                        "🔴 Campanha reprovada no teste TCPG",
    ("reprovada", "feito"):                   "🔴 Campanha reprovada — CRM finalizou mas teste reprovou",
}
