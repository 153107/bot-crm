# Growth Ops Copilot

Bot de inteligÃªncia operacional para Growth CRM PicPay. Integra Monday.com + Databricks + Slack.

## Escopo

**4 Ã¡reas:** Banking, Payments, Segmentos, Cross (CRM fora do escopo)

---

## Projeto

**DiretÃ³rio:** `C:\Users\jf102696\Downloads\growth-bot\`

| Arquivo | FunÃ§Ã£o |
|---------|--------|
| `app.py` | Entry point (Socket Mode + scheduler 09h) |
| `config.py` | Constantes, mapeamentos de status/canais |
| `handlers.py` | Comandos Slack + NLP (weighted scoring) |
| `parsers.py` | Parser de nomes de campanha |
| `monday_client.py` | Client Monday.com API |
| `databricks_client.py` | Client Databricks (OAuth U2M) |
| `databricks_oauth.py` | AutenticaÃ§Ã£o OAuth U2M |
| `formatters.py` | Formatters visuais Slack |
| `daily.py` | Daily Intelligence (formato executivo Banking) |
| `daily_dispatch.py` | Script standalone (GitHub Actions) |

---

## Credenciais

### Slack
- **Socket Mode:** habilitado
- **Canal Banking:** `sfpf-banking-growth-crm` (privado, ID: `C0A6SGP33RC`)
- **Token:** `xoxb-SEU-TOKEN-AQUI`

### Monday.com
- **Board ID:** `9905091320`

### Databricks (OAuth U2M)
- **Host:** `https://picpay-principal.cloud.databricks.com`
- **Profile:** `picpay`
- **Warehouse:** `3b94f0935afb32db` (Exploracao 03)

```bash
# Setup OAuth (uma vez)
winget install Databricks.DatabricksCLI
databricks auth login --host https://picpay-principal.cloud.databricks.com --profile picpay
```

---

## âš ï¸ REGRA GLOBAL: Filtro de Campanhas

**SEMPRE excluir** campanhas com:
- `color_mkvfrrnv` (Canceladas) = "SIM"
- `color_mkw8xn25` (is_teste) = "Ã‰ TESTE"

```python
# Aplicado em _is_valid_campaign() dentro de get_campaigns() no monday_client.py
# Todos os endpoints herdam automaticamente (status, daily, SLA, debug, upcoming)
def _is_valid_campaign(c: dict) -> bool:
    cancelada = (c.get("color_mkvfrrnv") or "").lower()
    is_teste = (c.get("color_mkw8xn25") or "").lower()
    return "sim" not in cancelada and "teste" not in is_teste
```

---

## Monday.com (Colunas)

| Dado | ID | ObservaÃ§Ã£o |
|------|----|------------|
| Nome | `name` | |
| Briefing ID | `numeric_mkvccc73` | Chave de ligaÃ§Ã£o Databricks |
| Status Campanha | `status` | Backlog / Priorizadas / ConcluÃ­da |
| Status CRM | `color_mky1jm7j` | Passo do fluxo CRM |
| Dt InÃ­cio | `date_mkv87hhf` | Data prevista de disparo |
| Vol. Clientes SF | `numeric_mkynfjpx` | Volume real (SF) |
| Vol. Estimado | `numeric_mkvn5qpc` | Fallback quando SF vazio |
| Ãrea | `color_mkv9c29w` | Banking / Payments / Segmentos / Cross |
| Produto | `color_mkv95cyj` | |
| ResponsÃ¡vel | `person` | |
| **Canceladas** | `color_mkvfrrnv` | âš ï¸ Excluir se "SIM" |
| **is_teste** | `color_mkw8xn25` | âš ï¸ Excluir se "Ã‰ TESTE" |

---

## Consultas (7 intents)

### 1. `campanha` â€” Macro + Micro (unificado)

Intent unificado que substituiu `debug` + `status`. Fluxo de desambiguaÃ§Ã£o:

```
1. Tem briefing_id ou nome â†’ micro direto
2. Sinal forte de macro (Ã¡rea sozinha, "pipeline", "quantas") â†’ macro direto
3. AmbÃ­guo â†’ pergunta "1 Macro ou 2 Micro?"
```

**Macro** (`_execute_campanha_macro`): pipeline por status + breakdown CRM + bloqueadas â€” fonte Monday.  
**Micro** (`_execute_campanha_micro`): decide fonte pela etapa:
- Backlog / Priorizadas â†’ `format_micro_monday` (planejamento)
- ConcluÃ­da â†’ `format_micro_databricks` (mÃ©tricas reais)

FunÃ§Ãµes formatters:
- `format_macro_campanha(summary, area, mtd)` â€” visÃ£o macro
- `format_micro_monday(campaign)` â€” visÃ£o micro prÃ©-disparo
- `format_micro_databricks(campaign, db_data, allowed_channels)` â€” visÃ£o micro pÃ³s-disparo
- `format_status_summary(...)` â€” alias de compatibilidade â†’ chama `format_macro_campanha`

**Nitro Link:** https://nitro-link.ppay.me/html/35bc3e548a40/351fad72476e5fb2-status-campanhas-completo.html

---

### 2. `lift` â€” Resultados de Teste LIFT

Fonte: Databricks `growth_adhoc_results`. Enrichment com nomes do Monday.  
Filtra por Ã¡rea via cross-reference Monday (campo `color_mkv9c29w`).  
Exibe: resultado (âœ…/âŒ/ðŸ”„), p-value, incremento, data.

**Nitro Link:** https://nitro-link.ppay.me/html/35bc3e548a40/23f74ab27e7b4e1e-resultado-lift-completo.html

---

### 3. `top` â€” Top Campanhas por Performance

Fonte: Databricks `pf_growth_notifications_reporting`.  
Agrupa por `briefing_id` (1 linha por campanha, todos os canais consolidados).  
Ordena por taxa de abertura (nÃ£o clique â€” PUSH/WhatsApp nÃ£o tÃªm clique).  
Filtro duplo de BU: `adjusted_bu_requester` OR sigla na taxonomia.

---

### 4. `daily` â€” Daily Intelligence D-1

Fonte: Databricks (disparo) + Monday (planejamento + SLA).  
Formato executivo monospace. Uma linha por campanha Ã— canal.

**Nitro Link:** https://nitro-link.ppay.me/html/35bc3e548a40/a10cd544e9c692c2-daily-intelligence-completo.html

---

### 5. `sla` â€” Campanhas Fora do SLA

Fonte: Monday. Regras:
- ðŸ”´ Excedido: inÃ­cio â‰¤ hoje, ainda em Backlog
- ðŸŸ¡ Risco: inÃ­cio em atÃ© 4 dias, nÃ£o priorizada

**Nitro Link:** https://nitro-link.ppay.me/html/35bc3e548a40/e730b929645a2a12-sla-crm-completo.html

---

### 6. `upcoming` â€” PrÃ³ximas Campanhas

Fonte: Monday. PrÃ³ximos 7 dias. Exibe etapa traduzida (`traduzir_etapa()`).

**Nitro Link:** https://nitro-link.ppay.me/html/35bc3e548a40/e4244f8029a1a9c1-proximas-campanhas-completo.html

---

### 7. `help` â€” Ajuda

Lista todas as consultas disponÃ­veis com exemplos naturais.

---

## Daily Intelligence Banking

### Formato Executivo (monospace)

```
ðŸ¦ Daily Intelligence | Banking Growth
RelatÃ³rio de Performance e OperaÃ§Ã£o â€” DD/MM/YYYY

ðŸ“¡ D-1 | Monitoramento de Campanhas
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ Campanha                â”‚ Canal    â”‚ Volume   â”‚ Entrega  â”‚ Abertura â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ PICPAY MAIS             â”‚ Push     â”‚ 1.2M     â”‚ 99% ðŸŸ¢   â”‚ 2.1% ðŸ”´  â”‚
â”‚ PICPAY MAIS             â”‚ Email    â”‚ 600K     â”‚ 99% ðŸŸ¢   â”‚ 3.2% ðŸŸ¡  â”‚
â”‚ CASHIN                  â”‚ InApp    â”‚ 10.5K    â”‚ 83% ðŸŸ¡   â”‚ 8.5% ðŸŸ¢  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
Resumo: X campanhas | Y entregas | Abertura mÃ©dia: Z%

ðŸš€ | PrÃ³ximas Campanhas
â­ Priorizadas â†’ ID | Campanha | Status CRM | InÃ­cio
ðŸ“‚ Backlog (N com data prevista) â†’ ID | Campanha | InÃ­cio

ðŸš¨ Aviso de SLA
â— Fora do SLA â†’ ID | Campanha | InÃ­cio | Atraso
âš ï¸ Excedendo o prazo â†’ ID | Campanha | InÃ­cio | Faltam

ðŸ§ª Teste LIFT
ID | Campanha | Status | p-value | Incremento
```

### MÃ©tricas de Engajamento â€” Conceitos Oficiais

| MÃ©trica | Numerador | Denominador | Filtro base |
|---------|-----------|-------------|-------------|
| % Entrega | `is_delivered = true` | total enviados | â€” |
| OR (Abertura 7d) | `seven_day_window_opened_at IS NOT NULL` | entregues | `is_delivered = true` |
| CTR (Clique 7d) | `seven_day_window_clicked_at IS NOT NULL` | entregues | `is_delivered = true` |
| CTOR | clicadas_7d | abertas_7d | `is_delivered = true` |

- **INAPP** usa colunas dedicadas: `inapp_seven_day_window_opened_at` / `inapp_seven_day_window_clicked_at`
- **WhatsApp** "abertura" = 2 checks (entregue ao device), nÃ£o engajamento real
- **PUSH / WhatsApp / SMS**: sem tracking de clique â€” exibe `âšª` na coluna Clique
- **CTOR** disponÃ­vel apenas para: EMAIL, INAPP, DM

### Agrupamento de Disparo

`get_dispatch_stats` agrupa por `channel + campaign_name + DATE(sent_at)`:
- `campaign_name` identifica o touchpoint Ãºnico na tabela de reporting
- Dentro de cada touchpoint, dias com volume < 1% do pico sÃ£o descartados (seedlist/teste)
- Os dias restantes sÃ£o consolidados numa linha com a data do dia de maior volume
- `first_sent = MIN(sent_at)` dentro do grupo = hora exata de inÃ­cio

Header exibido: `"23/03/2026 Â· inÃ­cio Ã s 10h54"`

### Seedlist â€” ExclusÃ£o Global

13 `consumer_id` fixos excluÃ­dos de **todas** as queries de disparo.  
Definidos em `config.py` como `SEEDLIST_CONSUMER_IDS` + clÃ¡usula `SEEDLIST_FILTER`.  
Aplicado em: `get_dispatch_stats`, `get_daily_dispatch_summary`, `get_best_performers`, `get_top_campaigns`, `get_top_channels`, `get_top_products`, `get_top_hours`, `daily.py`.

```python
# config.py
SEEDLIST_CONSUMER_IDS = (
    "140307882125168218", "334428515250163706", "110542583387691346",
    "164032341298786597", "177744940880682527", "129603751216762637",
    "186354102042317401", "223734888742478217", "157769491182413978",
    "115782605936524514", "199984163564535194", "855574196516324388",
    "306199889496343350",
)
SEEDLIST_FILTER = f"AND consumer_id NOT IN ({', '.join(repr(i) for i in SEEDLIST_CONSUMER_IDS)})"
```

### Thresholds de Engajamento

```python
ENGAGEMENT_THRESHOLDS = {
    "INAPP":     {"good": 15, "medium": 8},    # ðŸŸ¢ â‰¥15% | ðŸŸ¡ â‰¥8% | ðŸ”´ <8%
    "PUSH":      {"good": 3,  "medium": 1.5},
    "EMAIL":     {"good": 15, "medium": 8},
    "DM":        {"good": 10, "medium": 5},
    "WHATSAPP":  {"good": 40, "medium": 20},
    "SMS":       {"good": 5,  "medium": 2},
    # Clique CTOR (EMAIL, INAPP, DM)
    "INAPP_CTR": {"good": 1,  "medium": 0.3},
    "EMAIL_CTR": {"good": 1,  "medium": 0.3},
    "DM_CTR":    {"good": 1.5,"medium": 0.5},
}
DELIVERY_THRESHOLD = {"good": 95, "medium": 85}
```

### Regras de SLA

```python
# ðŸ”´ SLA EXCEDIDO: inÃ­cio â‰¤ hoje, ainda em Backlog
if dias_para_inicio <= 0:
    status = "excedido"

# ðŸŸ¡ RISCO: inÃ­cio em atÃ© 4 dias, nÃ£o priorizada
elif dias_para_inicio <= 4:
    status = "risco"
```

---

## NLP (handlers.py)

### Intents e Prioridade

```python
priority_order = ["sla", "campanha", "lift", "top", "daily", "upcoming", "help"]
```

### Intent Detection (weighted scoring)

```python
_INTENT_PATTERNS = {
    "campanha": [
        # Micro signals
        (r"\bdebug\b", 3),
        (r"\bdetalh", 2),
        (r"\bbriefing\b", 2),
        (r"\bme (?:fala|conta|mostra).{0,20}(?:campanha|briefing)\b", 2),
        (r"\bcomo (?:tÃ¡|ta|estÃ¡|esta|foi|anda).{0,20}(?:campanha|briefing)\b", 2),
        # Macro signals
        (r"\bstatus\b", 3),
        (r"\bvis[aÃ£]o geral\b", 2),
        (r"\bquantas campanhas\b", 2),
        (r"\bpipeline\b", 1),
        # Ãrea sozinha â†’ macro
        (r"^(e\s+)?(banking|bank|banco)(\?)?$", 3),
        (r"^(e\s+)?(payments?|pay|pagamentos?)(\?)?$", 3),
        (r"^(e\s+)?(segmentos?|seg)(\?)?$", 3),
        (r"^(e\s+)?(cross)(\?)?$", 3),
    ],
    "lift": [
        (r"\blift\b", 3),
        (r"\bincrementalidade\b", 3),
        (r"\bp[_-]?value\b", 3),
    ],
    "top": [
        (r"\btop\b", 3),
        (r"\bmelhor(?:es)?\s+campanha", 3),
        (r"\branking\b", 3),
        (r"\bperformance\b", 2),
    ],
    "sla": [
        (r"\bsla\b", 3),
        (r"\batrasa", 3),
        (r"\bfora do (?:sla|prazo)\b", 3),
        (r"\bprazo\b", 2),
    ],
    "daily": [
        (r"\bdaily\b", 3),
        (r"\bd-?1\b", 3),
        (r"\bontem\b", 2),
    ],
    "upcoming": [
        (r"\bprÃ³xim", 2),
        (r"\bprevist", 2),
        (r"\bupcoming\b", 3),
    ],
    "help": [
        (r"\bajuda\b", 3),
        (r"\bhelp\b", 3),
    ],
}
```

### Clarification Options

```python
_CLARIFICATION_OPTIONS = {
    "lift": {
        "1": "ultimos 30 dias",
        "2": "historico completo",
        "3": None,  # pede briefing_id
    },
    "campanha": {
        "1": "__macro__",   # vai pra _execute_campanha_macro
        "2": "__micro__",   # pede nome ou briefing_id
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
```

---

## Fluxos de Campanhas

### Growth Flow (5 etapas)
`Planejado` â†’ `Objetivos` â†’ `Touchpoints` â†’ `Criativos` â†’ `Fora do Prazo`  
SLA comeÃ§a a contar quando chega em **Criativos** (aba 4).

### CRM Flow (8 status)
`Abrir Briefing` â†’ `Montar Segmento` â†’ `Montar Jornada` â†’ `Testes` â†’ `Em FinalizaÃ§Ã£o` â†’ `Feito`  
Desvios: `AppSheet` (falta aprovaÃ§Ã£o), `Com Impedimento` (bloqueio)

```python
STATUS_CRM_ORDER = {
    "abrir briefing": 1, "montar segmento": 2, "montar jornada": 3,
    "testes": 4, "em finalizaÃ§Ã£o": 5, "feito": 6,
    "appsheet": -1, "com impedimento": -1,
}
```

---

## Mapeamentos

### Canais (14 canais, 6 reportÃ¡veis)

```python
CHANNEL_DISPLAY_NAME = {
    "INAPP": "InApp", "PUSH": "Push", "EMAIL": "Email",
    "DM": "DM", "WHATSAPP": "WhatsApp", "SMS": "SMS",
}
REPORTABLE_DB_CHANNELS = {"INAPP", "PUSH", "EMAIL", "DM", "WHATSAPP", "SMS"}
CHANNELS_NO_CLICK = {"PUSH", "WHATSAPP", "SMS"}
CHANNELS_NO_OPEN  = {"SMS"}
```

### BUs

```python
AREA_TO_BU = {
    "Banking":   "SFPF Banking",
    "Payments":  "SFPF Payments",
    "Segmentos": "SFPF Segmentos",
    "Cross":     "SFPF Cross",
}
# Siglas de taxonomia no Databricks
BU_TAXONOMY_SIGLA = {
    "Banking":   "sfpfban",
    "Payments":  "sfpfpay",
    "Segmentos": "sfpfseg",
    "Cross":     "sfpfcro",
}
```

---

## Tabelas Databricks

| Tabela | ConteÃºdo | PartiÃ§Ã£o |
|--------|----------|----------|
| `pf_growth_notifications_reporting` | Disparo (43 cols) | `year/month/day_partition` (string) |
| `pf_growth_campaign_message_events` | MarcaÃ§Ã£o (23 cols) | `year/month/day_partition` (int) |
| `growth_adhoc_results` | Resultados LIFT | â€” |

**Campo chave reporting:** `adjusted_bu_requester` (mais confiÃ¡vel que `bu_requester`)  
**Campo INAPP:** usa `inapp_opened_at` / `inapp_clicked_at` (colunas dedicadas, nÃ£o `opened_at`)

---

## Nitro Links (documentaÃ§Ã£o)

| Consulta | Link |
|----------|------|
| ðŸ“š DocumentaÃ§Ã£o v3.4 | https://nitro-link.ppay.me/html/35bc3e548a40/dfca8bf69ab3511b-growth-ops-copilot-v34.html |
| ðŸ“¡ Daily Intelligence | https://nitro-link.ppay.me/html/35bc3e548a40/a10cd544e9c692c2-daily-intelligence-completo.html |
| ðŸ§ª Resultado LIFT | https://nitro-link.ppay.me/html/35bc3e548a40/23f74ab27e7b4e1e-resultado-lift-completo.html |
| ðŸ“Š Campanhas (Macro + Micro) | https://nitro-link.ppay.me/html/35bc3e548a40/2410b1d086af0924-status-campanhas-completo.html |
| â° SLA CRM | https://nitro-link.ppay.me/html/35bc3e548a40/e730b929645a2a12-sla-crm-completo.html |
| ðŸ“… PrÃ³ximas Campanhas | https://nitro-link.ppay.me/html/35bc3e548a40/e4244f8029a1a9c1-proximas-campanhas-completo.html |

---

## 3 PrincÃ­pios

1. **ConsistÃªncia:** Nunca dado errado. Sem dado = "sem dados". Mostrar fonte + perÃ­odo sempre.
2. **Linguagem:** "Clientes impactados" (nÃ£o consumer_id). Nome sempre via `parse_campaign_name()`. Erros = mensagem amigÃ¡vel, sem traceback.
3. **MÃ©tricas por canal:** INAPP tem colunas prÃ³prias. PUSH/WhatsApp nÃ£o tÃªm clique. NÃ£o consolidar canais num nÃºmero sÃ³ no Daily.

---

## Status do Projeto

âœ… OAuth U2M Databricks configurado  
âœ… Filtro global `_is_valid_campaign()` em todos os endpoints  
âœ… Daily Banking formato executivo monospace  
âœ… NLP v3 â€” weighted scoring + desambiguaÃ§Ã£o  
âœ… Intent `campanha` unificado (debug + status merged)  
âœ… `format_macro_campanha` + `format_micro_monday` + `format_micro_databricks`  
âœ… `daily_dispatch.py` (GitHub Actions standalone)  
â³ Deploy automÃ¡tico 09h (GitHub Actions workflow)

