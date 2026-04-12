"""
Databricks OAuth Helper — Conecta via OAuth U2M (User-to-Machine)

Uso:
    from databricks_oauth import get_workspace_client, execute_query

    # Pra SDK completo
    w = get_workspace_client()
    me = w.current_user.me()

    # Pra queries SQL
    result = execute_query("SELECT 1 AS teste")
    print(result)
"""
import subprocess
import json
import os
from functools import lru_cache

# Config
DATABRICKS_HOST = "https://picpay-principal.cloud.databricks.com"
DATABRICKS_PROFILE = "picpay"
DATABRICKS_CLI_PATH = os.path.join(
    os.environ.get("LOCALAPPDATA", ""),
    "Microsoft", "WinGet", "Packages",
    "Databricks.DatabricksCLI_Microsoft.Winget.Source_8wekyb3d8bbwe",
    "databricks.exe"
)

# Warehouse padrão (Exploracao 03 - o que vc já usava)
DEFAULT_WAREHOUSE_ID = "3b94f0935afb32db"


def _get_oauth_token() -> str:
    """Pega token OAuth do CLI (auto-refresh se expirado)."""
    result = subprocess.run(
        [DATABRICKS_CLI_PATH, "auth", "token", 
         "--host", DATABRICKS_HOST, "--profile", DATABRICKS_PROFILE],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Falha ao obter token OAuth: {result.stderr}")
    
    token_data = json.loads(result.stdout)
    return token_data["access_token"]


def get_workspace_client():
    """Retorna WorkspaceClient autenticado via OAuth."""
    from databricks.sdk import WorkspaceClient
    
    token = _get_oauth_token()
    return WorkspaceClient(host=DATABRICKS_HOST, token=token)


def execute_query(sql: str, warehouse_id: str = None, timeout: int = 300) -> dict:
    """Executa query SQL e retorna resultado.
    
    Args:
        sql: Query SQL
        warehouse_id: ID do warehouse (default: Exploracao 03)
        timeout: Timeout em segundos pra queries pesadas
    
    Returns:
        {"status": "OK", "columns": [...], "data": [...], "row_count": N}
        ou {"status": "FAILED", "error": "..."}
    """
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.service.sql import StatementState
    import time
    
    warehouse_id = warehouse_id or DEFAULT_WAREHOUSE_ID
    token = _get_oauth_token()
    w = WorkspaceClient(host=DATABRICKS_HOST, token=token)
    
    # Submeter query (async pra queries pesadas)
    response = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=sql,
        wait_timeout="50s",  # max sync wait
    )
    
    # Se já completou
    if response.status.state == StatementState.SUCCEEDED:
        columns = [col.name for col in response.manifest.schema.columns]
        data = response.result.data_array if response.result else []
        return {"status": "OK", "columns": columns, "data": data, "row_count": len(data)}
    
    # Se falhou
    if response.status.state in (StatementState.FAILED, StatementState.CANCELED):
        error = response.status.error.message if response.status.error else "Erro desconhecido"
        return {"status": "FAILED", "error": error}
    
    # Ainda rodando → polling
    statement_id = response.statement_id
    elapsed = 50  # já esperou 50s
    
    while elapsed < timeout:
        time.sleep(5)
        elapsed += 5
        
        status = w.statement_execution.get_statement(statement_id)
        
        if status.status.state == StatementState.SUCCEEDED:
            columns = [col.name for col in status.manifest.schema.columns]
            data = status.result.data_array if status.result else []
            return {"status": "OK", "columns": columns, "data": data, "row_count": len(data)}
        
        if status.status.state in (StatementState.FAILED, StatementState.CANCELED):
            error = status.status.error.message if status.status.error else "Erro desconhecido"
            return {"status": "FAILED", "error": error}
    
    # Timeout → cancela
    w.statement_execution.cancel_execution(statement_id)
    return {"status": "TIMEOUT", "error": f"Query excedeu {timeout}s e foi cancelada"}


def list_warehouses() -> list:
    """Lista warehouses disponíveis."""
    w = get_workspace_client()
    return [
        {"id": wh.id, "name": wh.name, "state": str(wh.state)}
        for wh in w.warehouses.list()
    ]


# ═══════════════════════════════════════════════════════════
# Teste rápido
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("🔐 Testando conexão OAuth...")
    
    w = get_workspace_client()
    me = w.current_user.me()
    print(f"✅ Conectado como: {me.user_name}")
    
    print("\n📊 Warehouses:")
    for wh in list_warehouses()[:5]:
        print(f"  - {wh['name']} ({wh['id']}) [{wh['state']}]")
    
    print("\n🔍 Testando query...")
    result = execute_query("SELECT 1 AS teste, 'OAuth funcionando!' AS msg")
    print(f"  Status: {result['status']}")
    if result["status"] == "OK":
        print(f"  Colunas: {result['columns']}")
        print(f"  Dados: {result['data']}")
