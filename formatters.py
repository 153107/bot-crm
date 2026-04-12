"""
Growth Ops Copilot — Formatters
Mensagens visuais, com linguagem de negócio.
Sem termos técnicos, sem nomes de colunas.
"""
from datetime import datetime
from config import (
    CHANNEL_EMOJI, CHANNEL_DISPLAY_NAME, CHANNEL_MONDAY_TO_DB,
    SKIP_CHANNEL_LABELS, REPORTABLE_DB_CHANNELS,
    CHANNELS_NO_CLICK, CHANNELS_NO_OPEN,
    STATUS_CAMPANHA_HUMANO, STATUS_CRM_HUMANO, STATUS_COMBO_HUMANO,
    STATUS_CRM_ORDER,
)
from parsers import parse_campaign_name


# ═══════════════════════════════════════════════════════════
# Helpers de formatação
# ═══════════════════════════════════════════════════════════

_MEDAL = {1: "🥇", 2: "🥈", 3: "🥉"}
_BU_SHORT = {
    "SFPF Banking": "Banking",
    "SFPF Payments": "Payments",
    "SFPF Segmentos": "Segmentos",
    "SFPF Cross": "Cross",
    "SFPF": "CRM",
}


def traduzir_etapa(status_campanha: str, status_crm: str = "") -> str:
    """Traduz os status técnicos do Monday em linguagem humana.

    Cruza Status Campanha + Status CRM pra dar uma frase única
    que qualquer pessoa do time entenda sem precisar conhecer o board.

    Baseado nos PDFs oficiais:
      - Growth flow: 5 abas (Planejado → Objetivos → Touchpoints → Criativos → Fora do Prazo)
      - CRM flow: 6 passos (Briefing → Segmento → Jornada → Testes → Finalização → Feito)

    Exemplos:
        traduzir_etapa("Priorizadas", "Montar Jornada")
        → "🗺️ Priorizada — CRM montando jornada (passo 3/6)"

        traduzir_etapa("Backlog", "")
        → "📋 Na fila — Growth ainda está no planejamento"
    """
    sc = (status_campanha or "").strip()
    scr = (status_crm or "").strip()

    # Backlog = ainda com o Growth, CRM não tocou — ignorar status CRM
    if "backlog" in sc.lower():
        scr = ""

    # 1. Tenta combinação exata (mais preciso)
    combo_key = (sc.lower(), scr.lower())
    if combo_key in STATUS_COMBO_HUMANO:
        return STATUS_COMBO_HUMANO[combo_key]

    # 2. Se tem Status CRM, monta frase combinada
    sc_txt = STATUS_CAMPANHA_HUMANO.get(sc)
    scr_txt = STATUS_CRM_HUMANO.get(scr)

    if sc_txt and scr_txt:
        # Pega a parte antes do "—" do campanha + descrição completa do CRM
        base = sc_txt.split("—")[0].strip() if "—" in sc_txt else sc_txt
        return f"{base} — {scr_txt}"

    # 3. Só Status Campanha
    if sc_txt:
        return sc_txt

    # 4. Só Status CRM
    if scr_txt:
        return scr_txt

    # 5. Fallback: raw values (nunca deveria chegar aqui com dados bons)
    if sc and scr:
        return f"{sc} | CRM: {scr}"
    return sc or scr or "Status não informado"


def progresso_crm(status_crm: str) -> str:
    """Retorna barra de progresso visual do Status CRM.

    Exemplo:
        progresso_crm("Montar Jornada")
        → "●●●○○○ Passo 3/6"

        progresso_crm("Com Impeditivo")
        → "🚫 Bloqueada"
    """
    scr = (status_crm or "").strip().lower()
    step = STATUS_CRM_ORDER.get(scr)

    if step is None:
        return ""
    if step == -1:
        return "🚫 Bloqueada"

    filled = "●" * step
    empty = "○" * (6 - step)
    return f"{filled}{empty} Passo {step}/6"


def _fmt_date(val) -> str:
    """Formata data para DD/MM/YYYY. Aceita YYYY-MM-DD, ISO timestamp, ou date obj."""
    if not val or str(val).strip() in ("", "?", "None", "null"):
        return "—"
    s = str(val).strip()
    # ISO timestamp: 2026-02-12T10:58:53.000Z → 12/02/2026
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s[:26], fmt)
            return dt.strftime("%d/%m/%Y")
        except ValueError:
            continue
    return s

def _safe_int(val, default=0) -> int:
    """Converte valor pra int de forma segura. Databricks retorna strings."""
    if val is None:
        return default
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default


# Alias público pra uso externo (handlers.py, daily.py)
fmt_date = _fmt_date
safe_int = _safe_int


def _fmt_datetime(val) -> str:
    """Formata timestamp para DD/MM/YYYY às HHhMM."""
    if not val or str(val).strip() in ("", "?", "None", "null"):
        return "—"
    s = str(val).strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(s[:26], fmt)
            return dt.strftime("%d/%m/%Y às %Hh%M")
        except ValueError:
            continue
    # Fallback: se for só data
    return _fmt_date(val)


def fmt_number(n) -> str:
    """Formata número com separador de milhar."""
    try:
        n = float(n)
        if n >= 1_000_000:
            return f"{n / 1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n / 1_000:.1f}K"
        if n == int(n):
            return f"{int(n):,}".replace(",", ".")
        return f"{n:.2f}"
    except (ValueError, TypeError):
        return str(n) if n else "—"


def fmt_pct(n) -> str:
    """Formata percentual."""
    try:
        return f"{float(n):.1f}%"
    except (ValueError, TypeError):
        return "—"


def fmt_table(data: dict, max_rows: int = 20) -> str:
    """Formata resultado SQL como tabela Slack (monospace)."""
    if not data.get("rows"):
        return "_Nenhum dado encontrado._"

    cols = data["columns"]
    rows = data["rows"][:max_rows]

    header_line = " | ".join(str(c) for c in cols)
    sep_line = "-+-".join("-" * max(len(str(c)), 6) for c in cols)
    data_lines = []
    for row in rows:
        data_lines.append(" | ".join(str(v) if v is not None else "—" for v in row))

    return f"```\n{header_line}\n{sep_line}\n" + "\n".join(data_lines) + "\n```"


def channel_pill(db_channel: str) -> str:
    """Retorna emoji + nome amigável do canal."""
    emoji = CHANNEL_EMOJI.get(db_channel, "📨")
    name = CHANNEL_DISPLAY_NAME.get(db_channel, db_channel)
    return f"{emoji} {name}"


def monday_channels_summary(subitems: list[dict]) -> str:
    """Gera resumo dos canais a partir dos subitems do Monday."""
    if not subitems:
        return "_Sem touchpoints cadastrados._"

    channels = {}
    for si in subitems:
        label = (si.get("channel_label") or "").strip()
        if label in SKIP_CHANNEL_LABELS:
            continue
        db_ch = CHANNEL_MONDAY_TO_DB.get(label)
        if not db_ch:
            continue
        if db_ch not in channels:
            channels[db_ch] = {"labels": set(), "dates": [], "count": 0}
        channels[db_ch]["labels"].add(label)
        channels[db_ch]["count"] += 1
        dt = si.get("touch_date", "")
        if dt:
            channels[db_ch]["dates"].append(dt)

    if not channels:
        return "_Nenhum canal válido nos subitems._"

    lines = []
    for db_ch, info in sorted(channels.items()):
        pill = channel_pill(db_ch)
        variants = ", ".join(sorted(info["labels"]))
        dates_str = ""
        if info["dates"]:
            dates_sorted = sorted(set(info["dates"]))
            formatted_dates = [_fmt_date(d) for d in dates_sorted]
            dates_str = f" ({', '.join(formatted_dates)})"
        reportable = "✅" if db_ch in REPORTABLE_DB_CHANNELS else "⏳"
        lines.append(f"{pill} × {info['count']}  [{variants}]{dates_str} {reportable}")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════
# Block Kit primitives
# ═══════════════════════════════════════════════════════════

def section(text: str) -> dict:
    return {"type": "section", "text": {"type": "mrkdwn", "text": text}}


def header(text: str) -> dict:
    return {"type": "header", "text": {"type": "plain_text", "text": text, "emoji": True}}


def divider() -> dict:
    return {"type": "divider"}


def context(text: str) -> dict:
    return {"type": "context", "elements": [{"type": "mrkdwn", "text": text}]}


# ═══════════════════════════════════════════════════════════
# Botões de interação
# ═══════════════════════════════════════════════════════════

def actions_delivery_choice(callback_id: str) -> dict:
    return {
        "type": "actions",
        "block_id": f"delivery_{callback_id}",
        "elements": [
            {"type": "button", "text": {"type": "plain_text", "text": "📢 No canal"}, "action_id": "deliver_channel", "value": callback_id},
            {"type": "button", "text": {"type": "plain_text", "text": "🔒 Na DM"}, "action_id": "deliver_dm", "value": callback_id},
            {"type": "button", "text": {"type": "plain_text", "text": "📢🔒 Ambos"}, "action_id": "deliver_both", "value": callback_id},
        ],
    }


def actions_history_choice(callback_id: str, area: str = "") -> dict:
    return {
        "type": "actions",
        "block_id": f"history_{callback_id}",
        "elements": [
            {"type": "button", "text": {"type": "plain_text", "text": "🔎 Ver histórico completo (YTD)"}, "action_id": "status_full_history", "value": area or "", "style": "primary"},
        ],
    }


# ═══════════════════════════════════════════════════════════
# Format — Status
# ═══════════════════════════════════════════════════════════

def format_status_summary(summary: dict, area: str = None, mtd: bool = True) -> list[dict]:
    """Mantido por compatibilidade. Usa format_macro_campanha internamente."""
    return format_macro_campanha(summary, area=area, mtd=mtd)


def format_macro_campanha(summary: dict, area: str = None, mtd: bool = True) -> list[dict]:
    """Visão macro do pipeline: status + breakdown CRM + alertas de bloqueio."""
    period = "Mês atual" if mtd else "Histórico completo"
    title = f"📊 Campanhas — {period}" + (f" | {area}" if area else " | Todas as áreas")

    by_status = summary.get("by_status", summary)  # retrocompat: summary pode ser dict direto
    by_crm    = summary.get("by_crm", {})
    blocked   = summary.get("blocked", [])
    total     = summary.get("total", sum(by_status.values()))

    # ── Pipeline por status ──────────────────────────────
    STATUS_META = [
        ("priorizad",  "🟢", "Priorizadas"),
        ("backlog",    "🟡", "Backlog"),
        ("concluíd",   "🟢", "Concluídas"),
        ("concluido",  "🟢", "Concluídas"),
        ("teste tcpg", "🟠", "Em teste LIFT"),
        ("reprovad",   "🔴", "Reprovadas"),
    ]

    status_lines = []
    for raw_status, count in sorted(by_status.items(), key=lambda x: -x[1]):
        emoji, label = "⬜", raw_status
        for key, e, lbl in STATUS_META:
            if key in raw_status.lower():
                emoji, label = e, lbl
                break
        pct = count * 100 / total if total else 0
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        status_lines.append(f"{emoji} *{label}*: {count} ({pct:.0f}%) `{bar}`")

    blocks = [
        header(title),
        section("\n".join(status_lines) if status_lines else "_Nenhuma campanha no período._"),
        context(f"Total: {total} campanhas · _Fonte: Monday.com_"),
        divider(),
    ]

    # ── Breakdown CRM (só se tem priorizadas) ───────────
    if by_crm:
        CRM_META = {
            "abrir briefing":   ("📝", "Abrir Briefing"),
            "montar segmento":  ("🟡", "Montar Segmento"),
            "montar jornada":   ("🟡", "Montar Jornada"),
            "testes":           ("🟠", "Testes"),
            "em finaliz":       ("🟠", "Em Finalização"),
            "feito":            ("🟢", "Feito"),
            "appsheet":         ("🟠", "AppSheet"),
            "com impedit":      ("🔴", "Com Impedimento"),
            "com impedim":      ("🔴", "Com Impedimento"),
        }

        crm_lines = []
        for crm_status, count in sorted(by_crm.items(), key=lambda x: -x[1]):
            emoji, label = "⬜", crm_status
            for key, e, lbl in CRM_META.items():
                if key in crm_status.lower():
                    emoji, label = e, lbl
                    break
            crm_lines.append(f"{emoji} *{label}*: {count}")

        blocks.append(section("*🔄 Breakdown CRM (campanhas priorizadas)*\n" + "\n".join(crm_lines)))
        blocks.append(divider())

    # ── Alertas de bloqueio ──────────────────────────────
    if blocked:
        bloq_lines = []
        for c in blocked[:5]:
            bid = str(c.get("numeric_mkvccc73", "")).strip()
            raw_name = c.get("name", "?")
            nome = parse_campaign_name(raw_name, bid) if bid else raw_name
            owner = c.get("person") or "sem responsável"
            bloq_lines.append(f"• *{nome}* — Com Impedimento\n  Responsável: {owner}")

        blocks.append(section("*🔴 Campanhas bloqueadas:*\n" + "\n".join(bloq_lines)))
        blocks.append(divider())

    return blocks


def format_micro_monday(campaign: dict) -> list[dict]:
    """Visão micro de campanha ainda em planejamento/execução (Backlog ou Priorizada).
    Fonte: Monday — retorna status operacional."""
    bid = str(campaign.get("numeric_mkvccc73", "")).strip()
    raw_name = campaign.get("name", "?")
    nome = parse_campaign_name(raw_name, bid) if bid else raw_name

    status_camp = campaign.get("status", "") or ""
    status_crm  = campaign.get("color_mky1jm7j", "") or ""
    etapa_txt   = traduzir_etapa(status_camp, status_crm)
    barra       = progresso_crm(status_crm)

    area    = campaign.get("color_mkv9c29w") or "?"
    produto = campaign.get("color_mkv95cyj") or "?"
    dt_ini  = _fmt_date(campaign.get("date_mkv87hhf"))
    owner   = campaign.get("person") or "Sem responsável"

    vol_sf  = campaign.get("numeric_mkynfjpx", "")
    vol_est = campaign.get("numeric_mkvn5qpc", "")
    vol_val = fmt_number(vol_sf) if vol_sf else fmt_number(vol_est)
    vol_lbl = "Clientes SF" if vol_sf else "Vol. estimado"

    lines = [
        f"*📋 {nome}*",
        f"├ Etapa: {etapa_txt}",
    ]
    if barra:
        lines.append(f"├ Progresso CRM: {barra}")
    lines += [
        f"├ Área: {area}  ·  Produto: {produto}",
        f"├ Início previsto: *{dt_ini}*",
        f"├ {vol_lbl}: *{vol_val}*",
        f"└ Responsável: {owner}",
    ]

    # Touchpoints se disponíveis
    subitems = campaign.get("subitems", [])
    blocks = [
        header(f"📋 {nome}"),
        section("\n".join(lines)),
    ]

    if subitems:
        blocks.append(section(
            f"*🎯 Touchpoints ({len(subitems)})*\n"
            f"{monday_channels_summary(subitems)}"
        ))

    blocks += [
        divider(),
        context(f"_Fonte: Monday.com · Briefing {bid}_"),
    ]
    return blocks


def format_micro_databricks(campaign: dict, db_data: dict, allowed_channels: set = None) -> list[dict]:
    """Visão micro de campanha já disparada (Concluída).
    Fonte: Databricks — retorna métricas de performance."""
    bid = str(campaign.get("numeric_mkvccc73", "")).strip() if campaign else ""
    if campaign:
        raw_name = campaign.get("name", "?")
        nome = parse_campaign_name(raw_name, bid) if bid else raw_name
        area    = campaign.get("color_mkv9c29w") or "?"
        produto = campaign.get("color_mkv95cyj") or "?"
    else:
        nome    = f"Briefing {bid}"
        area    = "?"
        produto = "?"

    blocks = [header(f"📊 {nome}")]

    # ── Marcação (grupos) ────────────────────────────────
    marc = db_data.get("marcacao", {})
    if marc.get("rows"):
        cols = marc["columns"]
        grupos = {}
        for row in marc["rows"]:
            r = dict(zip(cols, row))
            group = r.get("group_type", "?")
            ch    = r.get("properties_channel", "")
            consumers = _safe_int(r.get("unique_consumers"))
            # Agrupa por grupo_type somando consumers
            key = ch if ch in _LIFT_MARKERS else group
            grupos[key] = grupos.get(key, 0) + consumers

        group_lines = []
        for key, total_c in grupos.items():
            if key in _LIFT_MARKERS:
                e, lbl = _LIFT_MARKER_LABELS_FULL.get(key, ("🧪", key))
            else:
                e, lbl = _GROUP_LABELS.get(key, ("⬜", key))
            group_lines.append(f"{e} *{lbl}*: {fmt_number(total_c)} clientes")

        blocks.append(section("*🏷️ Distribuição de grupos*\n" + "\n".join(group_lines)))

    # ── Disparo por canal ────────────────────────────────
    disp = db_data.get("disparo", {})
    if disp.get("rows"):
        cols = disp["columns"]
        for row in disp["rows"]:
            r = dict(zip(cols, row))
            channel = r.get("channel", "?")
            if allowed_channels and channel not in allowed_channels:
                continue
            if channel not in REPORTABLE_DB_CHANNELS:
                continue

            sent       = _safe_int(r.get("total_sent"))
            delivered  = _safe_int(r.get("delivered"))
            opened_7d  = _safe_int(r.get("opened_7d"))
            clicked_7d = _safe_int(r.get("clicked_7d"))

            del_rate  = delivered  / sent      * 100 if sent      else 0
            open_rate = opened_7d  / delivered * 100 if delivered else 0
            ctr       = clicked_7d / delivered * 100 if delivered else 0
            ctor      = clicked_7d / opened_7d * 100 if opened_7d else 0

            send_date  = _fmt_date(r.get("send_date"))
            first_sent = _fmt_datetime(r.get("first_sent"))
            hora = first_sent.split("às ")[-1] if "às" in first_sent else ""
            date_label = f"{send_date} · {hora}" if hora else send_date
            pill = channel_pill(channel)

            # Indicadores visuais
            del_ind  = "🟢" if del_rate  >= 95 else ("🟡" if del_rate  >= 85 else "🔴")
            open_ind = "🟢" if open_rate >= 15 else ("🟡" if open_rate >= 8  else "🔴")
            ctr_ind  = "🟢" if ctr       >= 1  else ("🟡" if ctr       >= 0.3 else "🔴")

            lines = [
                f"*{pill}*",
                f"📅 Disparo: *{date_label}*",
                f"📤 Enviados: *{fmt_number(sent)}*  •  Entregues: *{fmt_number(delivered)}* {del_ind} {fmt_pct(del_rate)}",
            ]
            if channel not in CHANNELS_NO_OPEN:
                lines.append(f"👁️ Abertura (OR 7d): *{fmt_number(opened_7d)}* {open_ind} *{fmt_pct(open_rate)}*")
            if channel not in CHANNELS_NO_CLICK:
                lines.append(f"🖱️ Clique CTR (7d): *{fmt_number(clicked_7d)}* {ctr_ind} *{fmt_pct(ctr)}*  •  CTOR: *{fmt_pct(ctor)}*")
            else:
                lines.append(f"🖱️ Clique: _sem tracking para este canal_")

            blocks.append(section("\n".join(lines)))

    # ── LIFT ────────────────────────────────────────────
    lift = db_data.get("lift", {})
    if lift.get("rows"):
        cols = lift["columns"]
        r    = dict(zip(cols, lift["rows"][0]))
        result = r.get("final_result") or "Rodando"
        emoji  = "✅" if "aprov" in str(result).lower() else ("❌" if "reprov" in str(result).lower() else "🔄")
        pv     = r.get("p_value", "—")
        inc    = r.get("incremental", "—")
        blocks.append(section(
            f"*🧪 Teste LIFT*\n"
            f"├ Resultado: {emoji} *{result}*\n"
            f"├ p-value: *{pv}*\n"
            f"└ Incrementalidade: *{inc}*"
        ))

    blocks += [
        divider(),
        context(f"_Área: {area} · Produto: {produto} · Fonte: Databricks · Briefing {bid}_"),
    ]
    return blocks


# ═══════════════════════════════════════════════════════════
# Format — Top Campanhas (VISUAL)
# ═══════════════════════════════════════════════════════════

def format_top_campaigns(data: dict, area: str = None) -> list[dict]:
    """Ranking visual de campanhas — 1 linha por campanha, consolidado de todos os canais."""
    title = "🏆 Top Campanhas" + (f" — {area}" if area else "") + " (últimos 30 dias)"
    blocks = [header(title)]

    if not data.get("rows"):
        blocks.append(section("_Nenhuma campanha com volume suficiente no período._"))
        blocks.append(divider())
        return blocks

    cols = data["columns"]
    for i, row in enumerate(data["rows"], 1):
        r = dict(zip(cols, row))
        medal = _MEDAL.get(i, f"*{i}º*")

        # Nome da campanha: tentar nome do Monday (se enriquecido) ou product_category
        nome_raw = r.get("nome_campanha") or ""
        monday_name = r.get("monday_name") or ""
        produto = r.get("produto") or "Produto não identificado"
        bu = _BU_SHORT.get(r.get("area", ""), r.get("area", "?"))
        bid = r.get("briefing_id", "?")

        # Prioridade: 1) nome do Monday (parseado), 2) product_category do Databricks
        if monday_name:
            nome_display = parse_campaign_name(monday_name, bid)
        else:
            nome_display = produto

        entregues = fmt_number(r.get("entregues", 0))
        clientes = fmt_number(r.get("clientes_impactados", 0))
        abertura = fmt_pct(r.get("taxa_abertura", 0))
        clique = fmt_pct(r.get("taxa_clique", 0))
        qtd_canais = r.get("qtd_canais", "?")
        primeiro = _fmt_date(r.get("primeiro_disparo"))
        ultimo = _fmt_date(r.get("ultimo_disparo"))

        # Período de disparo
        if primeiro and primeiro != "—" and ultimo and ultimo != "—" and primeiro != ultimo:
            periodo = f"{primeiro} → {ultimo}"
        elif primeiro and primeiro != "—":
            periodo = str(primeiro)
        else:
            periodo = "—"

        blocks.append(section(
            f"{medal}  *{nome_display}* ({bu})\n"
            f"      📅 Período: {periodo} · {qtd_canais} canais\n"
            f"      👥 Clientes: *{clientes}* · Entregues: *{entregues}*\n"
            f"      📬 Abertura: *{abertura}* · Clique: *{clique}*\n"
            f"      _Briefing: {bid}_"
        ))

    blocks.append(divider())
    blocks.append(context("_Ordenado por taxa de abertura. Mínimo 1K entregues. Últimos 30 dias. Fonte: Databricks (disparo)_"))
    return blocks


# ═══════════════════════════════════════════════════════════
# Format — Top Canais (VISUAL)
# ═══════════════════════════════════════════════════════════

def format_top_channels(data: dict, area: str = None) -> list[dict]:
    """Ranking visual de canais de disparo."""
    title = "📡 Ranking de Canais" + (f" — {area}" if area else "") + " (últimos 30 dias)"
    blocks = [header(title)]

    if not data.get("rows"):
        blocks.append(section("_Sem dados de disparo no período._"))
        return blocks

    cols = data["columns"]
    for i, row in enumerate(data["rows"], 1):
        r = dict(zip(cols, row))
        medal = _MEDAL.get(i, f"*{i}º*")
        canal = channel_pill(r.get("channel", "?"))
        entregues = fmt_number(r.get("entregues", 0))
        abertura = fmt_pct(r.get("taxa_abertura", 0))
        clique = fmt_pct(r.get("taxa_clique", 0))
        campanhas = r.get("campanhas", "?")
        entrega = fmt_pct(r.get("taxa_entrega", 0))

        abertura_line = f" · Abertura: *{abertura}*" if r.get("channel") not in CHANNELS_NO_OPEN else ""
        clique_line = f" · Clique: *{clique}*" if r.get("channel") not in CHANNELS_NO_CLICK else ""

        blocks.append(section(
            f"{medal}  {canal}\n"
            f"      Entregues: *{entregues}* (taxa {entrega}){abertura_line}{clique_line}\n"
            f"      _{campanhas} campanhas no período_"
        ))

    blocks.append(divider())
    blocks.append(context("_Ordenado por volume de entrega. Últimos 30 dias. Fonte: Databricks (disparo)_"))
    return blocks


# ═══════════════════════════════════════════════════════════
# Format — Top Produtos (VISUAL)
# ═══════════════════════════════════════════════════════════

def format_top_products(data: dict, area: str = None) -> list[dict]:
    """Ranking visual de produtos."""
    title = "📦 Ranking de Produtos" + (f" — {area}" if area else "") + " (últimos 30 dias)"
    blocks = [header(title)]

    if not data.get("rows"):
        blocks.append(section("_Sem dados no período._"))
        return blocks

    cols = data["columns"]
    for i, row in enumerate(data["rows"], 1):
        r = dict(zip(cols, row))
        medal = _MEDAL.get(i, f"*{i}º*")
        produto = r.get("product_category") or "Não identificado"
        bu = _BU_SHORT.get(r.get("bu_requester", ""), r.get("bu_requester", "?"))
        entregues = fmt_number(r.get("entregues", 0))
        abertura = fmt_pct(r.get("taxa_abertura", 0))
        clique = fmt_pct(r.get("taxa_clique", 0))
        campanhas = r.get("campanhas", "?")

        blocks.append(section(
            f"{medal}  *{produto}* ({bu})\n"
            f"      Entregues: *{entregues}* · Abertura: *{abertura}* · Clique: *{clique}*\n"
            f"      _{campanhas} campanhas_"
        ))

    blocks.append(divider())
    blocks.append(context("_Ordenado por volume. Mínimo 1K entregues. Últimos 30 dias. Taxas consolidam todos os canais. Fonte: Databricks (disparo)_"))
    return blocks


# ═══════════════════════════════════════════════════════════
# Format — Top Horários (VISUAL)
# ═══════════════════════════════════════════════════════════

def format_top_hours(data: dict, area: str = None) -> list[dict]:
    """Ranking visual de horários de envio."""
    title = "🕐 Melhores Horários de Envio" + (f" — {area}" if area else "") + " (últimos 30 dias)"
    blocks = [header(title)]

    if not data.get("rows"):
        blocks.append(section("_Sem dados no período._"))
        return blocks

    cols = data["columns"]
    for i, row in enumerate(data["rows"][:10], 1):
        r = dict(zip(cols, row))
        medal = _MEDAL.get(i, f"*{i}º*")
        hora = int(r.get("hora", 0))
        hora_str = f"{hora:02d}h"
        entregues = fmt_number(r.get("entregues", 0))
        abertura = fmt_pct(r.get("taxa_abertura", 0))
        clique = fmt_pct(r.get("taxa_clique", 0))

        # Barra visual proporcional
        try:
            pct = float(r.get("taxa_abertura", 0))
            bar_len = int(pct / 3)  # ~33% = barra cheia
            bar = "█" * bar_len + "░" * (10 - bar_len)
        except (ValueError, TypeError):
            bar = "░" * 10

        blocks.append(section(
            f"{medal}  *{hora_str}* `{bar}` Abertura: *{abertura}* · Clique: *{clique}*\n"
            f"      _Volume: {entregues} entregues_"
        ))

    blocks.append(divider())
    blocks.append(context("_Ordenado por taxa de abertura. Últimos 30 dias. Taxas consolidam todos os canais. Fonte: Databricks (disparo)_"))
    return blocks


# ═══════════════════════════════════════════════════════════
# Format — Disparo (com regras INAPP)
# ═══════════════════════════════════════════════════════════

def format_dispatch_stats(data: dict, briefing_id: str, allowed_channels: set = None) -> list[dict]:
    blocks = [header(f"📬 Disparo — Briefing {briefing_id}")]

    if not data.get("rows"):
        blocks.append(section("_Nenhum disparo encontrado para este briefing._"))
        return blocks

    cols = data["columns"]
    for row in data["rows"]:
        r = dict(zip(cols, row))
        channel = r.get("channel", "?")

        if allowed_channels and channel not in allowed_channels:
            continue
        if channel not in REPORTABLE_DB_CHANNELS:
            continue

        sent = _safe_int(r.get("total_sent"))
        delivered = _safe_int(r.get("delivered"))
        opened = _safe_int(r.get("opened"))
        clicked = _safe_int(r.get("clicked"))

        del_rate = delivered / sent * 100 if sent else 0
        open_rate = opened / delivered * 100 if delivered else 0
        ctr = clicked / delivered * 100 if delivered else 0

        pill = channel_pill(channel)
        lines = [
            f"{pill}",
            f"├ Enviados: *{fmt_number(sent)}*",
            f"├ Entregues: *{fmt_number(delivered)}* ({fmt_pct(del_rate)})",
        ]

        if channel not in CHANNELS_NO_OPEN:
            lines.append(f"├ Abertos: *{fmt_number(opened)}* ({fmt_pct(open_rate)})")
        else:
            lines.append(f"├ Abertos: _sem tracking_")

        if channel not in CHANNELS_NO_CLICK:
            lines.append(f"└ Clicados: *{fmt_number(clicked)}* ({fmt_pct(ctr)})")
        else:
            lines.append(f"└ Clicados: _sem tracking_")

        opened_7d = _safe_int(r.get("opened_7d"))
        clicked_7d = _safe_int(r.get("clicked_7d"))
        if opened_7d or clicked_7d:
            lines.append(f"  _Janela 7d: {fmt_number(opened_7d)} aberturas, {fmt_number(clicked_7d)} cliques_")

        blocks.append(section("\n".join(lines)))

    if data["rows"]:
        first_row = dict(zip(cols, data["rows"][0]))
        first_sent = _fmt_datetime(first_row.get("first_sent"))
        last_sent = _fmt_datetime(first_row.get("last_sent"))
        blocks.append(context(f"Primeiro envio: {first_sent} | Último envio: {last_sent}"))

    blocks.append(context("_Fonte: Databricks (disparo)_"))
    blocks.append(divider())
    return blocks


# ═══════════════════════════════════════════════════════════
# Format — LIFT
# ═══════════════════════════════════════════════════════════

def format_lift_results(data: dict) -> list[dict]:
    blocks = [header("🔬 Resultados LIFT")]

    if not data.get("rows"):
        blocks.append(section("_Nenhum teste LIFT encontrado._"))
        return blocks

    for row in data["rows"]:
        cols = data["columns"]
        r = dict(zip(cols, row))

        result = r.get("final_result", "?")
        is_aprovado  = "aprov" in str(result).lower()
        is_reprovado = "reprov" in str(result).lower()
        result_emoji = "🟢" if is_aprovado else ("🔴" if is_reprovado else "🟠")
        result_label = "Aprovado" if is_aprovado else ("Reprovado" if is_reprovado else "Em análise")

        try:
            pv = float(r.get("p_value", 1))
            pv_emoji = "🟢" if pv < 0.05 else "🔴"
            pv_label  = "significativo ✓" if pv < 0.05 else "não significativo"
        except (ValueError, TypeError):
            pv_emoji, pv_label = "⚪", "sem dado"

        bid = r.get("briefing_id", "?")
        monday_name = r.get("monday_name") or ""
        campaign_label = parse_campaign_name(monday_name, bid) if monday_name else f"Briefing {bid}"

        sent_dt   = _fmt_date(r.get("sent"))
        approv_dt = _fmt_date(r.get("aprovation_date"))

        treat = fmt_number(r.get("treatment_audience", 0))
        ctrl  = fmt_number(r.get("gc_audience", 0))

        # Incrementalidade — formatar como % se for decimal pequeno, número se for grande
        inc_raw = r.get("incremental", None)
        try:
            inc_val = float(inc_raw)
            inc_str = f"{inc_val:+.2f}" if abs(inc_val) < 100 else fmt_number(inc_val)
        except (ValueError, TypeError):
            inc_str = "—"

        pv_raw = r.get("p_value", "—")
        try:
            pv_str = f"{float(pv_raw):.3f}"
        except (ValueError, TypeError):
            pv_str = "—"

        blocks.append(section(
            f"{result_emoji} *{campaign_label}*\n"
            f"📋 Briefing: `{bid}`  •  📅 Envio: *{sent_dt}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 Tratamento: *{treat} clientes*  •  Controle: *{ctrl} clientes*\n"
            f"📈 Incrementalidade: *{inc_str}*\n"
            f"{pv_emoji} p-value: *{pv_str}* — _{pv_label}_\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Resultado: {result_emoji} *{result_label}*"
            + (f"  •  Aprovado em: {approv_dt}" if approv_dt and approv_dt != "—" else "")
        ))

    blocks.append(divider())
    blocks.append(context("_Fonte: Databricks (resultados LIFT)_"))
    return blocks


# ═══════════════════════════════════════════════════════════
# Format — Marcação (visual, não tabela crua)
# ═══════════════════════════════════════════════════════════

_GROUP_LABELS = {
    "GT": ("🟢", "Grupo Tratamento"),
    "GC": ("🔵", "Grupo Controle"),
    "GCU": ("🟣", "Controle Universal"),
    "ENG": ("🟡", "Engajamento"),
    "EXP_ADHOC": ("🧪", "Tratamento LIFT"),
    "EXP_ADHOC_GC": ("🧪", "Controle LIFT"),
    "EXP_ADHOC_WAIT": ("⏳", "Espera LIFT"),
    "NBO": ("📩", "NBO"),
}

_CHANNEL_LABELS = {
    "MARC": "Marcação",
    "GC": "Controle",
    "GI": "Marcação",
}

# Marcadores de experimento LIFT na marcação
_LIFT_MARKERS = {"EXP_ADHOC", "EXP_ADHOC_GC", "EXP_ADHOC_WAIT"}

_LIFT_MARKER_LABELS = {
    "EXP_ADHOC": "🧪 Tratamento",
    "EXP_ADHOC_GC": "🧪 Controle",
    "EXP_ADHOC_WAIT": "⏳ Espera",
}

_LIFT_MARKER_LABELS_FULL = {
    "EXP_ADHOC": ("🧪", "Teste LIFT — Tratamento"),
    "EXP_ADHOC_GC": ("🧪", "Teste LIFT — Controle"),
    "EXP_ADHOC_WAIT": ("⏳", "Teste LIFT — Espera (liberado se aprovado)"),
}


def _detect_lift_markers(marc_data: dict) -> list[str]:
    """Detecta se a marcação contém grupos de teste LIFT.
    
    Verifica tanto properties_channel quanto group_type, pois os marcadores
    de LIFT aparecem como properties_channel (EXP_ADHOC, EXP_ADHOC_GC, EXP_ADHOC_WAIT).
    
    Retorna lista de marcadores LIFT encontrados com labels legíveis, ou lista vazia.
    """
    if not marc_data or not marc_data.get("rows"):
        return []
    
    cols = marc_data.get("columns", [])
    found = set()
    
    # Checar em todas as colunas relevantes
    for col_name in ("properties_channel", "group_type"):
        if col_name not in cols:
            continue
        idx = cols.index(col_name)
        for row in marc_data["rows"]:
            val = str(row[idx]).strip()
            if val in _LIFT_MARKERS:
                found.add(val)
    
    return [_LIFT_MARKER_LABELS.get(m, m) for m in sorted(found)]


def _format_marcacao_visual(data: dict) -> list[dict]:
    """Formata dados de marcação como blocos visuais legíveis."""
    if not data.get("rows"):
        return [section("_Sem dados de marcação._")]

    cols = data["columns"]
    blocks = []
    for row in data["rows"]:
        r = dict(zip(cols, row))
        group = r.get("group_type", "?")
        channel = r.get("properties_channel", "?")
        total = _safe_int(r.get("total_marcacoes"))
        consumers = _safe_int(r.get("unique_consumers"))
        first_dt = _fmt_date(r.get("first_date"))
        last_dt = _fmt_date(r.get("last_date"))

        # O label principal vem do properties_channel se for marcador de LIFT,
        # senão do group_type
        if channel in _LIFT_MARKERS:
            emoji, label = _LIFT_MARKER_LABELS_FULL.get(channel, ("🧪", channel))
        else:
            emoji, label = _GROUP_LABELS.get(group, ("⬜", group))
        
        ch_label = _CHANNEL_LABELS.get(channel, channel)
        
        # Se for marcador LIFT, não mostrar channel label redundante
        if channel in _LIFT_MARKERS:
            header_text = f"{emoji} *{label}*"
        else:
            header_text = f"{emoji} *{label}* ({ch_label})"

        periodo = f"{first_dt} → {last_dt}" if first_dt != last_dt else first_dt

        blocks.append(section(
            f"{header_text}\n"
            f"├ Clientes únicos: *{fmt_number(consumers)}*\n"
            f"├ Total marcações: *{fmt_number(total)}*\n"
            f"└ Período: {periodo}"
        ))

    return blocks


# ═══════════════════════════════════════════════════════════
# Format — Debug Completo
# ═══════════════════════════════════════════════════════════
# Format — SLA CRM
# ═══════════════════════════════════════════════════════════

def format_sla_report(sla_data: dict, area: str = None) -> list[dict]:
    """Relatório visual de campanhas fora do SLA ou em risco."""
    from parsers import parse_campaign_name as _parse_name

    title = "⏰ SLA CRM" + (f" — {area}" if area else "")
    blocks = [header(title)]

    vencidas = sla_data.get("vencidas", [])
    em_risco = sla_data.get("em_risco", [])

    if not vencidas and not em_risco:
        blocks.append(section("✅ _Todas as campanhas em Backlog estão dentro do SLA. Nenhum atraso._"))
        blocks.append(context("_SLA CRM: avançar campanha até 4 dias antes da Dt Início. Fonte: Monday.com_"))
        return blocks

    # Vencidas (🔴)
    if vencidas:
        blocks.append(section(f"*🔴 Fora do SLA ({len(vencidas)})*"))
        for c in vencidas:
            bid = str(c.get("numeric_mkvccc73", "")).strip()
            raw_name = c.get("name", "?")
            nome = _parse_name(raw_name, bid) if bid else raw_name
            dt_inicio = c.get("_dt_inicio")
            dias = abs(c.get("_dias_restantes_sla", 0))
            owner = c.get("person") or "sem responsável"
            area_camp = c.get("color_mkv9c29w") or ""
            produto = c.get("color_mkv95cyj") or ""

            dt_fmt = _fmt_date(str(dt_inicio)) if dt_inicio else "?"

            blocks.append(section(
                f"🔴 *{nome}*\n"
                f"├ Disparo previsto: *{dt_fmt}*\n"
                f"├ SLA vencido há *{dias} dia(s)*\n"
                f"├ Responsável: {owner}\n"
                f"├ Área: {area_camp}"
                + (f" · Produto: {produto}" if produto else "") +
                f"\n└ _Briefing: {bid}_"
            ))

    # Em risco (🟡)
    if em_risco:
        blocks.append(section(f"*⚠️ Próximo do vencimento ({len(em_risco)})*"))
        for c in em_risco:
            bid = str(c.get("numeric_mkvccc73", "")).strip()
            raw_name = c.get("name", "?")
            nome = _parse_name(raw_name, bid) if bid else raw_name
            dt_inicio = c.get("_dt_inicio")
            dias = c.get("_dias_restantes_sla", 0)
            owner = c.get("person") or "sem responsável"
            area_camp = c.get("color_mkv9c29w") or ""

            dt_fmt = _fmt_date(str(dt_inicio)) if dt_inicio else "?"

            if dias == 0:
                urgencia = "vence *hoje*"
            elif dias == 1:
                urgencia = "vence *amanhã*"
            else:
                urgencia = f"vence em *{dias} dias*"

            blocks.append(section(
                f"🟡 *{nome}*\n"
                f"├ Disparo previsto: *{dt_fmt}*\n"
                f"├ SLA {urgencia}\n"
                f"├ Responsável: {owner}\n"
                f"└ _Briefing: {bid}_"
            ))

    # Resumo
    blocks.append(divider())
    total = len(vencidas) + len(em_risco)
    blocks.append(context(
        f"_{total} campanha(s) precisam de atenção. "
        f"SLA CRM: avançar até 4 dias antes do disparo. Fonte: Monday.com_"
    ))
    return blocks


# ═══════════════════════════════════════════════════════════
# Format — Debug Campanha Completo
# ═══════════════════════════════════════════════════════════

def format_campaign_debug(
    briefing_id: str,
    monday_data: dict,
    db_data: dict,
    allowed_channels: set = None,
) -> list[dict]:
    # Try to get a clean name for the header
    if monday_data:
        raw_name = monday_data.get('name', '')
        bid_str = str(monday_data.get('numeric_mkvccc73', '')).strip()
        header_name = parse_campaign_name(raw_name, bid_str if bid_str else briefing_id)
    else:
        header_name = None

    if header_name:
        blocks = [header(f"🔍 {header_name}")]
    else:
        blocks = [header(f"🔍 Campanha — Briefing {briefing_id}")]

    if monday_data:
        vol_sf = monday_data.get("numeric_mkynfjpx", "")
        vol_est = monday_data.get("numeric_mkvn5qpc", "")
        vol_display = fmt_number(vol_sf) if vol_sf else fmt_number(vol_est)
        vol_label = "Clientes SF" if vol_sf else "Estimado"

        # Parse clean campaign name
        raw_name = monday_data.get('name', '?')
        bid_str = str(monday_data.get('numeric_mkvccc73', '')).strip()
        clean_name = parse_campaign_name(raw_name, bid_str if bid_str else briefing_id)

        start_date = _fmt_date(monday_data.get('date_mkv87hhf'))
        status_crm_raw = monday_data.get('color_mky1jm7j', '')
        etapa_txt = traduzir_etapa(monday_data.get('status', ''), status_crm_raw)
        barra = progresso_crm(status_crm_raw)
        etapa_line = f"├ Etapa: {etapa_txt}"
        if barra:
            etapa_line += f"\n├ Progresso CRM: {barra}"

        blocks.append(section(
            f"*📋 Informações (Monday)*\n"
            f"├ Nome: *{clean_name}*\n"
            f"{etapa_line}\n"
            f"├ Área: {monday_data.get('color_mkv9c29w') or '?'}\n"
            f"├ Produto: {monday_data.get('color_mkv95cyj') or '?'}\n"
            f"├ Início: *{start_date}*\n"
            f"├ {vol_label}: *{vol_display}*\n"
            f"└ Qtd GT: {monday_data.get('numeric_mkv99sgg') or '?'}"
        ))

        subitems = monday_data.get("subitems", [])
        if subitems:
            blocks.append(section(
                f"*🎯 Touchpoints ({len(subitems)})*\n"
                f"{monday_channels_summary(subitems)}"
            ))

            touch_lines = []
            for si in sorted(subitems, key=lambda s: (s.get("touch_date") or "", s.get("sequence") or "")):
                label = (si.get("channel_label") or "").strip()
                if label in SKIP_CHANNEL_LABELS:
                    continue
                seq = si.get("sequence") or "?"
                dt = si.get("touch_date") or "sem data"
                st = si.get("touch_status") or "sem status"
                # Formatar data se vier no formato ISO
                dt = _fmt_date(dt) if dt != "sem data" else dt
                touch_lines.append(f"  T{seq}: {label} — {dt} ({st})")

            if touch_lines:
                blocks.append(section(
                    "*📅 Janelas de disparo*\n" + "\n".join(touch_lines[:20])
                ))

        blocks.append(divider())
    else:
        blocks.append(section("_⚠️ Campanha não encontrada no Monday._"))

    marc = db_data.get("marcacao", {})
    if marc.get("rows"):
        blocks.append(section("*🏷️ Marcação*"))
        blocks.extend(_format_marcacao_visual(marc))
    else:
        blocks.append(section("_🏷️ Sem dados de marcação._"))

    blocks.extend(format_dispatch_stats(
        db_data.get("disparo", {}),
        briefing_id,
        allowed_channels=allowed_channels,
    ))

    lift_data = db_data.get("lift", {})
    if lift_data.get("rows"):
        blocks.extend(format_lift_results(lift_data))
    else:
        # Checar se a marcação indica que houve teste LIFT (EXP_ADHOC markers)
        lift_markers = _detect_lift_markers(marc)
        if lift_markers:
            blocks.append(section(
                f"*🧪 Teste LIFT*\n"
                f"A campanha passou por teste LIFT (encontrei marcações de experimento: "
                f"{', '.join(lift_markers)}), mas o *resultado ainda não foi registrado* "
                f"na base de resultados.\n\n"
                f"_Possíveis razões: teste ainda em período de análise, resultado não publicado, "
                f"ou pipeline de dados pendente._"
            ))
        else:
            blocks.append(section("_🧪 Sem teste LIFT para este briefing._"))

    blocks.append(context(f"_Fontes: Monday.com + Databricks (disparo/marcação/LIFT) — {briefing_id}_"))
    return blocks
