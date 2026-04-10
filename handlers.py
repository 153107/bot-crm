"""
Growth Ops Copilot — Slack Handlers v3
Conversacional com memória: dialoga pra pegar insumos,
busca por nome, responde direto, lembra contexto da conversa.
"""
import re
import logging
import traceback
import uuid
import time
from slack_bolt import App

import monday_client as monday
import databricks_client as db
import formatters as fmt
from parsers import parse_campaign_name
from config import (
    AREAS_ALLOWED, AREAS_DAILY, AREA_TO_BU,
    REPORTABLE_DB_CHANNELS, CHANNEL_MONDAY_TO_DB,
    SKIP_CHANNEL_LABELS,
)

logger = logging.getLogger("growth-bot")

# ═══════════════════════════════════════════════════════════
# Memória de conversa por usuário (TTL 10 min)
# ═══════════════════════════════════════════════════════════
# Guarda contexto da última interação pra resolver referências
# como "a primeira", "2", "essa", "sim", etc.

_conversation_memory: dict[str, dict] = {}
_MEMORY_TTL = 600  # 10 minutos

def _set_memory(user_id: str, key: str, value):
    """Salva dado na memória do usuário."""
    if user_id not in _conversation_memory:
        _conversation_memory[user_id] = {}
    _conversation_memory[user_id][key] = value
    _conversation_memory[user_id]["_ts"] = time.time()

def _get_memory(user_id: str, key: str, default=None):
    """Recupera dado da memória do usuário (se não expirou)."""
    mem = _conversation_memory.get(user_id, {})
    if not mem:
        return default
    if time.time() - mem.get("_ts", 0) > _MEMORY_TTL:
        _conversation_memory.pop(user_id, None)
        return default
    return mem.get(key, default)

def _clear_memory(user_id: str):
    """Limpa memória do usuário."""
    _conversation_memory.pop(user_id, None)


# Cache de respostas pendentes (delivery-choice)
_pending_responses: dict[str, dict] = {}


# ═══════════════════════════════════════════════════════════
# NLP — Intent detection + Entity extraction
# ═══════════════════════════════════════════════════════════

_INTENT_PATTERNS = {
    "campanha": [
        # ── Micro: campanha específica ──
        (r"\bdebug\b", 3),
        (r"\bdetalh", 2),
        (r"\binvestig", 2),
        (r"\bme (?:fala|conta|mostra).{0,20}(?:campanha|briefing)\b", 2),
        (r"\bcomo (?:tá|ta|está|esta|foi|anda).{0,20}(?:campanha|briefing)\b", 2),
        (r"\bo que (?:aconteceu|rolou).{0,20}(?:campanha|briefing)", 2),
        (r"\bbriefing\b", 2),
        (r"\bpuxa.{0,10}(?:campanha|briefing)", 2),
        (r"\bver.{0,10}campanha\b", 1),
        # ── Macro: visão de área ──
        (r"\bstatus\b", 3),
        (r"\bsitua[çc][aã]o\b", 2),
        (r"\bvis[aã]o geral\b", 2),
        (r"\boverview\b", 2),
        (r"\bpanorama\b", 2),
        (r"\bcomo (?:tão|estão|andam)\b", 2),
        (r"\bquantas campanhas\b", 2),
        (r"\bpipeline\b", 1),
        # Área sozinha → macro
        (r"^(e\s+)?(banking|bank|banco)(\?)?$", 3),
        (r"^(e\s+)?(payments?|pay|pagamentos?)(\?)?$", 3),
        (r"^(e\s+)?(segmentos?|seg)(\?)?$", 3),
        (r"^(e\s+)?(cross)(\?)?$", 3),
        (r"\b(?:fala|mostra|abre|puxa|quero ver)\b.{0,10}(?:banking|payments?|segmentos?|cross)", 2),
        (r"\bcampanhas?.{0,10}(?:banking|payments?|segmentos?|cross)", 2),
        (r"\b(?:banking|payments?|segmentos?|cross).{0,10}campanhas?\b", 2),
        (r"\b(?:lista|mostra|quais).{0,10}campanhas?\b", 2),
        (r"\b(?:resumo|vis[aã]o|geral)\b.{0,10}(?:banking|payments?|segmentos?|cross)", 2),
        (r"\bcomo (?:tá|ta|está|esta|anda|vai)\b(?!.{0,20}ontem)", 2),
    ],
    "lift": [
        (r"\blift\b", 3),
        (r"\bincrementalidade\b", 3),
        (r"\bp[_-]?value\b", 3),
        (r"\baprovad[oa]\b", 2),
        (r"\breprovad[oa]\b", 2),
        (r"\bresultado.{0,10}teste", 2),
        (r"\bteste.{0,10}resultado", 2),
        (r"\bteste\b", 1),
    ],
    "top": [
        (r"\btop\b", 3),
        (r"\bmelhor(?:es)?\s+campanha", 3),
        (r"\branking\b(?!.{0,5}(?:canal|cana[ií]s|produto|hor[áa]rio))", 3),
        (r"\bperformance\b", 2),
        (r"\bdestaque", 2),
        (r"\bcampe[aã]", 2),
        (r"\bmelhor\b", 1),
    ],
    "daily": [
        (r"\bdaily\b", 3),
        (r"\bd-?1\b", 3),
        (r"\bcomo foi (?:o dia|ontem|hoje)\b", 3),
        (r"\bque (?:rolou|aconteceu) ontem\b", 3),
        (r"\bontem\b", 2),
        (r"\bresum(?:o|ão)\b", 1),
        (r"\brelatório\b", 1),
        (r"\brelatorio\b", 1),
    ],
    "upcoming": [
        (r"\bpróxim", 2),
        (r"\bproxim", 2),
        (r"\bprevist", 2),
        (r"\bagenda", 2),
        (r"\bupcoming\b", 3),
        (r"\bpipeline\b", 2),
        (r"\bsemana que vem\b", 3),
        (r"\bo que (?:tem|vem|está).{0,15}(?:previst|agenda|próxim|programad)", 3),
        (r"\bpróxim.{0,15}campanha", 3),
        (r"\bproxim.{0,15}campanha", 3),
        (r"\bcampanha.{0,15}próxim", 3),
        (r"\bcampanha.{0,15}proxim", 3),
    ],
    "help": [
        (r"\bajuda\b", 3),
        (r"\bme ajuda\b", 3),
        (r"\bhelp\b", 3),
        (r"\bo que (?:vc|voce|você) (?:faz|sabe|pode)\b", 3),
        (r"\bcomo funciona\b", 3),
        (r"\bcomo usar\b", 3),
        (r"\bcomo (?:uso|utilizo|acesso)\b", 3),
        (r"\bcomandos?\b", 2),
        (r"\bgrowth ops\b", 2),
        (r"\bcopilot\b", 2),
        (r"\bo que (?:é|sao|são) (?:vc|voce|você|isso|esse bot)\b", 3),
        (r"\bpra que (?:serve|você serve)\b", 3),
        (r"\bquais (?:são|sao) (?:as|os) (?:opções|opcoes|consultas|comandos|funcionalidades)\b", 3),
        (r"\bnão sei (?:o que|como)\b", 2),
        (r"\bsocorro\b", 2),
    ],
    "sla": [
        (r"\bsla\b", 3),
        (r"\batrasa", 3),
        (r"\bvencid[oa]", 3),
        (r"\bfora do (?:sla|prazo)\b", 3),
        (r"\bprazo\b", 2),
        (r"\bvencimento\b", 2),
        (r"\bpendente.{0,15}avan[çc]ar\b", 3),
        (r"\bavan[çc]ar.{0,15}campanha\b", 2),
        (r"\bbacklog.{0,15}(?:atrasa|venc|sla|prazo)\b", 3),
        (r"\brisco\b", 1),
        (r"\burgente\b", 1),
        (r"\batrasad[oa]\b", 2),
    ],
}

_AREA_SYNONYMS = {
    "banking": ["banking", "bank", "banco", "banc"],
    "payments": ["payments", "payment", "pay", "pagamento", "pagamentos"],
    "segmentos": ["segmentos", "segmento", "seg"],
    "cross": ["cross"],
}


def _detect_intent(text: str) -> str | None:
    """Detecta intenção principal do texto usando pesos por padrão.
    
    Cada padrão tem um peso (1-3). O score de cada intent é a soma dos pesos
    de todos os padrões que matcham. Desempate por prioridade.
    
    Remoção de 'campanha(s)' genérico: a palavra 'campanha' sozinha não mais
    favorece debug/status — só matcha quando acompanhada de outros sinais.
    """
    text_lower = text.lower()
    scores = {}
    for intent, pattern_weights in _INTENT_PATTERNS.items():
        score = 0
        for item in pattern_weights:
            if isinstance(item, tuple):
                p, w = item
            else:
                p, w = item, 1
            if re.search(p, text_lower):
                score += w
        if score > 0:
            scores[intent] = score

    if not scores:
        if _extract_briefing_id(text):
            return "campanha"
        return None

    # Se tem briefing_id, bônus forte pra campanha
    if _extract_briefing_id(text):
        scores["campanha"] = scores.get("campanha", 0) + 5

    priority_order = [
        "sla", "campanha", "lift", "top", "daily", "upcoming", "help",
    ]
    max_score = max(scores.values())
    top_intents = [i for i, s in scores.items() if s == max_score]

    if len(top_intents) == 1:
        return top_intents[0]

    for intent in priority_order:
        if intent in top_intents:
            return intent

    return max(scores, key=scores.get)


def _extract_briefing_id(text: str) -> str | None:
    match = re.search(r"\b(\d{8,12})\b", text)
    return match.group(1) if match else None


def _extract_area(text: str) -> str | None:
    text_lower = text.lower()
    for area, synonyms in _AREA_SYNONYMS.items():
        for syn in synonyms:
            if re.search(rf"\b{re.escape(syn)}\b", text_lower):
                return area.title()
    return None


def _extract_campaign_name(text: str, intent: str) -> str | None:
    clean = re.sub(r"<@[A-Z0-9]+>", "", text).strip()
    clean = re.sub(r"[?!.,;:]+$", "", clean).strip()

    stopwords = {
        # Intenções/ações
        "debug", "status", "detalhe", "detalha", "investiga", "analisa",
        "busca", "buscar", "procura", "procurar", "encontra", "encontrar",
        # Verbos auxiliares
        "campanha", "campanhas", "briefing",
        "como", "tá", "ta", "está", "esta", "anda", "foi", "ser", "ter", "tem",
        "me", "fala", "falar", "conta", "contar", "mostra", "mostrar",
        "puxa", "puxar", "qual", "quais", "quero", "queria", "gostaria",
        "saber", "sobre", "ver", "veja", "olha", "olhar",
        # Artigos/preposições
        "do", "da", "de", "dos", "das", "no", "na", "nos", "nas",
        "o", "a", "os", "as", "um", "uma", "uns", "umas",
        "que", "pra", "para", "com", "sem", "por", "pelo", "pela",
        "ao", "aos", "em", "esse", "essa", "isso", "este", "esta",
        # Intenções que podem contaminar
        "top", "melhor", "melhores", "ranking", "lift", "teste", "testes",
        "daily", "ontem", "hoje", "semana", "mês", "resultado",
        "banking", "payments", "segmentos", "cross", "bank", "pay", "seg",
        "growth", "ops", "copilot", "área", "area",
        # Extras comuns
        "alguma", "algum", "coisa", "informação", "info", "dados",
    }

    clean = re.sub(r"\b\d{8,12}\b", "", clean).strip()
    words = clean.lower().split()
    remaining = [w for w in words if w not in stopwords and len(w) > 1]

    if remaining:
        return " ".join(remaining)
    return None


def _extract_list_choice(text: str) -> int | None:
    """Extrai escolha de lista: '1', 'a primeira', 'segunda', etc."""
    text_lower = text.strip().lower()

    # Número direto
    m = re.match(r"^(\d{1,2})$", text_lower)
    if m:
        return int(m.group(1))

    ordinals = {
        "primeir": 1, "segund": 2, "terceir": 3, "quart": 4, "quint": 5,
        "sext": 6, "sétim": 7, "setim": 7, "oitav": 8, "non": 9, "décim": 10,
    }
    for prefix, num in ordinals.items():
        if prefix in text_lower:
            return num

    return None


def _extract_period(text: str) -> str | None:
    """Detecta período explícito na mensagem.
    
    Retorna: '7d', '30d', 'mtd', 'ytd', 'historico', ou None se não especificou.
    """
    t = text.lower()
    # Períodos específicos
    if re.search(r"\b(hoje|d[- ]?0)\b", t):
        return "1d"
    if re.search(r"\b(ontem|d[- ]?1)\b", t):
        return "1d"
    if re.search(r"\b(semana|7 dias|ultimos 7|ult\w* 7)\b", t):
        return "7d"
    if re.search(r"\b(15 dias|ultimos 15|ult\w* 15)\b", t):
        return "15d"
    if re.search(r"\b(30 dias|ultimos 30|ult\w* 30|ultimo m[eê]s)\b", t):
        return "30d"
    if re.search(r"\b(m[eê]s atual|mtd|este m[eê]s|esse m[eê]s)\b", t):
        return "mtd"
    if re.search(r"\b(ytd|ano|este ano|esse ano)\b", t):
        return "ytd"
    if re.search(r"\b(hist[oó]rico|tudo|completo|todos|geral|todo)\b", t):
        return "historico"
    if re.search(r"\b(especif|briefing)\b", t):
        return "especifico"
    return None


def _needs_clarification(text: str, intent: str) -> str | None:
    """Verifica se a pergunta é ampla demais e precisa de clarificação.
    
    Retorna a mensagem de clarificação, ou None se pode prosseguir.
    Não pede clarificação se já tem briefing_id ou período explícito.
    """
    # Se tem briefing_id, é específico o suficiente
    if _extract_briefing_id(text):
        return None
    
    # Se já especificou período, ok
    if _extract_period(text):
        return None

    area = _extract_area(text)
    area_label = f" de {area}" if area else ""

    if intent == "lift":
        return (
            f"Vc quer os resultados de LIFT{area_label}:\n\n"
            f"1️⃣ Últimos 30 dias\n"
            f"2️⃣ Histórico completo da área\n"
            f"3️⃣ De um briefing específico (me passa o ID)\n\n"
            f"Manda o número ou descreve melhor!"
        )
    
    if intent == "top":
        return (
            f"Vc quer o ranking de campanhas{area_label}:\n\n"
            f"1️⃣ Últimos 7 dias\n"
            f"2️⃣ Últimos 30 dias\n"
            f"3️⃣ Histórico completo\n\n"
            f"Manda o número ou descreve melhor!"
        )

    if intent == "daily":
        return (
            f"Vc quer o relatório diário{area_label}:\n\n"
            f"1️⃣ Ontem (D-1)\n"
            f"2️⃣ Hoje (pode estar incompleto)\n"
            f"3️⃣ Última semana (resumo)\n\n"
            f"Manda o número ou descreve melhor!"
        )

    return None


def _clean_monday_name(item: dict) -> str:
    """Extract clean campaign name from a Monday item dict."""
    raw = item.get("name", "?")
    bid = str(item.get("numeric_mkvccc73", "")).strip()
    return parse_campaign_name(raw, bid if bid else None) or raw


def _enrich_with_monday_names(data: dict) -> dict:
    """Add 'monday_name' column to Databricks query results by looking up briefing IDs in Monday.
    
    This enriches the data dict in-place (adds a new column) so formatters can use
    the clean Monday name instead of the Databricks taxonomy string.
    """
    if not data.get("rows"):
        return data
    
    cols = data["columns"]
    
    # Find the briefing_id column index
    try:
        bid_idx = cols.index("briefing_id")
    except ValueError:
        return data  # No briefing_id column, nothing to enrich
    
    # Collect all briefing IDs
    briefing_ids = [str(row[bid_idx]).strip() for row in data["rows"] if row[bid_idx]]
    
    if not briefing_ids:
        return data
    
    # Bulk lookup from Monday
    try:
        names_map = monday.get_names_by_briefing_ids(briefing_ids)
    except Exception:
        names_map = {}
    
    # Add monday_name column
    data["columns"] = cols + ["monday_name"]
    data["rows"] = [
        list(row) + [names_map.get(str(row[bid_idx]).strip(), "")]
        for row in data["rows"]
    ]
    
    return data


def _enrich_lift_with_product(data: dict) -> None:
    """For LIFT rows without monday_name, try to get product_category from marcação.
    
    Modifica data in-place. Busca na marcação só os briefings que não têm nome.
    """
    if not data.get("rows") or "monday_name" not in data["columns"]:
        return

    cols = data["columns"]
    bid_idx = cols.index("briefing_id")
    name_idx = cols.index("monday_name")

    # Collect briefings without name
    missing_bids = [
        str(row[bid_idx]).strip()
        for row in data["rows"]
        if not row[name_idx]
    ]
    if not missing_bids:
        return

    # Query marcação for product_category (query leve: 1 row)
    product_map = {}
    for bid in missing_bids:
        try:
            result = db.execute_sql(
                f"SELECT product_category FROM {db.TABLE_MARCACAO} "
                f"WHERE briefing_id = '{bid}' AND product_category IS NOT NULL "
                f"LIMIT 1"
            )
            if result.get("rows") and result["rows"][0][0]:
                product_map[bid] = result["rows"][0][0]
        except Exception:
            continue

    # Apply fallback names
    for row in data["rows"]:
        if not row[name_idx] and str(row[bid_idx]).strip() in product_map:
            row[name_idx] = product_map[str(row[bid_idx]).strip()]


# ═══════════════════════════════════════════════════════════
# Resposta conversacional — actions
# ═══════════════════════════════════════════════════════════

def _respond_campanha(say, text: str, user_id: str, channel_id: str, channel_name: str, is_direct: bool):
    """Handler unificado: Debug + Status em uma consulta só.

    Fluxo de desambiguação:
    1. Tem briefing_id ou nome → micro direto
    2. Texto indica claramente macro (área, "quantas", "pipeline") → macro direto
    3. Ambíguo → pergunta: macro ou micro?
    """
    briefing_id   = _extract_briefing_id(text)
    area          = _extract_area(text)
    campaign_name = _extract_campaign_name(text, "campanha") if not briefing_id else None

    # ── Micro por briefing_id ─────────────────────────────
    if briefing_id:
        _clear_memory(user_id)
        say(f"⏳ Buscando campanha *{briefing_id}*...")
        _execute_campanha_micro(say, briefing_id, channel_id, is_direct)
        return

    # ── Micro por nome ────────────────────────────────────
    if campaign_name:
        say(f"🔍 Buscando *\"{campaign_name}\"* no Monday...")
        results = monday.get_campaign_by_name(campaign_name)
        if not results:
            say(
                f"Não encontrei campanha com \"{campaign_name}\". 🤔\n\n"
                f"Tenta me passar:\n"
                f"• O *briefing_id* (número de 11 dígitos)\n"
                f"• Ou outro *nome/termo*"
            )
            return
        if len(results) == 1:
            c = results[0]
            bid = str(c.get("numeric_mkvccc73", "")).strip()
            nome = _clean_monday_name(c)
            etapa = fmt.traduzir_etapa(c.get("status", ""), c.get("color_mky1jm7j", ""))
            say(f"Achei: *{nome}*\n{etapa}\nBuscando dados...")
            if bid:
                _execute_campanha_micro(say, bid, channel_id, is_direct)
            else:
                say("⚠️ Essa campanha não tem briefing_id no Monday.")
            return
        # Múltiplos
        _set_memory(user_id, "pending_list", results[:10])
        _set_memory(user_id, "pending_action", "campanha_micro")
        lines = [f"Encontrei *{len(results)}* campanhas com \"{campaign_name}\":\n"]
        for i, c in enumerate(results[:10], 1):
            nome  = _clean_monday_name(c)
            etapa = fmt.traduzir_etapa(c.get("status", ""), c.get("color_mky1jm7j", ""))
            ar    = c.get("color_mkv9c29w", "?")
            lines.append(f"*{i}.* {nome}\n    {ar} · {etapa}")
        if len(results) > 10:
            lines.append(f"\n_... e mais {len(results) - 10}. Refina a busca._")
        lines.append(f"\nQual delas? Me manda o *número*.")
        say("\n".join(lines))
        return

    # ── Sinal forte de macro ──────────────────────────────
    # Área sozinha, "quantas", "pipeline", "lista campanhas"
    macro_signals = [
        r"^(e\s+)?(banking|payments?|segmentos?|cross)(\?)?$",
        r"\bquantas campanhas\b",
        r"\b(?:lista|mostra|quais).{0,10}campanhas?\b",
        r"\b(?:pipeline|panorama|vis[aã]o geral|overview|resumo)\b",
        r"\b(?:banking|payments?|segmentos?|cross).{0,10}campanhas?\b",
        r"\bcampanhas?.{0,10}(?:banking|payments?|segmentos?|cross)",
    ]
    is_macro = any(re.search(p, text.lower()) for p in macro_signals)

    if is_macro:
        _execute_campanha_macro(say, area, channel_id, is_direct)
        return

    # ── Ambíguo → desambiguação ───────────────────────────
    pending = _get_memory(user_id, "pending_clarification")
    area_label = f" de *{area}*" if area else ""
    _set_memory(user_id, "pending_clarification", {
        "intent": "campanha",
        "area": area,
        "original_text": text,
        "channel_name": channel_name,
    })
    say(
        f"Vc quer uma visão *macro* ou *micro*{area_label}? 🤔\n\n"
        f"*1️⃣ Macro* — Pipeline geral da área (quantas estão em cada etapa, alertas de bloqueio)\n"
        f"*2️⃣ Micro* — Detalhes de uma campanha específica (me passa o nome ou briefing_id)\n\n"
        f"Manda *1* ou *2*, ou digita direto o que vc quer."
    )


def _execute_campanha_micro(say, briefing_id: str, channel_id: str, is_direct: bool):
    """Executa visão micro: Monday se não disparou, Databricks se disparou."""
    monday_data = monday.get_campaign_by_briefing_id(briefing_id)
    status_camp = (monday_data.get("status", "") if monday_data else "").lower()

    # Detecta canais permitidos via subitems
    allowed_channels = None
    if monday_data and monday_data.get("subitems"):
        allowed = set()
        for si in monday_data["subitems"]:
            label = (si.get("channel_label") or "").strip()
            if label in SKIP_CHANNEL_LABELS:
                continue
            db_ch = CHANNEL_MONDAY_TO_DB.get(label)
            if db_ch and db_ch in REPORTABLE_DB_CHANNELS:
                allowed.add(db_ch)
        if allowed:
            allowed_channels = allowed

    # Decide fonte pela etapa
    is_concluida = any(k in status_camp for k in ("concluíd", "concluido", "concluída"))

    if is_concluida or not monday_data:
        # Fonte: Databricks (disparou)
        db_data = db.get_campaign_full_debug(briefing_id)
        blocks  = fmt.format_micro_databricks(monday_data, db_data, allowed_channels=allowed_channels)
    else:
        # Fonte: Monday (ainda em planejamento/execução)
        blocks = fmt.format_micro_monday(monday_data)

    if is_direct:
        say(blocks=blocks)
    else:
        callback_id = _queue_delivery(blocks)
        say(blocks=[
            fmt.section("🔍 Dados prontos. Onde quer postar?"),
            fmt.actions_delivery_choice(callback_id),
        ])


def _execute_campanha_macro(say, area: str, channel_id: str, is_direct: bool):
    """Executa visão macro: pipeline + breakdown CRM + bloqueados."""
    summary = monday.get_status_summary(area=area, mtd=True)
    blocks  = fmt.format_macro_campanha(summary, area=area, mtd=True)

    if is_direct:
        say(blocks=blocks)
    else:
        callback_id = _queue_delivery(blocks)
        say(blocks=[
            fmt.section("📊 Status pronto. Onde quer postar?"),
            fmt.actions_delivery_choice(callback_id),
        ])


def _respond_lift(say, text: str, user_id: str, channel_id: str, is_direct: bool):
    briefing_id = _extract_briefing_id(text)
    area = _extract_area(text)
    period = _extract_period(text)

    # Mapear período pra dias
    days_map = {"7d": 7, "15d": 15, "30d": 30}
    lift_days = days_map.get(period)  # None = historico completo
    data = db.get_lift_results(briefing_id, days=lift_days)

    # Enrich with Monday names for readable campaign labels
    data = _enrich_with_monday_names(data)

    # Second pass: for rows without monday_name, try product_category from marcação
    _enrich_lift_with_product(data)

    # Filter: keep only campaigns that exist in our ecosystem
    # (have monday_name OR product_category from marcação)
    # This removes LIFT results from other teams that share the table
    if data.get("rows") and "monday_name" in data["columns"]:
        name_idx = data["columns"].index("monday_name")
        data["rows"] = [row for row in data["rows"] if row[name_idx]]

    # Filter by area if requested (cross-reference with Monday)
    if area and data.get("rows") and "monday_name" in data["columns"]:
        bid_idx = data["columns"].index("briefing_id")
        bids_in_area = set()
        for row in data["rows"]:
            bid = str(row[bid_idx]).strip()
            campaign = monday.get_campaign_by_briefing_id(bid)
            if campaign:
                camp_area = (campaign.get("color_mkv9c29w") or "").lower()
                if area.lower() in camp_area:
                    bids_in_area.add(bid)
            else:
                # Not in Monday — include anyway (already filtered by ecosystem above)
                bids_in_area.add(bid)
        data["rows"] = [
            row for row in data["rows"]
            if str(row[bid_idx]).strip() in bids_in_area
        ]

    if not data.get("rows"):
        area_label = f" de {area}" if area else ""
        say(f"Nenhum teste LIFT encontrado{area_label} nas campanhas do nosso board. 🧪")
        return

    blocks = fmt.format_lift_results(data)

    if is_direct:
        say(blocks=blocks)
    else:
        callback_id = _queue_delivery(blocks)
        say(blocks=[
            fmt.section("🧪 Resultados prontos. Onde quer postar?"),
            fmt.actions_delivery_choice(callback_id),
        ])


def _respond_top(say, text: str, user_id: str, channel_id: str, is_direct: bool):
    """Top campanhas — visual, com posição e linguagem de negócio."""
    area = _extract_area(text)
    bu = AREA_TO_BU.get(area) if area else None
    period = _extract_period(text)

    # Mapear período pra dias
    days_map = {"7d": 7, "15d": 15, "30d": 30, "historico": 365}
    days = days_map.get(period, 30)

    data = db.get_top_campaigns(days=days, bu=bu)

    # Enrich with Monday names (clean campaign names instead of taxonomy)
    data = _enrich_with_monday_names(data)

    blocks = fmt.format_top_campaigns(data, area)

    if is_direct:
        say(blocks=blocks)
    else:
        callback_id = _queue_delivery(blocks)
        say(blocks=[
            fmt.section("🏆 Ranking pronto. Onde quer postar?"),
            fmt.actions_delivery_choice(callback_id),
        ])


def _respond_sla(say, text: str, user_id: str, channel_id: str, is_direct: bool):
    """Campanhas fora do SLA ou próximas do vencimento."""
    area = _extract_area(text)
    sla_data = monday.get_sla_campaigns(area=area)

    blocks = fmt.format_sla_report(sla_data, area)

    if is_direct:
        say(blocks=blocks)
    else:
        callback_id = _queue_delivery(blocks)
        say(blocks=[
            fmt.section("⏰ Relatório de SLA pronto. Onde quer postar?"),
            fmt.actions_delivery_choice(callback_id),
        ])


def _respond_daily(say, text: str, user_id: str, channel_id: str, is_direct: bool):
    from daily import generate_daily_report
    area = _extract_area(text)
    bu = AREA_TO_BU.get(area) if area else None

    if area and area not in AREAS_ALLOWED:
        say(f"Área *{area}* não tá no escopo. As opções são: {', '.join(sorted(AREAS_ALLOWED))}")
        return
    if area and area not in AREAS_DAILY:
        say(f"ℹ️ _{area} não tem Daily automático (09h), mas tô gerando pra vc..._")

    say("⏳ Gerando relatório D-1...")
    blocks = generate_daily_report(bu=bu)

    if is_direct:
        say(blocks=blocks)
    else:
        callback_id = _queue_delivery(blocks)
        say(blocks=[
            fmt.section("📰 Daily pronto. Onde quer postar?"),
            fmt.actions_delivery_choice(callback_id),
        ])


def _respond_upcoming(say, text: str, user_id: str, channel_id: str, is_direct: bool):
    area = _extract_area(text)
    if area and area not in AREAS_ALLOWED:
        say(f"Área *{area}* não tá no escopo. Opções: {', '.join(sorted(AREAS_ALLOWED))}")
        return

    campaigns = monday.get_upcoming_campaigns(days=7, area=area)
    blocks = [fmt.header(f"📅 Próximos 7 dias" + (f" — {area}" if area else ""))]

    if not campaigns:
        blocks.append(fmt.section("_Nenhuma campanha prevista pra próxima semana._"))
    else:
        # Separar por status
        priorizadas = []
        backlog = []
        for c in campaigns:
            status = (c.get("status") or "").lower()
            if any(k in status for k in ("priorizada", "priorizadas", "teste tcpg")):
                priorizadas.append(c)
            else:
                backlog.append(c)

        def _fmt_campaign_line(c: dict) -> str:
            vol_sf = c.get("numeric_mkynfjpx", "")
            vol = fmt.fmt_number(vol_sf) if vol_sf else fmt.fmt_number(c.get("numeric_mkvn5qpc", 0))
            name = _clean_monday_name(c)
            start_dt = fmt.fmt_date(c.get("date_mkv87hhf"))
            etapa = fmt.traduzir_etapa(c.get("status", ""), c.get("color_mky1jm7j", ""))
            return (
                f"• *{name}*\n"
                f"  Início: {start_dt} | Clientes: {vol}\n"
                f"  {etapa}"
            )

        if priorizadas:
            blocks.append(fmt.section("*🟢 Priorizadas*"))
            for c in priorizadas[:10]:
                blocks.append(fmt.section(_fmt_campaign_line(c)))

        if backlog:
            blocks.append(fmt.section(f"*🟡 Backlog ({len(backlog)} com data prevista)*"))
            for c in backlog[:10]:
                blocks.append(fmt.section(_fmt_campaign_line(c)))

    blocks.append(fmt.divider())

    if is_direct:
        say(blocks=blocks)
    else:
        callback_id = _queue_delivery(blocks)
        say(blocks=[
            fmt.section("📅 Prévia pronta. Onde quer postar?"),
            fmt.actions_delivery_choice(callback_id),
        ])



def _respond_help(say):
    say(
        "Oi! Sou o *Growth Ops Copilot* 🔀 — tô aqui pra facilitar tua vida com dados de campanha.\n\n"
        "É só me perguntar de forma natural:\n\n"
        "📊 *Campanhas:* _\"como tá Banking?\"_ ou _\"em que etapa tá a campanha do cofre?\"_ ou _\"detalha o briefing 11415988520\"_\n"
        "🧪 *LIFT:* _\"resultados de lift Banking\"_ ou _\"tem teste aprovado?\"_\n"
        "⏰ *SLA:* _\"tem campanha atrasada?\"_ ou _\"o que tá fora do SLA?\"_\n"
        "📰 *Daily:* _\"como foi ontem?\"_ ou _\"daily Banking\"_\n"
        "📅 *Próximas:* _\"o que tem previsto pra semana?\"_\n\n"
        "Se eu listar opções, é só mandar o *número* da que vc quer. 💚"
    )


def _respond_not_understood(say, text: str):
    bid = _extract_briefing_id(text)
    if bid:
        say(f"Vi o briefing *{bid}* na sua mensagem. Quer que eu puxe os dados completos dele? 🔍")
        return

    say(
        "Hmm, não captei bem o que vc precisa. 🤔\n\n"
        "Tenta algo como:\n"
        "• _\"como tá Banking?\"_ → visão geral das campanhas\n"
        "• _\"melhor campanha de Payments\"_ → ranking de performance\n"
        "• _\"me fala da campanha cofrinho\"_ → detalhe de campanha\n"
        "• _\"como foi ontem?\"_ → relatório D-1\n\n"
        "Ou manda _\"ajuda\"_ pra ver tudo que sei fazer."
    )


def _handle_list_selection(say, text: str, user_id: str, channel_id: str, is_direct: bool):
    """Resolve seleção de item de uma lista anterior."""
    choice = _extract_list_choice(text)
    pending_list = _get_memory(user_id, "pending_list")
    pending_action = _get_memory(user_id, "pending_action")

    if not pending_list or not choice:
        return False  # Não era seleção de lista

    if choice < 1 or choice > len(pending_list):
        say(f"Escolha de *1* a *{len(pending_list)}*. Qual vc quer?")
        return True

    item = pending_list[choice - 1]
    _clear_memory(user_id)

    if pending_action in ("debug", "campanha_micro"):
        bid = str(item.get("numeric_mkvccc73", "")).strip()
        name = _clean_monday_name(item)
        if bid:
            say(f"Beleza! Buscando dados de *{name}* (briefing {bid})...")
            _execute_campanha_micro(say, bid, channel_id, is_direct)
        else:
            say(f"⚠️ *{name}* não tem briefing_id no Monday. Preciso dele pra buscar os dados.")

    return True


# ═══════════════════════════════════════════════════════════
# Clarification response handler
# ═══════════════════════════════════════════════════════════

# Maps: intent → {choice_number → period_keyword to inject}
_CLARIFICATION_OPTIONS = {
    "lift": {
        "1": "ultimos 30 dias",
        "2": "historico completo",
        "3": None,  # Specific — needs briefing_id
    },
    "campanha": {
        "1": "__macro__",   # sinal especial: vai pra macro
        "2": "__micro__",   # sinal especial: vai pedir nome/id
    },
    "top": {
        "1": "ultimos 7 dias",
        "2": "ultimos 30 dias",
        "3": "historico completo",
    },
    "daily": {
        "1": "ontem",
        "2": "hoje",
        "3": "ultima semana",
    },
}


def _handle_clarification_response(
    say, text: str, user_id: str, channel_id: str,
    channel_name: str, is_direct: bool, ctx: dict,
) -> bool:
    """Handle user's response to a clarification question.
    
    Returns True if handled, False if should fall through to normal processing.
    """
    intent = ctx["intent"]
    area = ctx["area"]
    original = ctx["original_text"]
    ch_name = ctx.get("channel_name", "")

    # Clear pending state
    _set_memory(user_id, "pending_clarification", None)

    # Check if user typed a number (1, 2, 3)
    choice = text.strip()
    if choice in ("1", "2", "3"):
        options = _CLARIFICATION_OPTIONS.get(intent, {})
        period_text = options.get(choice)

        if period_text is None and intent == "lift" and choice == "3":
            # User wants specific briefing — ask for ID
            say("Me manda o briefing ID da campanha que vc quer ver o LIFT. 🧪")
            return True

        # Build enriched text with period injected
        area_part = f" {area}" if area else ""
        enriched = f"{original} {period_text}"
        logger.info(f"Clarification resolved: choice={choice} -> '{enriched}'")

        # Campanha: tratar sinais especiais __macro__ / __micro__
        if intent == "campanha":
            if period_text == "__macro__":
                _execute_campanha_macro(say, area, channel_id, is_direct)
            elif period_text == "__micro__":
                say(
                    "Me passa o *nome* ou o *briefing_id* da campanha que vc quer ver. 🔍\n"
                    "Exemplo: _\"campanha do cofrinho\"_ ou _\"11415988520\"_"
                )
            return True

        # Re-route with enriched text
        if intent == "lift":
            _respond_lift(say, enriched, user_id, channel_id, is_direct)
        elif intent == "top":
            _respond_top(say, enriched, user_id, channel_id, is_direct)
        elif intent == "daily":
            _respond_daily(say, enriched, user_id, channel_id, is_direct)
        return True

    # Not a number — check if it's a new period keyword
    period = _extract_period(text)
    if period:
        enriched = f"{original} {text}"
        logger.info(f"Clarification resolved via period: '{enriched}'")
        if intent == "lift":
            _respond_lift(say, enriched, user_id, channel_id, is_direct)
        elif intent == "campanha":
            _respond_campanha(say, enriched, user_id, channel_id, ch_name, is_direct)
        elif intent == "top":
            _respond_top(say, enriched, user_id, channel_id, is_direct)
        elif intent == "daily":
            _respond_daily(say, enriched, user_id, channel_id, is_direct)
        return True

    # Check if it's a briefing_id (for LIFT "specific" option)
    bid = _extract_briefing_id(text)
    if bid and intent == "lift":
        enriched = f"lift {bid}"
        _respond_lift(say, enriched, user_id, channel_id, is_direct)
        return True

    # User said something else entirely — don't handle, let it fall through
    return False


# ═══════════════════════════════════════════════════════════
# Router principal
# ═══════════════════════════════════════════════════════════

def _process_message(say, text: str, user_id: str, channel_id: str, channel_name: str = "", is_direct: bool = False):
    text_clean = re.sub(r"<@[A-Z0-9]+>", "", text).strip()
    if not text_clean:
        _respond_help(say)
        return

    # 1. Checar se é resposta a pergunta de clarificação pendente
    pending_clarification = _get_memory(user_id, "pending_clarification")
    if pending_clarification:
        resolved = _handle_clarification_response(say, text_clean, user_id, channel_id, channel_name, is_direct, pending_clarification)
        if resolved:
            return

    # 2. Checar se é seleção de lista pendente ("1", "a primeira", etc)
    if _get_memory(user_id, "pending_list"):
        if _handle_list_selection(say, text_clean, user_id, channel_id, is_direct):
            return

    # 3. Detectar intenção normal
    intent = _detect_intent(text_clean)
    logger.info(f"NLP: text='{text_clean}' intent={intent} user={user_id}")

    # 4. Checar se precisa clarificação (pergunta ampla sem período)
    intents_with_clarification = {"lift", "campanha", "top", "daily"}
    if intent in intents_with_clarification:
        clarification = _needs_clarification(text_clean, intent)
        if clarification:
            area = _extract_area(text_clean)
            _set_memory(user_id, "pending_clarification", {
                "intent": intent,
                "area": area,
                "original_text": text_clean,
                "channel_name": channel_name,
            })
            say(clarification)
            return

    if intent == "campanha":
        _respond_campanha(say, text_clean, user_id, channel_id, channel_name, is_direct)
    elif intent == "lift":
        _respond_lift(say, text_clean, user_id, channel_id, is_direct)
    elif intent == "top":
        _respond_top(say, text_clean, user_id, channel_id, is_direct)
    elif intent == "sla":
        _respond_sla(say, text_clean, user_id, channel_id, is_direct)
    elif intent == "daily":
        _respond_daily(say, text_clean, user_id, channel_id, is_direct)
    elif intent == "upcoming":
        _respond_upcoming(say, text_clean, user_id, channel_id, is_direct)
    elif intent == "help":
        _respond_help(say)
    else:
        _respond_not_understood(say, text_clean)


# ═══════════════════════════════════════════════════════════
# Registro dos handlers no Slack
# ═══════════════════════════════════════════════════════════

def register_handlers(app: App):

    @app.command("/growth")
    def handle_growth(ack, command, say, client):
        ack()
        text = (command.get("text") or "").strip()
        user_id = command["user_id"]
        channel_id = command["channel_id"]
        channel_name = command.get("channel_name", "")

        try:
            if not text or text.lower() == "help":
                _respond_help(say)
                return
            _process_message(say, text, user_id, channel_id, channel_name, is_direct=False)
        except Exception as e:
            logger.error(f"Error /growth: {e}\n{traceback.format_exc()}")
            say("Ops, algo deu errado na consulta. Tenta de novo em 1 minuto? Se persistir, avisa a Jack. 🔀")

    @app.command("/campaign")
    def handle_campaign(ack, say):
        ack()
        say("🚧 Ainda em construção!")

    @app.event("app_mention")
    def handle_mention(event, say):
        text = event.get("text", "")
        user_id = event.get("user", "")
        channel_id = event.get("channel", "")

        try:
            _process_message(say, text, user_id, channel_id, is_direct=True)
        except Exception as e:
            logger.error(f"Error mention: {e}\n{traceback.format_exc()}")
            say("Ops, algo deu errado na consulta. Tenta de novo em 1 minuto? Se persistir, avisa a Jack. 🔀")

    @app.event("message")
    def handle_dm(event, say):
        # Só processa DMs diretas ao bot
        if event.get("channel_type") != "im":
            return
        # Ignora mensagens de bots (incluindo o próprio bot)
        if event.get("bot_id"):
            return
        # Ignora subtypes (edições, deleções, bot_message, etc.)
        if event.get("subtype"):
            return

        text = (event.get("text") or "").strip()
        if not text:
            return

        user_id = event.get("user", "")
        channel_id = event.get("channel", "")

        try:
            _process_message(say, text, user_id, channel_id, is_direct=True)
        except Exception as e:
            logger.error(f"Error DM: {e}\n{traceback.format_exc()}")
            say("Ops, algo deu errado na consulta. Tenta de novo em 1 minuto? Se persistir, avisa a Jack. 🔀")

    # Silencia eventos de message com subtypes que o Bolt reclamaria
    @app.event({"type": "message", "subtype": "bot_message"})
    def handle_bot_message(): pass

    @app.event({"type": "message", "subtype": "message_changed"})
    def handle_message_changed(): pass

    @app.event({"type": "message", "subtype": "message_deleted"})
    def handle_message_deleted(): pass

    @app.action("deliver_channel")
    def deliver_channel(ack, body, client):
        ack()
        _deliver_response(body, client, mode="channel")

    @app.action("deliver_dm")
    def deliver_dm(ack, body, client):
        ack()
        _deliver_response(body, client, mode="dm")

    @app.action("deliver_both")
    def deliver_both(ack, body, client):
        ack()
        _deliver_response(body, client, mode="both")

    @app.action("status_full_history")
    def status_full_history(ack, body, say):
        ack()
        area = (body["actions"][0].get("value") or "").strip()
        area = area.title() if area else None
        if area and area not in AREAS_ALLOWED:
            area = None
        summary = monday.get_status_summary(area=area, mtd=False)
        blocks = fmt.format_status_summary(summary, area, mtd=False)
        say(blocks=blocks)


# ═══════════════════════════════════════════════════════════
# Delivery helpers
# ═══════════════════════════════════════════════════════════

def _queue_delivery(blocks: list[dict]) -> str:
    cb = uuid.uuid4().hex[:12]
    _pending_responses[cb] = {"blocks": blocks}
    return cb


def _deliver_response(body: dict, client, mode: str):
    action = body["actions"][0]
    callback_id = action["value"]
    user_id = body["user"]["id"]
    channel_id = body["channel"]["id"]

    pending = _pending_responses.pop(callback_id, None)
    if not pending:
        try:
            client.chat_postEphemeral(
                channel=channel_id, user=user_id,
                text="⚠️ Essa resposta já foi entregue ou expirou. Roda de novo!"
            )
        except Exception:
            pass
        return

    blocks = pending.get("blocks", [])

    if mode in ("channel", "both"):
        client.chat_postMessage(channel=channel_id, blocks=blocks)

    if mode in ("dm", "both"):
        dm = client.conversations_open(users=[user_id])
        dm_channel = dm["channel"]["id"]
        client.chat_postMessage(channel=dm_channel, blocks=blocks)
