"""
Growth Ops Copilot — Monday.com Client
Consultas ao board Growth CRM W&B (somente leitura)
"""
import requests
import urllib3
from datetime import datetime, timedelta
from config import MONDAY_API_TOKEN, MONDAY_API_URL, MONDAY_BOARD_ID, MONDAY_AREA_MAP, STATUS_CRM_ORDER

# Desabilita warning de SSL (rede corporativa com proxy/certificado próprio)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "Authorization": MONDAY_API_TOKEN,
    "Content-Type": "application/json",
}

# Colunas que o bot precisa
COLUMNS = [
    "name",
    "numeric_mkvccc73",   # Briefing ID
    "status",             # Status Campanha
    "color_mky1jm7j",     # Status CRM
    "date_mkv87hhf",      # Dt Previsão Início
    "person",             # Owner
    "numeric_mkynfjpx",   # Vol. Clientes SF DE
    "numeric_mkv99sgg",   # Qtd GT
    "numeric_mkvn5qpc",   # Vol Estimado
    "color_mkyef3p2",     # GC %
    "color_mkv95cyj",     # Produto
    "color_mkv9c29w",     # Área Demandante
    "color_mkvfrrnv",     # Canceladas (SIM/NÃO)
    "color_mkw8xn25",     # is_teste (É TESTE/NÃO)
]

# Colunas dos subitems (touchpoints)
SUBITEM_COLUMNS = [
    "color_mkv8tr7p",  # Canal
    "date_mkv8t7cz",   # Data do touch
    "numeric_mkv8kja9",# Sequência
    "color_mkvbsqyw",  # Status do disparo
]


def _query(graphql: str) -> dict:
    """Executa query GraphQL no Monday."""
    resp = requests.post(
        MONDAY_API_URL,
        headers=HEADERS,
        json={"query": graphql},
        timeout=30,
        verify=False,
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(f"Monday API error: {data['errors']}")
    return data["data"]


def _parse_item(item: dict) -> dict:
    """Transforma item do Monday em dict legível."""
    parsed = {"id": item["id"], "name": item["name"], "group": item.get("group", {}).get("title", "")}
    for col in item.get("column_values", []):
        col_id = col.get("id")
        if col_id:
            parsed[col_id] = col.get("text", "") or col.get("value", "")
    return parsed


def _is_valid_campaign(c: dict) -> bool:
    """Filtro global: exclui campanhas canceladas e de teste.
    SEMPRE aplicar antes de processar qualquer campanha."""
    cancelada = (c.get("color_mkvfrrnv") or "").lower()
    is_teste = (c.get("color_mkw8xn25") or "").lower()
    return "sim" not in cancelada and "teste" not in is_teste


def _parse_subitem(si: dict) -> dict:
    """Transforma subitem em dict com campos úteis."""
    parsed = {"id": si["id"], "name": si.get("name", "")}
    for col in si.get("column_values", []):
        col_id = col.get("id")
        if col_id:
            parsed[col_id] = col.get("text", "") or col.get("value", "")
    # Normalizados
    parsed["channel_label"] = parsed.get("color_mkv8tr7p", "")
    parsed["touch_date"] = parsed.get("date_mkv8t7cz", "")
    parsed["sequence"] = parsed.get("numeric_mkv8kja9", "")
    parsed["touch_status"] = parsed.get("color_mkvbsqyw", "")
    return parsed


def get_campaigns(area: str = None, status: str = None, limit: int = 50) -> list[dict]:
    """
    Busca campanhas do board.
    area: Banking, Payments, Segmentos, Cross, CRM (ou None = todas)
    status: filtro por Status Campanha (ou None = todos)
    """
    cols_str = ", ".join(f'"{c}"' for c in COLUMNS)
    
    # Monday não tem filtro server-side robusto, então pega tudo e filtra local
    query = f"""
    {{
        boards(ids: [{MONDAY_BOARD_ID}]) {{
            items_page(limit: 500) {{
                items {{
                    id
                    name
                    group {{ title }}
                    column_values(ids: [{cols_str}]) {{
                        id
                        text
                        value
                    }}
                }}
            }}
        }}
    }}
    """
    data = _query(query)
    items = data["boards"][0]["items_page"]["items"]
    campaigns = [_parse_item(item) for item in items]

    # Filtro global: exclui canceladas e testes
    campaigns = [c for c in campaigns if _is_valid_campaign(c)]

    # Filtro por área
    if area and area in MONDAY_AREA_MAP:
        campaigns = [c for c in campaigns if area.lower() in (c.get("color_mkv9c29w") or "").lower()]

    # Filtro por status
    if status:
        campaigns = [c for c in campaigns if status.lower() in (c.get("status") or "").lower()]

    return campaigns[:limit]


def get_campaign_subitems(item_id: str) -> list[dict]:
    """Retorna subitems (touchpoints) de um item do Monday."""
    cols_str = ", ".join(f'"{c}"' for c in SUBITEM_COLUMNS)
    query = f"""
    {{
        items(ids: [{item_id}]) {{
            subitems {{
                id
                name
                column_values(ids: [{cols_str}]) {{
                    id
                    text
                    value
                }}
            }}
        }}
    }}
    """
    data = _query(query)
    items = data.get("items", [])
    if not items:
        return []
    subitems = items[0].get("subitems", []) or []
    return [_parse_subitem(si) for si in subitems]


def get_campaign_by_briefing_id(briefing_id: str) -> dict | None:
    """Busca campanha específica pelo Briefing ID (com subitems)."""
    campaigns = get_campaigns(limit=500)
    for c in campaigns:
        if str(c.get("numeric_mkvccc73", "")).strip() == str(briefing_id).strip():
            # anexar subitems
            try:
                c["subitems"] = get_campaign_subitems(c["id"]) or []
            except Exception:
                c["subitems"] = []
            return c
    return None


def get_campaign_by_name(name: str) -> list[dict]:
    """Busca campanhas por nome (match parcial, case insensitive)."""
    campaigns = get_campaigns(limit=500)
    name_lower = name.lower()
    return [c for c in campaigns if name_lower in c.get("name", "").lower()]


# Cache simples para evitar múltiplas chamadas ao Monday na mesma sessão
_briefing_name_cache: dict[str, str] = {}


def get_names_by_briefing_ids(briefing_ids: list[str]) -> dict[str, str]:
    """
    Bulk lookup: dado uma lista de briefing_ids, retorna {briefing_id: monday_name}.
    Faz uma única chamada ao Monday e cacheia o resultado.
    Retorna somente os IDs encontrados.
    """
    if not briefing_ids:
        return {}

    # Separar IDs que já estão no cache
    missing = [bid for bid in briefing_ids if bid not in _briefing_name_cache]

    if missing:
        # Buscar todos os itens do Monday (já é o padrão — API não filtra server-side)
        campaigns = get_campaigns(limit=500)
        for c in campaigns:
            bid = str(c.get("numeric_mkvccc73", "")).strip()
            if bid:
                _briefing_name_cache[bid] = c.get("name", "")

    return {bid: _briefing_name_cache[bid] for bid in briefing_ids if bid in _briefing_name_cache}


def get_status_summary(area: str = None, mtd: bool = True) -> dict:
    """Retorna contagem por Status Campanha + breakdown CRM para Priorizadas.
    
    Retorna:
        {
            "by_status": {"Backlog": 5, "Priorizadas": 12, ...},
            "by_crm": {"Montar Jornada": 4, "Testes": 3, ...},  # só Priorizadas
            "blocked": [campaign_dict, ...],  # campanhas com impedimento
            "total": 25,
        }
    """
    campaigns = get_campaigns(area=area, limit=500)
    if mtd:
        today = datetime.now().date()
        filtered = []
        for c in campaigns:
            dt_str = c.get("date_mkv87hhf", "")
            if not dt_str:
                continue
            try:
                dt = datetime.strptime(dt_str, "%Y-%m-%d").date()
                if dt.year == today.year and dt.month == today.month:
                    filtered.append(c)
            except ValueError:
                continue
        campaigns = filtered

    by_status = {}
    by_crm = {}
    blocked = []

    for c in campaigns:
        st = c.get("status", "Sem status") or "Sem status"
        by_status[st] = by_status.get(st, 0) + 1

        # Breakdown CRM só pra campanhas ativas (Priorizadas ou Teste TCPG)
        if st.lower() in ("priorizadas", "teste tcpg"):
            crm = c.get("color_mky1jm7j", "").strip()
            if crm:
                by_crm[crm] = by_crm.get(crm, 0) + 1
                if crm.lower() in ("com impeditivo", "com impedimento"):
                    blocked.append(c)

    return {
        "by_status": by_status,
        "by_crm": by_crm,
        "blocked": blocked,
        "total": len(campaigns),
    }


def get_upcoming_campaigns(days: int = 7, area: str = None) -> list[dict]:
    """Campanhas com previsão de início nos próximos N dias."""
    from datetime import datetime, timedelta
    
    campaigns = get_campaigns(area=area, limit=500)
    today = datetime.now().date()
    cutoff = today + timedelta(days=days)
    
    upcoming = []
    for c in campaigns:
        dt_str = c.get("date_mkv87hhf", "")
        if dt_str:
            try:
                dt = datetime.strptime(dt_str, "%Y-%m-%d").date()
                if today <= dt <= cutoff:
                    c["_start_date"] = dt
                    upcoming.append(c)
            except ValueError:
                continue
    
    upcoming.sort(key=lambda x: x["_start_date"])
    return upcoming


def get_sla_campaigns(area: str = None, sla_days: int = 4) -> dict:
    """Identifica campanhas em risco de SLA.
    
    SLA CRM: campanha precisa ser avançada (sair de Backlog) 
    até {sla_days} dias antes da Dt Previsão Início.
    
    Retorna dict com 3 listas:
    - vencidas: já passou a data limite do SLA (disparo em < sla_days ou no passado)
    - em_risco: faltam entre sla_days e sla_days+2 dias (janela de atenção)
    - dentro: faltam mais de sla_days+2 dias (ok por enquanto)
    """
    campaigns = get_campaigns(area=area, limit=500)
    today = datetime.now().date()
    
    vencidas = []
    em_risco = []
    
    for c in campaigns:
        status = (c.get("status") or "").lower()
        
        # Só campanhas em Backlog (ainda não avançadas)
        if "backlog" not in status:
            continue
        
        dt_str = c.get("date_mkv87hhf", "")
        if not dt_str:
            continue
        
        try:
            dt_inicio = datetime.strptime(dt_str, "%Y-%m-%d").date()
        except ValueError:
            continue
        
        # Data limite do SLA = dt_inicio - sla_days
        dt_sla = dt_inicio - timedelta(days=sla_days)
        dias_restantes = (dt_sla - today).days
        
        c["_dt_inicio"] = dt_inicio
        c["_dt_sla"] = dt_sla
        c["_dias_restantes_sla"] = dias_restantes
        
        if dias_restantes < 0:
            # SLA já venceu
            c["_sla_status"] = "vencida"
            vencidas.append(c)
        elif dias_restantes <= 2:
            # Vai vencer em 0-2 dias
            c["_sla_status"] = "em_risco"
            em_risco.append(c)
    
    # Ordenar por urgência (mais atrasada primeiro)
    vencidas.sort(key=lambda x: x["_dias_restantes_sla"])
    em_risco.sort(key=lambda x: x["_dias_restantes_sla"])
    
    return {"vencidas": vencidas, "em_risco": em_risco}
