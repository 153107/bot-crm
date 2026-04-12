"""
Growth Ops Copilot — Daily Intelligence Banking
Relatório executivo D-1 focado exclusivamente em Banking Growth.
Formato: Jornal Executivo — direto, sem introduções, foco em métricas e gargalos.
"""
import logging
from datetime import datetime, timedelta

import databricks_client as db
import monday_client as monday
import formatters as fmt
from parsers import parse_campaign_name
from config import AREA_TO_BU, SEEDLIST_FILTER

logger = logging.getLogger("growth-bot")

# Thresholds de engajamento (abertura %) pra indicador visual
ENGAGEMENT_THRESHOLDS = {
    "INAPP": {"good": 15, "medium": 8},
    "PUSH": {"good": 3, "medium": 1.5},
    "EMAIL": {"good": 15, "medium": 8},
    "DM": {"good": 10, "medium": 5},
    "WHATSAPP": {"good": 40, "medium": 20},
    "SMS": {"good": 5, "medium": 2},
    "DELIVERY": {"good": 95, "medium": 85},
}

CLICK_THRESHOLDS = {
    "INAPP": {"good": 1.0, "medium": 0.3},
    "EMAIL": {"good": 1.0, "medium": 0.3},
    "DM": {"good": 1.5, "medium": 0.5},
}

CHANNEL_DISPLAY = {
    "INAPP": "InApp", "PUSH": "Push", "EMAIL": "Email",
    "DM": "DM", "WHATSAPP": "WhatsApp", "SMS": "SMS",
}


def _ind(rate: float, channel: str) -> str:
    thresholds = ENGAGEMENT_THRESHOLDS.get(channel.upper(), {"good": 10, "medium": 5})
    if rate >= thresholds["good"]:
        return "🟢"
    elif rate >= thresholds["medium"]:
        return "🟡"
    return "🔴"


def _ind_click(rate: float, channel: str) -> str:
    thresholds = CLICK_THRESHOLDS.get(channel.upper(), {"good": 1.0, "medium": 0.3})
    if rate >= thresholds["good"]:
        return "🟢"
    elif rate >= thresholds["medium"]:
        return "🟡"
    return "🔴"


def _mono_table(headers: list[str], rows: list[list[str]], widths: list[int]) -> str:
    """Monta tabela monospace alinhada pra bloco ``` do Slack."""
    header_line = "  ".join(h.ljust(w) for h, w in zip(headers, widths))
    sep = "-" * (sum(widths) + 2 * (len(widths) - 1))
    lines = [header_line, sep]
    for row in rows:
        lines.append("  ".join(str(cell).ljust(w) for cell, w in zip(row, widths)))
    return "\n".join(lines)


AREA_CONFIG = {
    "Banking":   {"bu": "SFPF Banking",   "emoji": "🏦", "label": "Banking Growth"},
    "Payments":  {"bu": "SFPF Payments",  "emoji": "💳", "label": "Payments Growth"},
    "Segmentos": {"bu": "SFPF Segmentos", "emoji": "🎯", "label": "Segmentos Growth"},
    "Cross":     {"bu": "SFPF Cross",     "emoji": "🔀", "label": "Cross Growth"},
}


def generate_daily_banking(date: str = None, area: str = "Banking") -> list[dict]:
    cfg  = AREA_CONFIG.get(area, AREA_CONFIG["Banking"])
    BU   = cfg["bu"]
    AREA = area

    if not date:
        yesterday = datetime.now() - timedelta(days=1)
        date = yesterday.strftime("%Y-%m-%d")

    date_display = datetime.strptime(date, "%Y-%m-%d").strftime("%d/%m/%Y")
    today = datetime.now().date()
    today_display = today.strftime("%d/%m/%Y")

    blocks = []

    # ══════════════════════════════════════════════════════════
    # HEADER
    # ══════════════════════════════════════════════════════════
    blocks.append(fmt.header(f"{cfg['emoji']} Daily Intelligence | {cfg['label']}"))
    blocks.append(fmt.context(f"Relatório de Performance e Operação — {today_display}"))
    blocks.append(fmt.divider())

    # ══════════════════════════════════════════════════════════
    # 📡 D-1 | Monitoramento de Campanhas
    # ══════════════════════════════════════════════════════════
    blocks.append(fmt.section("*📡 D-1 | Monitoramento de Campanhas*"))

    try:
        campaigns_d1 = _get_campaigns_by_channel(date, BU)

        if campaigns_d1:
            headers = ["ID", "Campanha", "Canal", "Volume", "Entrega", "Abertura", "Clique"]
            widths = [12, 21, 9, 9, 9, 9, 8]
            table_rows = []

            # Canais sem tracking de clique (PUSH, WHATSAPP, SMS)
            NO_CLICK = {"PUSH", "WHATSAPP", "SMS"}

            for item in campaigns_d1[:15]:
                bid = item["briefing_id"][:12]
                name = item["name"][:18] + "..." if len(item["name"]) > 21 else item["name"]
                ch = CHANNEL_DISPLAY.get(item["channel"].upper(), item["channel"])
                vol = fmt.fmt_number(item["delivered"])

                ent = f"{fmt.fmt_pct(item['delivery_rate'])}{_ind(item['delivery_rate'], 'DELIVERY')}"
                ab  = f"{fmt.fmt_pct(item['open_rate'])}{_ind(item['open_rate'], item['channel'])}"

                channel_upper = item["channel"].upper()
                if channel_upper in NO_CLICK:
                    cl = "⚪ —"
                else:
                    # Exibe CTOR (clique / abertura) quando tem abertura; CTR caso contrário
                    cl_val = item["ctor"] if item["opened_7d"] > 0 else item["ctr"]
                    cl = f"{fmt.fmt_pct(cl_val)}{_ind_click(cl_val, channel_upper)}" if cl_val > 0 else "⚪ —"

                table_rows.append([bid, name, ch, vol, ent, ab, cl])

            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"```{_mono_table(headers, table_rows, widths)}```"}})

            unique = len(set(i["briefing_id"] for i in campaigns_d1))
            total_del = sum(i["delivered"] for i in campaigns_d1)
            # OR médio = média das taxas de abertura por linha (cada linha = campanha × canal)
            avg_open = sum(i["open_rate"] for i in campaigns_d1) / len(campaigns_d1)
            blocks.append(fmt.context(f"_Resumo: {unique} campanhas | {fmt.fmt_number(total_del)} entregas | OR médio: {fmt.fmt_pct(avg_open)}_"))
        else:
            blocks.append(fmt.section(f"_Nenhuma atividade de {AREA} registrada para D-1._"))

    except Exception as e:
        logger.error(f"Erro D-1: {e}", exc_info=True)
        blocks.append(fmt.section("_Erro ao consultar dados de D-1._"))

    blocks.append(fmt.divider())

    # ══════════════════════════════════════════════════════════
    # 🚀 Próximas Campanhas
    # ══════════════════════════════════════════════════════════
    blocks.append(fmt.section("*🚀 | Próximas Campanhas*"))

    priorizadas  = []
    backlog      = []
    sla_excedido = []
    sla_risco    = []

    try:
        campaigns_monday = monday.get_campaigns(area=AREA, limit=100)
        sla_risco = []

        for c in campaigns_monday:
            status = (c.get("status") or "").lower()
            status_crm = c.get("color_mky1jm7j", "") or ""
            raw_name = c.get("name", "?")
            bid = str(c.get("numeric_mkvccc73", "")).strip()
            clean_name = parse_campaign_name(raw_name, bid) if bid else raw_name

            dt_str = c.get("date_mkv87hhf", "")
            dt_inicio = None
            dt_inicio_fmt = ""
            dias_para_inicio = None

            if dt_str:
                try:
                    dt_inicio = datetime.strptime(dt_str, "%Y-%m-%d").date()
                    dt_inicio_fmt = dt_inicio.strftime("%d/%m")
                    dias_para_inicio = (dt_inicio - today).days
                except ValueError:
                    pass

            item = {
                "bid": bid,
                "name": clean_name,
                "status_crm": status_crm,
                "status": status,
                "dt_inicio": dt_inicio,
                "dt_inicio_fmt": dt_inicio_fmt,
                "dias_para_inicio": dias_para_inicio,
                "owner": c.get("person", "") or "Sem responsável",
            }

            if "priorizada" in status or "teste tcpg" in status:
                priorizadas.append(item)
            elif "backlog" in status:
                if dt_inicio is not None:
                    backlog.append(item)
                    if dias_para_inicio is not None:
                        if dias_para_inicio <= 0:
                            item["dias_excedido"] = abs(dias_para_inicio)
                            sla_excedido.append(item)
                        elif dias_para_inicio <= 4:
                            sla_risco.append(item)

        # ⭐ Priorizadas
        blocks.append(fmt.section("*🟢 Priorizadas*"))
        if priorizadas:
            headers = ["ID", "Campanha", "Status CRM", "Início"]
            widths = [12, 25, 20, 8]
            table_rows = []
            for item in priorizadas[:10]:
                bid = item["bid"][:12]
                name = item["name"][:22] + "..." if len(item["name"]) > 25 else item["name"]
                st = item["status_crm"][:20] if item["status_crm"] else "Em andamento"
                dt = item["dt_inicio_fmt"] or "—"
                table_rows.append([bid, name, st, dt])
            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"```{_mono_table(headers, table_rows, widths)}```"}})
        else:
            blocks.append(fmt.section("_Nenhuma campanha priorizada no momento._"))

        # 📂 Backlog
        backlog_normal = [b for b in backlog if b not in sla_excedido and b not in sla_risco]
        blocks.append(fmt.section(f"*🟡 Backlog ({len(backlog)} com data prevista)*"))
        if backlog:
            headers = ["ID", "Campanha", "Início"]
            widths = [12, 30, 8]
            table_rows = []
            for item in (backlog_normal + sla_risco + sla_excedido)[:10]:
                bid = item["bid"][:12]
                name = item["name"][:27] + "..." if len(item["name"]) > 30 else item["name"]
                dt = item["dt_inicio_fmt"] or "—"
                table_rows.append([bid, name, dt])
            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"```{_mono_table(headers, table_rows, widths)}```"}})
        else:
            blocks.append(fmt.section("_Backlog vazio._"))

    except Exception as e:
        logger.error(f"Erro Monday: {e}", exc_info=True)
        blocks.append(fmt.section("_Erro ao consultar Monday._"))

    blocks.append(fmt.divider())

    # ══════════════════════════════════════════════════════════
    # 🚨 Aviso de SLA
    # ══════════════════════════════════════════════════════════
    blocks.append(fmt.section("*🚨 Aviso de SLA*"))

    if sla_excedido or sla_risco:
        # ❗ Fora do SLA
        if sla_excedido:
            blocks.append(fmt.section("*🔴 Fora do SLA*"))
            headers = ["ID", "Campanha", "Início", "Atraso"]
            widths = [12, 25, 8, 15]
            table_rows = []
            for item in sla_excedido[:5]:
                bid = item["bid"][:12]
                name = item["name"][:22] + "..." if len(item["name"]) > 25 else item["name"]
                dt = item["dt_inicio_fmt"]
                atraso = f"{item['dias_excedido']}d excedido" if item["dias_excedido"] > 0 else "Vence hoje"
                table_rows.append([bid, name, dt, atraso])
            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"```{_mono_table(headers, table_rows, widths)}```"}})

        # ⚠️ Excedendo o prazo
        if sla_risco:
            blocks.append(fmt.section("*⚠️ Excedendo o prazo*"))
            headers = ["ID", "Campanha", "Início", "Faltam"]
            widths = [12, 25, 8, 12]
            table_rows = []
            for item in sla_risco[:5]:
                bid = item["bid"][:12]
                name = item["name"][:22] + "..." if len(item["name"]) > 25 else item["name"]
                dt = item["dt_inicio_fmt"]
                faltam = f"{item['dias_para_inicio']}d p/ início"
                table_rows.append([bid, name, dt, faltam])
            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"```{_mono_table(headers, table_rows, widths)}```"}})
    else:
        blocks.append(fmt.section("_Todas as campanhas dentro do prazo._"))

    blocks.append(fmt.divider())

    # ══════════════════════════════════════════════════════════
    # 🧪 Teste LIFT
    # ══════════════════════════════════════════════════════════
    blocks.append(fmt.section("*🔬 Teste LIFT*"))

    try:
        # Buscar LIFT do mês atual
        lift_data = db.get_lift_results(days=30)

        if lift_data.get("rows"):
            cols = lift_data["columns"]

            area_lifts = []
            area_lower = AREA.lower()
            for row in lift_data["rows"]:
                r = dict(zip(cols, row))
                bid = str(r.get("briefing_id", ""))
                campaign = monday.get_campaign_by_briefing_id(bid)
                if campaign:
                    camp_area = (campaign.get("color_mkv9c29w") or "").lower()
                    if area_lower in camp_area:
                        r["campaign_name"] = parse_campaign_name(campaign.get("name", ""), bid)
                        area_lifts.append(r)

            if area_lifts:
                headers = ["ID", "Campanha", "Status", "p-value", "Incremento"]
                widths = [12, 22, 12, 9, 12]
                table_rows = []

                for r in area_lifts[:5]:
                    bid = str(r.get("briefing_id", ""))[:12]
                    name = r.get("campaign_name", "?")
                    if len(name) > 22:
                        name = name[:19] + "..."

                    result = r.get("final_result") or "Rodando"
                    if "aprov" in str(result).lower():
                        st = "Aprovado ✅"
                    elif "reprov" in str(result).lower():
                        st = "Reprovado ❌"
                    else:
                        st = "Rodando 🔄"

                    pv = str(r.get("p_value") or "—")
                    inc = str(r.get("incremental") or "—")

                    table_rows.append([bid, name, st, pv, inc])

                blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"```{_mono_table(headers, table_rows, widths)}```"}})
            else:
                blocks.append(fmt.section(f"_Nenhum teste LIFT de {AREA} no mês._"))
        else:
            blocks.append(fmt.section("_Nenhum teste LIFT ativo._"))

    except Exception as e:
        logger.error(f"Erro LIFT: {e}", exc_info=True)
        blocks.append(fmt.section("_Erro ao consultar testes LIFT._"))

    # ══════════════════════════════════════════════════════════
    # FOOTER
    # ══════════════════════════════════════════════════════════
    blocks.append(fmt.divider())
    blocks.append(fmt.context(f"_Fonte: Databricks (D-1: {date_display}) + Monday.com | Growth Ops Copilot_"))

    return blocks


def _get_campaigns_by_channel(date: str, bu: str) -> list[dict]:

    sql = f"""
    SELECT
        d.briefing_id,
        d.channel,
        MAX(d.product_category) as produto,
        COUNT(*) as sent,
        SUM(CASE WHEN d.is_delivered = true THEN 1 ELSE 0 END) as delivered,
        -- Abertura janela 7d (OR): INAPP usa coluna dedicada
        SUM(CASE
            WHEN d.channel = 'INAPP' AND d.inapp_seven_day_window_opened_at IS NOT NULL THEN 1
            WHEN d.channel != 'INAPP' AND d.seven_day_window_opened_at IS NOT NULL THEN 1
            ELSE 0
        END) as opened_7d,
        -- Clique janela 7d (CTR): INAPP usa coluna dedicada
        SUM(CASE
            WHEN d.channel = 'INAPP' AND d.inapp_seven_day_window_clicked_at IS NOT NULL THEN 1
            WHEN d.channel != 'INAPP' AND d.seven_day_window_clicked_at IS NOT NULL THEN 1
            ELSE 0
        END) as clicked_7d
    FROM {db.TABLE_DISPARO} d
    WHERE d.notification_day_date = '{date}'
      AND (d.adjusted_bu_requester = '{bu}' OR d.bu_requester = '{bu}')
      {SEEDLIST_FILTER.replace('AND consumer_id', 'AND d.consumer_id')}
    GROUP BY d.briefing_id, d.channel
    HAVING delivered > 0
    ORDER BY delivered DESC
    """

    result = db.execute_sql(sql)
    if not result.get("rows"):
        return []

    items = []
    cols = result["columns"]

    bids = list(set(str(row[cols.index("briefing_id")]) for row in result["rows"]))
    names_map = monday.get_names_by_briefing_ids(bids)

    for row in result["rows"]:
        r = dict(zip(cols, row))
        bid = str(r.get("briefing_id", ""))
        channel = r.get("channel", "?")

        monday_name = names_map.get(bid, "")
        name = parse_campaign_name(monday_name, bid) if monday_name else (r.get("produto") or f"Campanha {bid}")

        sent      = int(r.get("sent") or 0)
        delivered = int(r.get("delivered") or 0)
        opened_7d = int(r.get("opened_7d") or 0)
        clicked_7d = int(r.get("clicked_7d") or 0)

        # % Entrega: entregues / enviados
        delivery_rate = (delivered / sent * 100) if sent else 0
        # OR:   abertas_7d / entregues  (denominador = entregues)
        open_rate = (opened_7d / delivered * 100) if delivered else 0
        # CTR:  clicadas_7d / entregues
        ctr = (clicked_7d / delivered * 100) if delivered else 0
        # CTOR: clicadas_7d / abertas_7d
        ctor = (clicked_7d / opened_7d * 100) if opened_7d else 0

        items.append({
            "briefing_id": bid,
            "name": name,
            "channel": channel,
            "sent": sent,
            "delivered": delivered,
            "opened_7d": opened_7d,
            "clicked_7d": clicked_7d,
            "delivery_rate": delivery_rate,
            "open_rate": open_rate,
            "ctr": ctr,
            "ctor": ctor,
        })

    return items


# ══════════════════════════════════════════════════════════════
# Compatibilidade com app.py
# ══════════════════════════════════════════════════════════════

def generate_daily_report(bu: str = None, date: str = None) -> list[dict]:
    from config import AREA_TO_BU
    # Mapear BU de volta pra área (ex: "SFPF Banking" → "Banking")
    bu_to_area = {v: k for k, v in AREA_TO_BU.items()}
    area = bu_to_area.get(bu, "Banking") if bu else "Banking"
    return generate_daily_banking(date, area=area)


def post_daily_to_channels(app):
    from config import SLACK_CHANNELS, AREAS_DAILY

    logger.info("Posting Daily Intelligence to channels...")

    for area, channel_name in SLACK_CHANNELS.items():
        if area not in AREAS_DAILY:
            continue

        try:
            blocks = generate_daily_banking(area=area)

            channel_id = None
            for channel_type in ["public_channel", "private_channel"]:
                result = app.client.conversations_list(types=channel_type, limit=1000)
                for ch in result.get("channels", []):
                    if ch["name"] == channel_name:
                        channel_id = ch["id"]
                        break
                if channel_id:
                    break

            if channel_id:
                app.client.chat_postMessage(channel=channel_id, blocks=blocks)
                logger.info(f"Daily posted to #{channel_name} ({area})")
            else:
                logger.warning(f"Channel #{channel_name} not found")

        except Exception as e:
            logger.error(f"Failed to post daily to #{channel_name}: {e}")
