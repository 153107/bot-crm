# Handover — Growth Ops Copilot
**De:** Jackeliny Bicalho  
**Para:** Nova responsável  
**Data:** Abril/2026  
**Versão do bot:** v3.4

---

## O que é esse projeto

Bot de Slack chamado **Toninho do Workflow CRM** — inteligência operacional do time de Growth CRM do PicPay. Ele centraliza dados de Monday.com, Databricks e testes LIFT em linguagem natural.

Em vez de abrir cada sistema separado, qualquer pessoa do time manda uma mensagem pro bot e recebe a resposta na hora.

---

## Onde está tudo

| Item | Local |
|------|-------|
| Código do bot | `C:\Users\jf102696\Downloads\growth-bot\` (na máquina da Jackeliny) |
| Repositório GitHub | https://github.com/153107/bot-crm |
| Skill HubAI Nitro | `~/.wolf/skills/growth-ops-copilot/SKILL.md` |
| Credenciais | `.env` na pasta do projeto (NÃO está no GitHub) |

---

## Credenciais necessárias

Solicitar à Jackeliny antes do handover:

| Credencial | Onde usar |
|---|---|
| `SLACK_BOT_TOKEN` | xoxb-... (token do bot no Slack) |
| `SLACK_SIGNING_SECRET` | Segredo de assinatura do app Slack |
| `SLACK_APP_TOKEN` | xapp-... (token Socket Mode) |
| `MONDAY_API_TOKEN` | Token da API do Monday.com |
| `MONDAY_BOARD_ID` | `9905091320` (board de campanhas) |
| Databricks OAuth | Rodar `databricks auth login` na nova máquina |

---

## Canais Slack onde o bot está ativo

| Área | Canal | Canal ID |
|------|-------|----------|
| Banking | `sfpf-banking-growth-crm` | `C0A6SGP33RC` |
| Payments | `sfpf-payments-growth-crm` | `C0A6UMYB4SW` |
| Segmentos | `sfpf-segmentos-growth-crm` | (verificar após adicionar bot) |

**Importante:** o bot precisa ser adicionado manualmente a cada canal privado (Configurações do canal → Integrações → Adicionar app).

---

## O que o bot faz (7 consultas)

| Intent | Como acionar | Fonte |
|--------|-------------|-------|
| `campanha` | "como tá Banking?" / "detalha 11491165427" | Monday + Databricks |
| `daily` | "daily banking" / "como foi ontem?" | Databricks + Monday |
| `sla` | "tem campanha atrasada?" / "SLA" | Monday |
| `lift` | "resultados de lift Banking" | Databricks |
| `upcoming` | "próximas campanhas de banking" | Monday |
| `top` | "top campanhas" *(implementado, não divulgado)* | Databricks |
| `help` | "me ajuda" / "como usar" | — |

---

## Daily Intelligence automático

- Roda às **09h** todos os dias úteis
- Posta nos 3 canais: Banking, Payments, Segmentos
- Estrutura: D-1 Monitoramento → Próximas Campanhas → SLA → Teste LIFT
- Se D-1 vier vazio: pipeline Databricks com atraso — é esperado

---

## Esquema de cores dos retornos

| Cor | Significado |
|-----|------------|
| 🟢 | Priorizadas / Concluída / CRM Feito |
| 🟡 | Backlog / Montar Segmento / Montar Jornada |
| 🟠 | Testes / Em Finalização / AppSheet |
| 🔴 | Fora do SLA / Bloqueada / Reprovada |
| ⚠️ | Excedendo o prazo (SLA em risco) |
| 🔬 | Teste LIFT |

---

## 3 Princípios inegociáveis

1. **Consistência de dados** — nunca responde dado errado. Se não tem, diz "sem dados".
2. **Linguagem acessível** — "Clientes impactados" (não consumer_id). Nomes limpos de campanha. Erros amigáveis.
3. **Métricas por canal** — INAPP tem colunas próprias. PUSH/WhatsApp sem clique. Nunca consolidar canais.

---

## Filtros globais (NUNCA remover)

- **Canceladas:** `color_mkvfrrnv = "SIM"` → excluídas de todas as queries Monday
- **Testes:** `color_mkw8xn25 = "É TESTE"` → excluídas de todas as queries Monday
- **Seedlist:** 13 consumer_ids fixos excluídos de todas as queries Databricks
- **Dias residuais:** dias com <10% do volume do pico OU <100 entregues são descartados

---

## Tabelas Databricks utilizadas

| Tabela | Uso |
|--------|-----|
| `picpay.self_service_analytics.pf_growth_notifications_reporting` | Disparo (métricas de entrega/abertura/clique) |
| `picpay.self_service_analytics.pf_growth_campaign_message_events` | Marcação (GT/GC/GCU) |
| `picpay.self_service_analytics.growth_adhoc_results` | Resultados LIFT |

**Campo chave:** usar sempre `adjusted_bu_requester` (não `bu_requester`) para filtrar por área.

---

## Métricas — conceitos corretos

| Métrica | Numerador | Denominador |
|---------|-----------|-------------|
| Entrega | `is_delivered = true` | enviados |
| OR (Abertura 7d) | `seven_day_window_opened_at IS NOT NULL` | entregues |
| CTR (Clique 7d) | `seven_day_window_clicked_at IS NOT NULL` | entregues |
| CTOR | clicadas_7d | abertas_7d |

**INAPP:** usa `inapp_seven_day_window_opened_at` e `inapp_seven_day_window_clicked_at` (colunas exclusivas).  
**PUSH / WhatsApp / SMS:** sem clique — exibe ⚪.

---

## Divergência de métricas (aceita)

Pode haver divergência pequena entre o bot e relatórios externos — causada por latência do pipeline. Os engajamentos (`seven_day_window_*`) chegam com atraso na tabela. O bot sempre reflete o estado atual da tabela, que é a fonte de verdade.

---

## Fluxo de campanhas

**Growth (5 etapas):** Planejado → Objetivos → Touchpoints → Criativos → Fora do Prazo  
**SLA começa:** quando chega em Criativos (aba 4).

**CRM (6 passos):** Abrir Briefing → Montar Segmento → Montar Jornada → Testes → Em Finalização → Feito  
**Desvios:** AppSheet (falta aprovação) · Com Impedimento (bloqueio)

**Regra importante:** campanha em **Backlog nunca mostra status CRM** — está com o Growth, o CRM não tocou nela.

---

## Instalação em nova máquina

Ver `INSTALL.md` no repositório: https://github.com/153107/bot-crm

Passos principais:
1. Clonar o repo
2. `pip install -r requirements.txt`
3. Criar `.env` com as credenciais (usar `.env.example` como base)
4. `databricks auth login --host https://picpay-principal.cloud.databricks.com --profile picpay`
5. `python app.py`

---

## Manutenção recorrente

| Tarefa | Frequência | Como |
|--------|-----------|------|
| Renovar token Databricks OAuth | Quando der erro "refresh token invalid" | `databricks auth login --profile picpay` |
| Reiniciar bot após mudanças | A cada deploy | `python app.py` (ou via bot_service.py) |
| Verificar log | Se bot não responder | `service.log` na pasta do projeto |

---

## Pendências / Backlog

- [ ] **Top campanhas** — implementado mas não divulgado ainda (retirado do help intencionalmente)
- [ ] **Threshold seedlist** — testado parcialmente com campanha 11491165427; validar se 10% + 100 entregues resolve todos os casos
- [ ] **Hospedar no GitHub Codespaces** — configuração do devcontainer já está pronta (`.devcontainer/devcontainer.json`)
- [ ] **Daily Segmentos** — canal `sfpf-segmentos-growth-crm` configurado, mas bot precisa ser adicionado ao canal
- [ ] **Orquestrador Monday W&B** — projeto separado em estudo puro (substituir N8N por agente com webhooks)

---

## Skill HubAI Nitro (Toninho)

A skill está em `skill/SKILL.md` no GitHub. Para instalar na nova máquina:

```bash
mkdir -p ~/.wolf/skills/growth-ops-copilot
cp skill/SKILL.md ~/.wolf/skills/growth-ops-copilot/SKILL.md
```

O agente **Toninho do Workflow CRM** no HubAI Nitro é o copiloto de desenvolvimento — ele conhece toda a arquitetura, decisões técnicas e histórico do projeto.

---

## Contato para dúvidas

Jackeliny Bicalho — `Jackeliny.Santos@picpay.com`
