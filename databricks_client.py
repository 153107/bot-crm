"""
Growth Ops Copilot — Databricks Client
Autenticação dual:
  1. DATABRICKS_TOKEN (env var) — usado no Codespaces/servidor
  2. OAuth U2M via CLI — usado localmente no Windows
"""
import time
import subprocess
import json
import os
import logging

from config import BU_TAXONOMY_SIGLA, SEEDLIST_FILTER

logger = logging.getLogger("growth-bot")

# ── Config ────────────────────────────────────────────────
DATABRICKS_HOST         = "https://picpay-principal.cloud.databricks.com"
DATABRICKS_PROFILE      = "picpay"
DATABRICKS_WAREHOUSE_ID = "3b94f0935afb32db"  # Exploracao 03

# Path do CLI (Windows via winget)
DATABRICKS_CLI_PATH = os.path.join(
    os.environ.get("LOCALAPPDATA", ""),
    "Microsoft", "WinGet", "Packages",
    "Databricks.DatabricksCLI_Microsoft.Winget.Source_8wekyb3d8bbwe",
    "databricks.exe"
)

# ── Tabelas ──────────────────────────────────────────────
TABLE_MARCACAO = "picpay.self_service_analytics.pf_growth_campaign_message_events"
TABLE_DISPARO  = "picpay.self_service_analytics.pf_growth_notifications_reporting"
TABLE_LIFT     = "picpay.self_service_analytics.growth_adhoc_results"


def _get_oauth_token() -> str:
    """Pega token Databricks.
    
    Prioridade:
    1. Variável de ambiente DATABRICKS_TOKEN (Codespaces / servidor)
    2. OAuth U2M via CLI (local Windows)
    """
    # 1. Env var (Codespaces/servidor)
    env_token = os.environ.get("DATABRICKS_TOKEN", "").strip()
    if env_token:
        logger.debug("Usando DATABRICKS_TOKEN da env var")
        return env_token

    # 2. OAuth U2M via CLI (local)
    cli_path = DATABRICKS_CLI_PATH
    # Fallback: CLI no PATH (Linux/Codespaces após install)
    if not os.path.exists(cli_path):
        cli_path = "databricks"

    try:
        result = subprocess.run(
            [cli_path, "auth", "token",
             "--host", DATABRICKS_HOST, "--profile", DATABRICKS_PROFILE],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            raise RuntimeError(f"CLI error: {result.stderr}")
        token_data = json.loads(result.stdout)
        return token_data["access_token"]
    except FileNotFoundError:
        raise RuntimeError(
            "Databricks CLI não encontrado. "
            "Configure DATABRICKS_TOKEN como variável de ambiente, "
            "ou instale o CLI: https://docs.databricks.com/dev-tools/cli/install.html"
        )
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Erro ao parsear token OAuth: {e}")


def _get_workspace_client():
    """Retorna WorkspaceClient autenticado via OAuth."""
    from databricks.sdk import WorkspaceClient
    token = _get_oauth_token()
    return WorkspaceClient(host=DATABRICKS_HOST, token=token)


def _bu_filter(bu: str, table_alias: str = "") -> str:
    """Gera filtro SQL para área usando adjusted_bu_requester (campo corrigido pela governança).
    
    Hierarquia de confiabilidade:
    1. adjusted_bu_requester — corrigido, 4 valores limpos: Banking, Payments, Segmentos, Cross
    2. bu_requester — pode ter inconsistências (ex: 'SFPF' genérico)
    3. campaign_name sigla — pode refletir BU original pré-migração (NÃO usar pra filtro)
    
    Usamos adjusted_bu_requester como filtro primário com bu_requester como fallback.
    """
    if not bu:
        return ""
    prefix = f"{table_alias}." if table_alias else ""
    return f"AND ({prefix}adjusted_bu_requester = '{bu}' OR {prefix}bu_requester = '{bu}')"


def execute_sql(sql: str, timeout_seconds: int = 300) -> dict:
    """
    Executa SQL no Databricks via SDK com OAuth.
    Tenta sync primeiro (até 50s). Se não terminar, faz polling async.
    Retorna: {"columns": [...], "rows": [[...], ...]}
    """
    from databricks.sdk.service.sql import StatementState
    
    w = _get_workspace_client()
    
    # Submeter query (sync até 50s)
    response = w.statement_execution.execute_statement(
        warehouse_id=DATABRICKS_WAREHOUSE_ID,
        statement=sql,
        wait_timeout="50s",
    )
    
    # Se já completou
    if response.status.state == StatementState.SUCCEEDED:
        return _parse_sdk_result(response)
    
    # Se falhou
    if response.status.state in (StatementState.FAILED, StatementState.CANCELED):
        error = response.status.error.message if response.status.error else "Query failed"
        raise RuntimeError(f"Databricks SQL error: {error}")
    
    # Ainda rodando → polling async
    statement_id = response.statement_id
    elapsed = 50
    
    while elapsed < timeout_seconds:
        time.sleep(5)
        elapsed += 5
        
        status = w.statement_execution.get_statement(statement_id)
        
        if status.status.state == StatementState.SUCCEEDED:
            return _parse_sdk_result(status)
        
        if status.status.state in (StatementState.FAILED, StatementState.CANCELED):
            error = status.status.error.message if status.status.error else "Query failed"
            raise RuntimeError(f"Databricks SQL error: {error}")
    
    # Timeout → cancela
    w.statement_execution.cancel_execution(statement_id)
    raise TimeoutError(f"Query {statement_id} did not complete after {timeout_seconds}s")


def _parse_sdk_result(response) -> dict:
    """Extrai colunas e rows do resultado do SDK."""
    columns = [col.name for col in response.manifest.schema.columns]
    rows = response.result.data_array if response.result else []
    return {"columns": columns, "rows": rows}


# ═══════════════════════════════════════════════════════════
# Queries prontas — Marcação
# ═══════════════════════════════════════════════════════════

def get_marcacao_stats(briefing_id: str) -> dict:
    """Estatísticas de marcação para um briefing_id."""
    sql = f"""
    SELECT
        properties_channel,
        group_type,
        COUNT(*) as total_marcacoes,
        COUNT(DISTINCT consumer_id) as unique_consumers,
        MIN(created_date) as first_date,
        MAX(created_date) as last_date
    FROM {TABLE_MARCACAO}
    WHERE briefing_id = '{briefing_id}'
    GROUP BY properties_channel, group_type
    ORDER BY total_marcacoes DESC
    """
    return execute_sql(sql)


def get_marcacao_by_bu(bu: str, days: int = 7) -> dict:
    """Marcações dos últimos N dias por BU.
    Usa bu_requester + sigla na taxonomia (properties_sending_name).
    Tabela de marcação NÃO tem adjusted_bu_requester.
    """
    sigla = BU_TAXONOMY_SIGLA.get(bu, "")
    bu_where = f"bu_requester = '{bu}'"
    if sigla:
        bu_where = f"({bu_where} OR properties_sending_name LIKE '%{sigla}%')"

    sql = f"""
    SELECT
        briefing_id,
        product_category,
        campaign_type,
        group_type,
        COUNT(DISTINCT consumer_id) as consumers,
        MIN(created_date) as start_date,
        MAX(created_date) as end_date
    FROM {TABLE_MARCACAO}
    WHERE {bu_where}
      AND created_date >= DATE_SUB(CURRENT_DATE(), {days})
      AND is_test = false
    GROUP BY briefing_id, product_category, campaign_type, group_type
    ORDER BY consumers DESC
    LIMIT 50
    """
    return execute_sql(sql)


# ═══════════════════════════════════════════════════════════
# Queries prontas — Disparo
# ═══════════════════════════════════════════════════════════

def get_dispatch_stats(briefing_id: str) -> dict:
    """Métricas de disparo por canal × touchpoint (campaign_name).

    Lógica de seedlist: dentro de cada campaign_name, dias com volume
    inferior a 1% do dia de maior volume são descartados (seedlist/teste).
    Se todos os dias têm volumes similares (régua incremental), consolida
    tudo numa linha com a data do dia de maior volume como referência.

    Conceitos:
    - Entrega (%): is_delivered=true / total_sent
    - OR (%):  abertas_7d / entregues  (janela 7d, denominador = entregues)
    - CTR (%): clicadas_7d / entregues
    - CTOR (%): clicadas_7d / abertas_7d
    INAPP usa colunas dedicadas: inapp_seven_day_window_opened/clicked_at
    """
    sql = f"""
    WITH raw AS (
        SELECT
            channel,
            campaign_name,
            DATE(sent_at)                                        as send_date,
            MIN(sent_at)                                         as first_sent,
            COUNT(*)                                             as total_sent,
            SUM(CASE WHEN is_delivered = true THEN 1 ELSE 0 END) as delivered,
            SUM(CASE
                WHEN is_delivered = true AND channel = 'INAPP' AND inapp_seven_day_window_opened_at IS NOT NULL THEN 1
                WHEN is_delivered = true AND channel != 'INAPP' AND seven_day_window_opened_at IS NOT NULL THEN 1
                ELSE 0
            END) as opened_7d,
            SUM(CASE
                WHEN is_delivered = true AND channel = 'INAPP' AND inapp_seven_day_window_clicked_at IS NOT NULL THEN 1
                WHEN is_delivered = true AND channel != 'INAPP' AND seven_day_window_clicked_at IS NOT NULL THEN 1
                ELSE 0
            END) as clicked_7d
        FROM {TABLE_DISPARO}
        WHERE briefing_id = '{briefing_id}' OR adjusted_briefing_id = '{briefing_id}'
          {SEEDLIST_FILTER}
        GROUP BY channel, campaign_name, DATE(sent_at)
    ),
    max_per_touchpoint AS (
        SELECT channel, campaign_name, MAX(total_sent) as max_sent
        FROM raw
        GROUP BY channel, campaign_name
    ),
    filtered AS (
        -- Remove dias com volume < 10% do pico do mesmo touchpoint (seedlist/testes parciais)
        -- E garante mínimo absoluto de 50 entregues pra ser considerado disparo real
        SELECT r.*
        FROM raw r
        JOIN max_per_touchpoint m
          ON r.channel = m.channel AND r.campaign_name = m.campaign_name
        WHERE r.total_sent >= m.max_sent * 0.10
          AND r.delivered >= 100
    )
    -- Consolida os dias restantes por touchpoint
    SELECT
        channel,
        campaign_name,
        -- Data do dia de maior volume (disparo principal ou maior onda)
        FIRST_VALUE(send_date) OVER (
            PARTITION BY channel, campaign_name
            ORDER BY total_sent DESC
        )                                                    as send_date,
        FIRST_VALUE(first_sent) OVER (
            PARTITION BY channel, campaign_name
            ORDER BY total_sent DESC
        )                                                    as first_sent,
        SUM(total_sent)   OVER (PARTITION BY channel, campaign_name) as total_sent,
        SUM(delivered)    OVER (PARTITION BY channel, campaign_name) as delivered,
        SUM(opened_7d)    OVER (PARTITION BY channel, campaign_name) as opened_7d,
        SUM(clicked_7d)   OVER (PARTITION BY channel, campaign_name) as clicked_7d
    FROM filtered
    QUALIFY ROW_NUMBER() OVER (PARTITION BY channel, campaign_name ORDER BY total_sent DESC) = 1
    ORDER BY total_sent DESC
    """
    return execute_sql(sql)


def get_daily_dispatch_summary(date: str, bu: str = None) -> dict:
    """Resumo de disparos de um dia específico (formato YYYY-MM-DD).

    Métricas com janela móvel 7d — denominador = entregues:
    - OR   = opened_7d / delivered
    - CTR  = clicked_7d / delivered
    - CTOR = clicked_7d / opened_7d
    """
    bu_clause = _bu_filter(bu)
    sql = f"""
    SELECT
        adjusted_bu_requester,
        channel,
        COUNT(*) as total_sent,
        COUNT(DISTINCT consumer_id) as unique_consumers,
        SUM(CASE WHEN is_delivered = true THEN 1 ELSE 0 END) as delivered,
        SUM(CASE
            WHEN is_delivered = true AND channel = 'INAPP' AND inapp_seven_day_window_opened_at IS NOT NULL THEN 1
            WHEN is_delivered = true AND channel != 'INAPP' AND seven_day_window_opened_at IS NOT NULL THEN 1
            ELSE 0
        END) as opened_7d,
        SUM(CASE
            WHEN is_delivered = true AND channel = 'INAPP' AND inapp_seven_day_window_clicked_at IS NOT NULL THEN 1
            WHEN is_delivered = true AND channel != 'INAPP' AND seven_day_window_clicked_at IS NOT NULL THEN 1
            ELSE 0
        END) as clicked_7d,
        COUNT(DISTINCT briefing_id) as campaigns
    FROM {TABLE_DISPARO}
    WHERE notification_day_date = '{date}'
      {SEEDLIST_FILTER}
      {bu_clause}
    GROUP BY adjusted_bu_requester, channel
    ORDER BY adjusted_bu_requester, total_sent DESC
    """
    return execute_sql(sql)


def get_best_performers(days: int = 30, bu: str = None, limit: int = 10) -> dict:
    """Top campanhas por OR (abertas_7d / entregues) nos últimos N dias."""
    bu_clause = _bu_filter(bu)
    sql = f"""
    SELECT
        briefing_id,
        adjusted_bu_requester,
        channel,
        COUNT(*) as total_sent,
        SUM(CASE WHEN is_delivered = true THEN 1 ELSE 0 END) as delivered,
        SUM(CASE
            WHEN is_delivered = true AND channel = 'INAPP' AND inapp_seven_day_window_opened_at IS NOT NULL THEN 1
            WHEN is_delivered = true AND channel != 'INAPP' AND seven_day_window_opened_at IS NOT NULL THEN 1
            ELSE 0
        END) as opened_7d,
        SUM(CASE
            WHEN is_delivered = true AND channel = 'INAPP' AND inapp_seven_day_window_clicked_at IS NOT NULL THEN 1
            WHEN is_delivered = true AND channel != 'INAPP' AND seven_day_window_clicked_at IS NOT NULL THEN 1
            ELSE 0
        END) as clicked_7d,
        ROUND(SUM(CASE
            WHEN is_delivered = true AND channel = 'INAPP' AND inapp_seven_day_window_opened_at IS NOT NULL THEN 1
            WHEN is_delivered = true AND channel != 'INAPP' AND seven_day_window_opened_at IS NOT NULL THEN 1
            ELSE 0
        END) * 100.0 / NULLIF(SUM(CASE WHEN is_delivered = true THEN 1 ELSE 0 END), 0), 2) as or_pct,
        ROUND(SUM(CASE
            WHEN is_delivered = true AND channel = 'INAPP' AND inapp_seven_day_window_clicked_at IS NOT NULL THEN 1
            WHEN is_delivered = true AND channel != 'INAPP' AND seven_day_window_clicked_at IS NOT NULL THEN 1
            ELSE 0
        END) * 100.0 / NULLIF(SUM(CASE WHEN is_delivered = true THEN 1 ELSE 0 END), 0), 2) as ctr_pct
    FROM {TABLE_DISPARO}
    WHERE notification_day_date >= DATE_SUB(CURRENT_DATE(), {days})
      {SEEDLIST_FILTER}
      {bu_clause}
    GROUP BY briefing_id, adjusted_bu_requester, channel
    HAVING delivered > 1000
    ORDER BY or_pct DESC
    LIMIT {limit}
    """
    return execute_sql(sql)


def get_top_campaigns(days: int = 30, bu: str = None, limit: int = 10) -> dict:
    """Top campanhas consolidadas. OR/CTR calculados sobre entregues. CTOR = clicadas/abertas."""
    bu_clause = _bu_filter(bu, "d")
    sql = f"""
    SELECT
        d.briefing_id,
        MAX(d.product_category) as produto,
        MAX(d.adjusted_bu_requester) as area,
        MAX(d.campaign_name) as nome_campanha,
        COUNT(DISTINCT d.channel) as qtd_canais,
        MIN(d.notification_day_date) as primeiro_disparo,
        MAX(d.notification_day_date) as ultimo_disparo,
        COUNT(*) as enviados,
        SUM(CASE WHEN d.is_delivered = true THEN 1 ELSE 0 END) as entregues,
        COUNT(DISTINCT d.consumer_id) as clientes_impactados,
        SUM(CASE
            WHEN d.is_delivered = true AND d.channel = 'INAPP' AND d.inapp_seven_day_window_opened_at IS NOT NULL THEN 1
            WHEN d.is_delivered = true AND d.channel != 'INAPP' AND d.seven_day_window_opened_at IS NOT NULL THEN 1
            ELSE 0
        END) as abertas_7d,
        SUM(CASE
            WHEN d.is_delivered = true AND d.channel = 'INAPP' AND d.inapp_seven_day_window_clicked_at IS NOT NULL THEN 1
            WHEN d.is_delivered = true AND d.channel != 'INAPP' AND d.seven_day_window_clicked_at IS NOT NULL THEN 1
            ELSE 0
        END) as clicadas_7d,
        -- OR: abertas / entregues
        ROUND(SUM(CASE
            WHEN d.is_delivered = true AND d.channel = 'INAPP' AND d.inapp_seven_day_window_opened_at IS NOT NULL THEN 1
            WHEN d.is_delivered = true AND d.channel != 'INAPP' AND d.seven_day_window_opened_at IS NOT NULL THEN 1
            ELSE 0
        END) * 100.0 / NULLIF(SUM(CASE WHEN d.is_delivered = true THEN 1 ELSE 0 END), 0), 2) as taxa_abertura,
        -- CTR: clicadas / entregues
        ROUND(SUM(CASE
            WHEN d.is_delivered = true AND d.channel = 'INAPP' AND d.inapp_seven_day_window_clicked_at IS NOT NULL THEN 1
            WHEN d.is_delivered = true AND d.channel != 'INAPP' AND d.seven_day_window_clicked_at IS NOT NULL THEN 1
            ELSE 0
        END) * 100.0 / NULLIF(SUM(CASE WHEN d.is_delivered = true THEN 1 ELSE 0 END), 0), 2) as taxa_clique
    FROM {TABLE_DISPARO} d
    WHERE d.notification_day_date >= DATE_SUB(CURRENT_DATE(), {days})
      {SEEDLIST_FILTER.replace('AND consumer_id', 'AND d.consumer_id')}
      {bu_clause}
    GROUP BY d.briefing_id
    HAVING entregues > 1000
    ORDER BY taxa_abertura DESC
    LIMIT {limit}
    """
    return execute_sql(sql)


def get_top_channels(days: int = 30, bu: str = None) -> dict:
    """Performance por canal. OR/CTR sobre entregues."""
    bu_clause = _bu_filter(bu)
    sql = f"""
    SELECT
        channel,
        COUNT(*) as enviados,
        SUM(CASE WHEN is_delivered = true THEN 1 ELSE 0 END) as entregues,
        ROUND(SUM(CASE WHEN is_delivered = true THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 2) as taxa_entrega,
        SUM(CASE
            WHEN is_delivered = true AND channel = 'INAPP' AND inapp_seven_day_window_opened_at IS NOT NULL THEN 1
            WHEN is_delivered = true AND channel != 'INAPP' AND seven_day_window_opened_at IS NOT NULL THEN 1
            ELSE 0
        END) as abertas_7d,
        ROUND(SUM(CASE
            WHEN is_delivered = true AND channel = 'INAPP' AND inapp_seven_day_window_opened_at IS NOT NULL THEN 1
            WHEN is_delivered = true AND channel != 'INAPP' AND seven_day_window_opened_at IS NOT NULL THEN 1
            ELSE 0
        END) * 100.0 / NULLIF(SUM(CASE WHEN is_delivered = true THEN 1 ELSE 0 END), 0), 2) as taxa_abertura,
        SUM(CASE
            WHEN is_delivered = true AND channel = 'INAPP' AND inapp_seven_day_window_clicked_at IS NOT NULL THEN 1
            WHEN is_delivered = true AND channel != 'INAPP' AND seven_day_window_clicked_at IS NOT NULL THEN 1
            ELSE 0
        END) as clicadas_7d,
        ROUND(SUM(CASE
            WHEN is_delivered = true AND channel = 'INAPP' AND inapp_seven_day_window_clicked_at IS NOT NULL THEN 1
            WHEN is_delivered = true AND channel != 'INAPP' AND seven_day_window_clicked_at IS NOT NULL THEN 1
            ELSE 0
        END) * 100.0 / NULLIF(SUM(CASE WHEN is_delivered = true THEN 1 ELSE 0 END), 0), 2) as taxa_clique,
        COUNT(DISTINCT briefing_id) as campanhas
    FROM {TABLE_DISPARO}
    WHERE notification_day_date >= DATE_SUB(CURRENT_DATE(), {days})
      {SEEDLIST_FILTER}
      {bu_clause}
    GROUP BY channel
    ORDER BY entregues DESC
    """
    return execute_sql(sql)


def get_top_products(days: int = 30, bu: str = None, limit: int = 15) -> dict:
    """Performance por produto. OR/CTR sobre entregues."""
    bu_clause = _bu_filter(bu)
    sql = f"""
    SELECT
        product_category,
        adjusted_bu_requester,
        COUNT(*) as enviados,
        SUM(CASE WHEN is_delivered = true THEN 1 ELSE 0 END) as entregues,
        SUM(CASE
            WHEN is_delivered = true AND channel = 'INAPP' AND inapp_seven_day_window_opened_at IS NOT NULL THEN 1
            WHEN is_delivered = true AND channel != 'INAPP' AND seven_day_window_opened_at IS NOT NULL THEN 1
            ELSE 0
        END) as abertas_7d,
        ROUND(SUM(CASE
            WHEN is_delivered = true AND channel = 'INAPP' AND inapp_seven_day_window_opened_at IS NOT NULL THEN 1
            WHEN is_delivered = true AND channel != 'INAPP' AND seven_day_window_opened_at IS NOT NULL THEN 1
            ELSE 0
        END) * 100.0 / NULLIF(SUM(CASE WHEN is_delivered = true THEN 1 ELSE 0 END), 0), 2) as taxa_abertura,
        SUM(CASE
            WHEN is_delivered = true AND channel = 'INAPP' AND inapp_seven_day_window_clicked_at IS NOT NULL THEN 1
            WHEN is_delivered = true AND channel != 'INAPP' AND seven_day_window_clicked_at IS NOT NULL THEN 1
            ELSE 0
        END) as clicadas_7d,
        ROUND(SUM(CASE
            WHEN is_delivered = true AND channel = 'INAPP' AND inapp_seven_day_window_clicked_at IS NOT NULL THEN 1
            WHEN is_delivered = true AND channel != 'INAPP' AND seven_day_window_clicked_at IS NOT NULL THEN 1
            ELSE 0
        END) * 100.0 / NULLIF(SUM(CASE WHEN is_delivered = true THEN 1 ELSE 0 END), 0), 2) as taxa_clique,
        COUNT(DISTINCT briefing_id) as campanhas
    FROM {TABLE_DISPARO}
    WHERE notification_day_date >= DATE_SUB(CURRENT_DATE(), {days})
      AND product_category IS NOT NULL
      AND product_category != ''
      {SEEDLIST_FILTER}
      {bu_clause}
    GROUP BY product_category, adjusted_bu_requester
    HAVING entregues > 1000
    ORDER BY entregues DESC
    LIMIT {limit}
    """
    return execute_sql(sql)


def get_top_hours(days: int = 30, bu: str = None) -> dict:
    """Performance por hora de envio. OR/CTR sobre entregues."""
    bu_clause = _bu_filter(bu)
    sql = f"""
    SELECT
        HOUR(sent_at) as hora,
        COUNT(*) as enviados,
        SUM(CASE WHEN is_delivered = true THEN 1 ELSE 0 END) as entregues,
        SUM(CASE
            WHEN is_delivered = true AND channel = 'INAPP' AND inapp_seven_day_window_opened_at IS NOT NULL THEN 1
            WHEN is_delivered = true AND channel != 'INAPP' AND seven_day_window_opened_at IS NOT NULL THEN 1
            ELSE 0
        END) as abertas_7d,
        ROUND(SUM(CASE
            WHEN is_delivered = true AND channel = 'INAPP' AND inapp_seven_day_window_opened_at IS NOT NULL THEN 1
            WHEN is_delivered = true AND channel != 'INAPP' AND seven_day_window_opened_at IS NOT NULL THEN 1
            ELSE 0
        END) * 100.0 / NULLIF(SUM(CASE WHEN is_delivered = true THEN 1 ELSE 0 END), 0), 2) as taxa_abertura,
        SUM(CASE
            WHEN is_delivered = true AND channel = 'INAPP' AND inapp_seven_day_window_clicked_at IS NOT NULL THEN 1
            WHEN is_delivered = true AND channel != 'INAPP' AND seven_day_window_clicked_at IS NOT NULL THEN 1
            ELSE 0
        END) as clicadas_7d,
        ROUND(SUM(CASE
            WHEN is_delivered = true AND channel = 'INAPP' AND inapp_seven_day_window_clicked_at IS NOT NULL THEN 1
            WHEN is_delivered = true AND channel != 'INAPP' AND seven_day_window_clicked_at IS NOT NULL THEN 1
            ELSE 0
        END) * 100.0 / NULLIF(SUM(CASE WHEN is_delivered = true THEN 1 ELSE 0 END), 0), 2) as taxa_clique
    FROM {TABLE_DISPARO}
    WHERE notification_day_date >= DATE_SUB(CURRENT_DATE(), {days})
      AND sent_at IS NOT NULL
      {SEEDLIST_FILTER}
      {bu_clause}
    GROUP BY HOUR(sent_at)
    HAVING entregues > 1000
    ORDER BY taxa_abertura DESC
    """
    return execute_sql(sql)


# ═══════════════════════════════════════════════════════════
# Queries prontas — LIFT Test
# ═══════════════════════════════════════════════════════════

def get_lift_results(briefing_id: str = None, days: int = None) -> dict:
    """Resultados de testes LIFT. Se briefing_id=None, retorna todos. days filtra por período."""
    conditions = []
    if briefing_id:
        conditions.append(f"briefing_id = '{briefing_id}'")
    if days:
        conditions.append(f"sent >= DATE_SUB(CURRENT_DATE(), {days})")
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    sql = f"""
    SELECT
        briefing_id,
        sent,
        treatment_audience,
        gc_audience,
        ROUND(treatment_kpi_result, 4) as treat_kpi,
        ROUND(gc_kpi_result, 4) as gc_kpi,
        ROUND(incremental_kpi_result, 4) as incremental,
        ROUND(incremental_kpi_result_wol, 4) as incremental_wol,
        ROUND(p_value, 4) as p_value,
        final_result,
        aprovation_date
    FROM {TABLE_LIFT}
    {where}
    ORDER BY sent DESC
    """
    return execute_sql(sql)


def get_campaign_full_debug(briefing_id: str) -> dict:
    """
    Debug completo: marcação + disparo + lift para um briefing.
    Retorna dict com as 3 fontes.
    """
    return {
        "marcacao": get_marcacao_stats(briefing_id),
        "disparo": get_dispatch_stats(briefing_id),
        "lift": get_lift_results(briefing_id),
    }
