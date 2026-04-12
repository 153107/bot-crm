# Growth Ops Copilot — Guia de Instalação

## Pré-requisitos

- Python 3.12+
- Git
- Windows 10/11

---

## 1. Instalar Python 3.12

Baixar em: https://www.python.org/downloads/
> ⚠️ Marcar "Add Python to PATH" durante a instalação

Verificar:
```
python --version
```

---

## 2. Copiar o projeto

Copiar a pasta `growth-bot` para `C:\Users\SEU_USUARIO\Downloads\growth-bot`

---

## 3. Instalar dependências

```bash
cd C:\Users\SEU_USUARIO\Downloads\growth-bot
pip install -r requirements.txt
```

---

## 4. Configurar o arquivo .env

Criar o arquivo `.env` na pasta do projeto com o conteúdo abaixo
(preencher os valores reais):

```env
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...
SLACK_APP_TOKEN=xapp-...
SLACK_CHANNEL_BANKING=sfpf-banking-growth-crm
SLACK_CHANNEL_SEGMENTOS=sfpf-segmentos-growth-crm
SLACK_CHANNEL_PAYMENTS=sfpf-payments-growth-crm
MONDAY_API_TOKEN=...
MONDAY_BOARD_ID=9905091320
```

---

## 5. Configurar Databricks (OAuth U2M)

### Instalar o CLI:
```
winget install Databricks.DatabricksCLI
```

### Autenticar (abre o browser):
```
databricks auth login --host https://picpay-principal.cloud.databricks.com --profile picpay
```

> O token renova automaticamente. Repetir este passo se receber erro de "refresh token invalid".

---

## 6. Iniciar o bot

### Manual (para testes):
```bash
cd C:\Users\SEU_USUARIO\Downloads\growth-bot
python app.py
```

### Automático no login do Windows:
O arquivo `GrowthOpsBot.bat` já está configurado na pasta Startup.
Copiar para:
```
C:\Users\SEU_USUARIO\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\
```

---

## 7. Verificar funcionamento

Enviar DM pro bot no Slack:
```
ajuda
```

O bot deve responder com o menu de consultas.

---

## Estrutura de arquivos

```
growth-bot/
├── app.py                  # Entry point
├── config.py               # Configurações e constantes
├── handlers.py             # NLP + roteamento Slack
├── monday_client.py        # Integração Monday.com
├── databricks_client.py    # Integração Databricks
├── daily.py                # Daily Intelligence
├── daily_dispatch.py       # Script standalone Daily
├── formatters.py           # Visual Slack (Block Kit)
├── parsers.py              # Parser nomes de campanha
├── databricks_oauth.py     # Auth Databricks
├── bot_service.py          # Wrapper auto-restart
├── requirements.txt        # Dependências Python
├── .env                    # ⚠️ Credenciais (NÃO commitar)
└── .devcontainer/          # Config GitHub Codespaces
    └── devcontainer.json
```

---

## Canais Slack configurados

| Área | Canal |
|------|-------|
| Banking | sfpf-banking-growth-crm |
| Payments | sfpf-payments-growth-crm |
| Segmentos | sfpf-segmentos-growth-crm |

---

## Daily Intelligence

- Roda automaticamente às **09h** (horário de Brasília) dias úteis
- Canais: Banking, Payments, Segmentos
- Pode ser disparado manualmente via DM: `daily banking`

---

## Credenciais necessárias

| Credencial | Onde obter |
|---|---|
| SLACK_BOT_TOKEN | api.slack.com → seu app → OAuth & Permissions |
| SLACK_SIGNING_SECRET | api.slack.com → seu app → Basic Information |
| SLACK_APP_TOKEN | api.slack.com → seu app → Basic Information → App-Level Tokens |
| MONDAY_API_TOKEN | monday.com → perfil → Developers → API |
| MONDAY_BOARD_ID | URL do board no Monday.com |
| Databricks OAuth | `databricks auth login` (ver passo 5) |

---

## Troubleshooting

### "refresh token is invalid"
Token Databricks expirou. Rodar:
```
databricks auth login --host https://picpay-principal.cloud.databricks.com --profile picpay
```

### Bot não responde no Slack
Verificar se o processo está rodando:
```powershell
Get-Process python
```

### D-1 vazio no Daily
Pipeline Databricks com atraso — normal quando não houve disparo no dia anterior ou pipeline atrasado.

### Monday timeout
API Monday instável momentaneamente — o bot exibe as seções disponíveis e ignora as que deram erro.
