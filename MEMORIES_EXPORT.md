# Growth Ops Copilot — Memórias do Agente Toninho
# Arquivo de exportação para importar no HubAI Nitro da nova responsável
# Gerado em: Abril/2026
# Formato: decision/fact/observation por bloco

---

## PROJETO

**fact** [projeto,identidade]
Projeto: Growth Ops Copilot — Bot Slack de inteligência operacional para o time de Growth CRM do PicPay. Integra Monday.com (board 9905091320) + Databricks + Slack. Código em C:\Users\SEU_USUARIO\Downloads\growth-bot\ (ou onde clonar o repo). Repositório: https://github.com/153107/bot-crm. Chave de ligação entre todas as fontes: briefing_id. Versão atual: v3.4.

---

## ARQUITETURA

**decision** [arquitetura,modulos]
9 módulos: app.py (entry point + scheduler 09h), config.py (constantes/mapeamentos), handlers.py (NLP + roteamento), monday_client.py (Monday GraphQL), databricks_client.py (SQL OAuth U2M), daily.py (Daily Intelligence genérico por área), formatters.py (Block Kit visual Slack), parsers.py (limpeza nomes campanha), databricks_oauth.py (auth).

**decision** [autenticacao,databricks,oauth]
Databricks usa OAuth U2M via CLI. Token renova automaticamente (1h). Setup: winget install Databricks.DatabricksCLI → databricks auth login --host https://picpay-principal.cloud.databricks.com --profile picpay. Se der "refresh token invalid": rodar o auth login novamente. Alternativa para servidor: variável DATABRICKS_TOKEN no .env (databricks_client.py aceita ambos).

---

## CANAIS E ÁREAS

**fact** [canais,slack,areas]
Canais Slack ativos:
- Banking: sfpf-banking-growth-crm (ID: C0A6SGP33RC)
- Payments: sfpf-payments-growth-crm (ID: C0A6UMYB4SW)
- Segmentos: sfpf-segmentos-growth-crm
Daily automático às 09h para: Banking, Payments, Segmentos (AREAS_DAILY no config.py).
Cross é consultável manualmente mas não tem canal próprio.

**decision** [escopo,areas]
4 áreas consultáveis: Banking, Payments, Segmentos, Cross. CRM fica fora do escopo. Filtro por área usa adjusted_bu_requester (mais confiável que bu_requester). Valores: "SFPF Banking", "SFPF Payments", "SFPF Segmentos", "SFPF Cross".

---

## FILTROS GLOBAIS (NUNCA REMOVER)

**decision** [filtros,monday,segurança]
Filtros globais Monday — aplicados em TODOS os endpoints via _is_valid_campaign() no monday_client.py:
- Canceladas: color_mkvfrrnv = "SIM" → excluir
- Testes: color_mkw8xn25 = "É TESTE" → excluir
Esses filtros são automáticos — qualquer consulta que chame get_campaigns() herda.

**decision** [filtros,databricks,seedlist]
Seedlist — 13 consumer_ids fixos excluídos de TODAS as queries Databricks via SEEDLIST_FILTER no config.py:
140307882125168218, 334428515250163706, 110542583387691346, 164032341298786597, 177744940880682527, 129603751216762637, 186354102042317401, 223734888742478217, 157769491182413978, 115782605936524514, 199984163564535194, 855574196516324388, 306199889496343350.

**decision** [filtros,databricks,threshold-seedlist]
Threshold seedlist em get_dispatch_stats() — dias com menos de 10% do volume do pico do touchpoint OU menos de 100 entregues são descartados como seedlist/testes. Código no filtered CTE: WHERE r.total_sent >= m.max_sent * 0.10 AND r.delivered >= 100. Pendente: validar com campanha 11491165427.

---

## MÉTRICAS

**decision** [metricas,janela-7d,denominador]
Métricas corretas (janela 7 dias, denominador = entregues):
- Entrega: is_delivered = true / total_sent
- OR (Abertura): seven_day_window_opened_at IS NOT NULL / entregues
- CTR (Clique): seven_day_window_clicked_at IS NOT NULL / entregues
- CTOR: clicadas_7d / abertas_7d (só EMAIL, INAPP, DM)
INAPP usa: inapp_seven_day_window_opened_at / inapp_seven_day_window_clicked_at (colunas exclusivas — opened_at e clicked_at são sempre NULL para INAPP).

**decision** [metricas,canais,sem-clique]
Canais SEM tracking de clique: PUSH, WHATSAPP, SMS → exibir ⚪ na coluna Clique, nunca mostrar CTR/CTOR.
Canal SEM abertura: SMS → omitir coluna Abertura.
WhatsApp "abertura" = entrega ao device (2 checks), não engajamento real.

**decision** [metricas,divergencia,aceita]
Divergência entre bot e relatórios externos é esperada e aceita. Causada por latência do pipeline de engajamento — relatório externo pode ter sido gerado antes dos engajamentos chegarem na tabela. O bot sempre reflete o estado atual da tabela (fonte de verdade). Investigado com campanha 11530378005 (DM) — confirmado não é bug.

---

## THRESHOLDS DE ENGAJAMENTO

**decision** [thresholds,visual]
Thresholds por canal (indicadores 🟢🟡🔴):
- INAPP: 🟢≥15% 🟡≥8% | PUSH: 🟢≥3% 🟡≥1.5% | EMAIL: 🟢≥15% 🟡≥8%
- DM: 🟢≥10% 🟡≥5% | WHATSAPP: 🟢≥40% 🟡≥20% | DELIVERY: 🟢≥95% 🟡≥85%
- Clique CTOR: INAPP 🟢≥1% 🟡≥0.3% | EMAIL 🟢≥1% 🟡≥0.3% | DM 🟢≥1.5% 🟡≥0.5%

---

## ESQUEMA DE CORES

**decision** [visual,emojis,cores]
Esquema de cores aplicado em todo o bot (formatters.py, config.py, daily.py, handlers.py):
- 🟢 Priorizadas / Concluída / CRM Feito
- 🟡 Backlog / Montar Segmento / Montar Jornada
- 🟠 Testes / Em Finalização / AppSheet
- 🔴 Fora do SLA / Bloqueada / Reprovada
- ⚠️ Excedendo o prazo (SLA em risco)
- 🔬 Teste LIFT

---

## FLUXOS DE CAMPANHA

**decision** [fluxo,growth,crm,sla]
Growth Flow (5 etapas): Planejado → Objetivos → Touchpoints → Criativos → Fora do Prazo. SLA só começa a contar quando chega em Criativos (aba 4). Abas 1-3 não entram no SLA.

CRM Flow (6 passos): Abrir Briefing → Montar Segmento → Montar Jornada → Testes → Em Finalização → Feito. Desvios: AppSheet (falta aprovação de ativação), Com Impedimento (bloqueio).

**decision** [backlog,crm,regra]
REGRA CRÍTICA: campanha em Backlog nunca exibe status CRM. Está com o Growth, o CRM não tocou nela. Implementado em formatters.py → traduzir_etapa(): se "backlog" in status_campanha.lower(), scr = "".

---

## NLP

**decision** [nlp,intents,prioridade]
NLP com weighted scoring. Prioridade de desempate: sla > campanha > lift > top > daily > upcoming > help. Cada padrão regex tem peso 1-3. Intent "campanha" cobre macro (pipeline área) e micro (detalhe específico). Briefing ID detectado dá bônus +5 pro intent campanha.

**decision** [nlp,upcoming,correcao]
"próximas campanhas de banking" rota corretamente para intent upcoming (não campanha). Padrões adicionados: próxim.{0,15}campanha e campanha.{0,15}proxim com peso 3.

**decision** [nlp,help]
Help reconhece: "me ajuda", "ajuda", "help", "como usar o growth ops", "como funciona", "como usar", "o que você faz/pode/sabe", "quais são as consultas/comandos", "pra que serve", "growth ops", "copilot", "não sei o que perguntar", "socorro".

---

## DAILY INTELLIGENCE

**decision** [daily,estrutura,areas]
Daily Intelligence genérico por área via AREA_CONFIG em daily.py. Aceita: Banking (🏦), Payments (💳), Segmentos (🎯), Cross (🔀). Estrutura: D-1 Monitoramento → Próximas (🟢 Priorizadas + 🟡 Backlog) → 🚨 SLA (🔴 Fora + ⚠️ Excedendo) → 🔬 Teste LIFT. Tudo em tabela monospace — nunca bullet points.

**decision** [daily,bug-corrigido]
Bug corrigido em daily.py: variáveis sla_excedido, sla_risco, priorizadas, backlog são inicializadas ANTES do bloco try/except do Monday. Evita UnboundLocalError quando Monday dá timeout.

---

## TABELAS DATABRICKS

**fact** [databricks,tabelas,schema]
Tabelas utilizadas:
- pf_growth_notifications_reporting (disparo, 43 cols, partição year/month/day_partition como STRING)
- pf_growth_campaign_message_events (marcação GT/GC/GCU, 23 cols, partição como INT)
- growth_adhoc_results (resultados LIFT)
Campo chave reporting: adjusted_bu_requester (mais confiável que bu_requester).
INAPP: opened_at e clicked_at são SEMPRE NULL → usar inapp_opened_at e inapp_clicked_at.

---

## MONDAY.COM

**fact** [monday,colunas,board]
Board ID: 9905091320. Colunas chave:
- name: nome raw (precisa passar por parse_campaign_name() antes de exibir)
- numeric_mkvccc73: briefing_id (chave de ligação com Databricks)
- status: macro-etapa (Backlog / Priorizadas / Concluída)
- color_mky1jm7j: Status CRM (Montar Segmento / Montar Jornada / etc.)
- date_mkv87hhf: data prevista de início
- numeric_mkynfjpx: Vol. Clientes SF (volume REAL, preferir sobre estimado)
- numeric_mkvn5qpc: Vol. Estimado (fallback)
- color_mkv9c29w: Área (Banking / Payments / Segmentos / Cross)
- color_mkvfrrnv: Canceladas (excluir se "SIM")
- color_mkw8xn25: is_teste (excluir se "É TESTE")

---

## FUNCIONALIDADES PENDENTES / BACKLOG

**decision** [pendencias,backlog]
Pendências conhecidas:
1. Top campanhas: implementado em handlers.py/_respond_top mas REMOVIDO do help intencionalmente — não está no ar ainda.
2. Threshold seedlist: correção aplicada (10% + 100 entregues) mas validação com campanha 11491165427 ficou pendente.
3. Daily Segmentos: canal configurado mas bot precisa ser adicionado ao canal sfpf-segmentos-growth-crm.
4. Orquestrador Monday W&B: projeto separado, substituir N8N por agente com webhooks. Fase: estudo puro.
5. GitHub Codespaces: devcontainer.json pronto, DATABRICKS_TOKEN como env var implementado. Falta configurar secrets no Codespace.

---

## PRINCÍPIOS INEGOCIÁVEIS

**decision** [principios,qualidade]
P1 - Consistência: nunca dado errado. Sem dado = "sem dados". Mostrar fonte + período sempre.
P2 - Linguagem acessível: "Clientes impactados" não consumer_id. Nomes via parse_campaign_name(). Erros amigáveis, sem traceback.
P3 - Métricas por canal: INAPP tem colunas próprias. PUSH/WhatsApp sem clique. Não consolidar canais num número só.
