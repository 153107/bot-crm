# Relatório Executivo — Growth & CRM (Wallet & Banking)

> **Racional de construção, regras de negócio e guia de parametrização.**
> Atualizado em: Abril/2026

---

## 1. Visão Geral

Relatório HTML visual (light mode) com KPIs de Growth e CRM da BU de Wallet & Banking do PicPay.
Gerado a partir de queries no Databricks, renderizado com Chart.js + tabelas estilizadas.

### Estrutura

| Sessão | Seção | Conteúdo |
|--------|-------|----------|
| **1. Volumetria** | 1.1 | Big Numbers (envios, usuários, campanhas, freq/user, entrega) |
| | 1.2 | Ranking de Campanhas (Rádio + Top 10 Não-Rádio) |
| | 1.3 | Disparos por Canal — 6 meses (stacked bar) |
| | 1.4 | Taxa de Entrega (diagnóstico de queda) |
| | 1.5 | Réguas vs Ações Pontuais — 6 meses |
| | 1.6 | MAU App vs Não-MAU App — 6 meses |
| | 1.7 | Disparos por Vertical — 4 meses (stacked bar) |
| | 1.8 | Vertical x Produto Macro — 3 meses (tabelas com/sem rádio) |
| | 1.9 | Mix de Verticais e Produtos por Usuário MAU (donut + top 10 combos Fev vs Mês) |
| **2. Engajamento** | 2.1 | Denominadores de Engajamento (envios, aberturas, cliques por canal) |
| | 2.2 | KPIs: OR, CTR, CTOR por Canal — 3 meses (consolidado BU) |
| | 2.2b | KPIs por Vertical — Payments, Banking, Segmentos |
| | 2.3 | Campanhas Destaque — normalizado por faixa de audiência |

---

## 2. Fonte de Dados

### Tabela principal
```
picpay.self_service_analytics.pf_growth_notifications_reporting
```

**Filtros base:**
- `is_delivered = true` — apenas envios entregues
- `channel IN ('EMAIL','DM','PUSH','INAPP')` — canais com tracking
- SMS e Banner **excluídos** de todos os cálculos (sem tracking de abertura/clique)
- WhatsApp: apenas volumetria (OR = delivery rate, sem tracking real)

### Tabela de nomes de campanhas
```
picpay.validation.tb_book_growth_nome_campanhas
```
- JOIN via `briefing_id`
- Campo `nome` usado para classificação (ex: identificar rádio)
- Fallback: `campaign_name` quando `nome` é NULL

### Tabela MAU App
```
picpay.consumers.daily_app_accesses
```
- `consumer_id` com `access_date` no período
- Usado na seção 1.6 (MAU vs não-MAU) e 1.9 (mix por usuário MAU)

### Campo de vertical
```
adjusted_bu_requester
```
- **Atenção:** Valores mudaram para formato `SFPF Banking`, `SFPF Payments`, `SFPF Segmentos`
- Sempre usar `REPLACE(adjusted_bu_requester, 'SFPF ', '')` para normalizar

### Partições
- `year_partition` — string ou int, sempre fazer CAST
- `month_partition` — string ou int, sempre fazer CAST
- Filtrar com: `CAST(year_partition AS INT) = YYYY AND CAST(month_partition AS INT) = M`

---

## 3. Regras de Negócio por Canal

| Canal | OR (Open Rate) | CTR (Click-Through Rate) | CTOR (Click-to-Open Rate) | KPI Primário |
|-------|----------------|--------------------------|---------------------------|--------------|
| **Email** | `seven_day_window_opened_at` / envios | `seven_day_window_clicked_at` / envios | cliques / aberturas | OR |
| **DM** | `seven_day_window_opened_at` / envios | `seven_day_window_clicked_at` / envios | cliques / aberturas | OR |
| **Push** | N/A (abertura = clique) | `seven_day_window_opened_at` / envios | N/A | CTR |
| **InApp** | `inapp_seven_day_window_opened_at` / envios (passivo) | `inapp_seven_day_window_clicked_at` / envios | cliques_inapp / aberturas_inapp | **CTOR** |
| **WhatsApp** | delivery rate (sem tracking real) | N/A | N/A | — |
| **SMS** | excluído | excluído | excluído | — |
| **Banner** | excluído | excluído | excluído | — |

**Observações críticas:**
- InApp OR é **passivo** (exibição automática) — não comparável com Email/DM
- Push não tem OR real — a abertura da notificação já é o clique
- Consolidado BU de OR: calcula-se apenas sobre Email + DM
- Consolidado BU de CTR: calcula-se sobre Email + DM + Push + InApp
- Consolidado BU de CTOR: calcula-se sobre Email + DM (InApp separado, Push sem OR)

---

## 4. Classificação de Campanhas de Rádio

```sql
CASE WHEN LOWER(COALESCE(c.nome, a.campaign_name)) LIKE '%radio%' 
          OR LOWER(COALESCE(c.nome, a.campaign_name)) LIKE '%rádio%' 
     THEN 'Rádio' ELSE 'Não-Rádio' END
```

---

## 5. Faixas de Audiência (Normalização de Engajamento)

Para comparar engajamento entre campanhas de tamanhos diferentes, cada campanha é classificada por faixa:

| Faixa | Envios | Código |
|-------|--------|--------|
| Hiper-segmentada | < 500K | `1_hiper_seg` |
| Segmentada | 500K – 1M | `2_segmentada` |
| Média | 1M – 5M | `3_media` |
| Grande | 5M – 10M | `4_grande` |
| Massiva | > 10M | `5_massiva` |

**Regra:** Cada campanha é comparada apenas com campanhas **do mesmo canal e mesma faixa**.
O delta (pp e %) indica quanto a campanha está acima ou abaixo da média ponderada da sua faixa.

**Filtro mínimo de volume:** ≥ 100K envios para entrar no ranking de destaques.

---

## 6. Parametrização Temporal — Janelas de Período

O relatório suporta 5 janelas temporais:

| Parâmetro | Descrição | Filtro de data |
|-----------|-----------|----------------|
| `mes_fechado` | Mês inteiro (D1 a D_último) | `month_partition = M` |
| `MTD7` | Até o dia 7 do mês | `day(created_at) <= 7` dentro do mês |
| `MTD14` | Até o dia 14 do mês | `day(created_at) <= 14` dentro do mês |
| `MTD21` | Até o dia 21 do mês | `day(created_at) <= 21` dentro do mês |
| `MTD28` | Até o dia 28 do mês | `day(created_at) <= 28` dentro do mês |

### Como aplicar o filtro MTD

A tabela `pf_growth_notifications_reporting` tem campo `sent_at` (timestamp do envio).
Para janelas MTD, adicionar ao WHERE:

```sql
-- MTD28 exemplo
AND DAY(a.sent_at) <= 28

-- Para comparação MoM com MTD, o mês anterior TAMBÉM deve ser filtrado pela mesma janela:
-- Se estou gerando MTD14 de Abril, Março também deve ser MTD14 (dias 1-14 de março)
```

### Janelas de comparação

Para cada mês analisado (mês referência e meses de comparação no MoM), aplicar o **mesmo corte temporal**:

| Relatório | Mês Ref | Comparação MoM | Série 3m | Série 6m |
|-----------|---------|----------------|----------|----------|
| Abr/26 MTD14 | Abr D1-D14 | Mar D1-D14 | Jan-Fev-Mar (D1-D14 cada) | Out-Nov-Dez-Jan-Fev-Mar (D1-D14 cada) |
| Mar/26 mês_fechado | Mar inteiro | Fev inteiro | Jan-Fev-Mar inteiros | Out-Nov-Dez-Jan-Fev-Mar inteiros |

### Como solicitar o relatório

```
"Me gere o relatório executivo do realizado, considerando MTD28"
→ Gera o relatório do mês corrente, filtrado até D28 de cada mês

"Me gere o relatório executivo do realizado, considerando mês fechado"
→ Gera o relatório do último mês completo

"Me gere o relatório executivo do realizado de abril, considerando MTD14"
→ Gera o relatório de abril, filtrado até D14 de cada mês
```

---

## 7. Seções — Detalhamento de Queries

### 1.1 Big Numbers

5 cards: Envios Sucesso, Usuários Únicos, Campanhas Distintas, Frequência/Usuário, Taxa de Entrega.
Cada card com MoM vs mês anterior.

```sql
-- Envios sucesso
SELECT COUNT(*) FROM pf_growth_notifications_reporting
WHERE is_delivered = true AND year_partition = {ANO} AND month_partition = {MES}
  {AND DAY(sent_at) <= {MTD_DIA}}  -- se MTD

-- Usuários únicos
SELECT COUNT(DISTINCT consumer_id) ...

-- Campanhas distintas
SELECT COUNT(DISTINCT COALESCE(c.nome, a.campaign_name)) ...

-- Frequência/usuário = envios / usuários únicos

-- Taxa de entrega = envios entregues / envios totais (inclui is_delivered=false)
```

### 1.2 Ranking de Campanhas

Duas tabelas: Rádio (5 campanhas) e Top 10 Não-Rádio.
Classificação rádio via campo `nome` (LIKE '%radio%' ou '%rádio%').

### 1.3 Canais — 6 meses

Stacked bar Chart.js com InApp, Push, Email, DM, WhatsApp.
Query: GROUP BY channel, month_partition para os últimos 6 meses.

### 1.4 Taxa de Entrega

Diagnóstico comparando taxa com/sem rádio e com/sem InApp.
InApp tem taxa ~82% (menor que outros canais ~98%).

### 1.5 Réguas vs Ações Pontuais

Classificação por `notification_strategy`:
- Régua = `notification_strategy = 'regua'`
- Ação Pontual = demais

### 1.6 MAU vs Não-MAU

JOIN com `daily_app_accesses` para separar quem é MAU App no mês.

### 1.7 Verticais — 4 meses

Stacked bar por `adjusted_bu_requester` (Banking, Payments, Segmentos, Cross).
Dois gráficos: com e sem rádio.

### 1.8 Vertical x Produto Macro

Tabelas por `product_category` agrupadas por vertical, 3 meses.
Versão com rádio e sem rádio.

### 1.9 Mix por Usuário MAU

**Filtro: INNER JOIN com daily_app_accesses (apenas MAU App).**

- Donut: combinações de verticais por usuário
- Top 10: combinações de `product_category` por usuário (COLLECT_SET + ARRAY_JOIN)
- Comparação mês anterior vs mês atual

### 2.1 Denominadores

Envios, Aberturas e Cliques por canal (3 cards separados).

### 2.2 KPIs Consolidados BU

OR, CTR, CTOR por canal — 3 meses com MoM.

### 2.2b KPIs por Vertical

Mesmo que 2.2, mas com breakdown Payments / Banking / Segmentos.

### 2.3 Destaques Normalizados

1. Tabela de benchmarks por faixa × canal
2. Top Performers (delta positivo vs média da faixa)
3. Bottom Performers (delta negativo)
4. Diagnóstico consolidado

---

## 8. Design e Visualização

### Paleta
- Verde: `#16A34A` (destaque positivo, Banking)
- Azul: `#3B82F6` (Payments, links)
- Cinza: `#94A3B8` / `#CBD5E1` (contexto, referência)
- Amarelo: `#D97706` (rádio, alerta)
- Vermelho: `#DC2626` (negativo, bottom)

### Princípios (Storytelling with Data)
- Eliminar clutter (sem bordas pesadas, sem grid)
- Cor com propósito (cinza = contexto, cor = insight)
- Títulos narrativos (contam a história, não descrevem o gráfico)
- Hierarquia visual (big number → tabela → footnote)

### Tecnologias
- Chart.js 4.4.7 + chartjs-plugin-datalabels 2.2.0 (CDN)
- CSS custom properties para temas
- Light mode only (fundo branco)

---

## 9. Regras Especiais

| Regra | Detalhe |
|-------|---------|
| Campanha 9760674755 | PicPay Mais Benefícios Segmentados — classificada como Banking (Segmentos no adjusted_bu, mas é Banking pelo produto) |
| Briefing 11583267449 | Cofrinhos Banking — sem nome no book, identificado manualmente |
| InApp OR | Passivo — não entra no consolidado BU de OR |
| Push OR | Não existe — abertura = clique |
| SMS/Banner | Excluídos de tudo |
| WhatsApp | Só volumetria |
| `adjusted_bu_requester` | Prefixo `SFPF ` deve ser removido via REPLACE |
| Partições | Sempre CAST para INT antes de filtrar |

---

## 10. Localização dos Arquivos

```
jaiminho/
├── docs/
│   └── RACIONAL.md              ← este arquivo
├── results/
│   └── growth-crm/
│       ├── relatorio_fechamento_marco2026_light.html   ← relatório principal
│       └── relatorio_fechamento_marco2026.html         ← versão dark (desatualizada)
```

---

## 11. Changelog

| Data | Versão | Mudança |
|------|--------|---------|
| Mar/2026 | v1.0 | Primeira versão — sessão 1 (volumetria) completa |
| Abr/2026 | v2.0 | Sessão 2 (engajamento) adicionada com 4 subseções |
| Abr/2026 | v2.1 | Seção 2.3 reescrita com normalização por faixa de audiência |
| Abr/2026 | v2.2 | Seção 2.2b adicionada (KPIs por vertical) |
| Abr/2026 | v2.3 | Seção 1.9 filtrada por MAU App (INNER JOIN daily_app_accesses) |
| Abr/2026 | v2.4 | PicPay Mais reincluída no ranking de volumetria (seção 1.2) |
| Abr/2026 | v2.5 | Parametrização temporal documentada (mês_fechado, MTD7/14/21/28) |
