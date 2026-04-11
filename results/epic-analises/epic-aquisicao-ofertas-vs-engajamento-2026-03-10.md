# 📊 EPIC — Análise de Aquisição: Ofertas vs Engajamento

**Período:** Snapshot atual (ofertas ativas) + Últimos 30 dias (MAT)  
**Data do relatório:** 10/Mar/2026  
**Analista:** ABA (Analista de Business Analytics)

---

## 🎯 Objetivo da Análise

Entender o panorama dos usuários com ofertas ativas EPIC e identificar alavancas de aquisição para aumentar a taxa de conversão do produto alta renda.

**Hipótese de Negócio:** Grande parte dos usuários com oferta ativa não estão engajados (Não-MAU), criando uma barreira de conversão.

---

## 📈 Resumo Executivo

### **Principais Achados:**

1. **71% dos usuários com oferta ativa EPIC não transacionaram nos últimos 30 dias** (282 mil de 397 mil)
2. **96% dos Não-MAT são cadastros antigos** (2+ anos na base)
3. **69% estão inativos há mais de 1 ano** (195 mil usuários)
4. **17% nunca transacionaram** na plataforma (49 mil usuários)
5. **Quando ativos, 52% usavam PIX** (P2P e P2B) como produto principal

---

## 1️⃣ Diagnóstico: Ofertas vs Engajamento (MAT)

### **📊 Panorama Geral**

| Métrica | Volume | % do Total |
|---------|--------|------------|
| **Total de Usuários com Oferta Ativa** | 397.329 | 100% |
| **Com MAT (transacionando últimos 30d)** | 115.117 | **28,97%** |
| **Sem MAT (não transacionando)** | 282.212 | **71,03%** |

> **💡 Insight Crítico:** A hipótese do time de produto está **validada**. Mais de 2/3 da base de ofertas está inativa, o que explica a dificuldade de aquisição.

---

## 2️⃣ Perfil dos Não-MAT (282 mil usuários)

### **2.1 Tempo de Cadastro na PicPay**

| Faixa de Tempo | Total de Usuários | % do Total | Média de Dias |
|----------------|-------------------|------------|---------------|
| 0-30 dias | 18 | 0,01% | 24 dias |
| 31-90 dias | 358 | 0,13% | 67 dias |
| 91-180 dias | 295 | 0,10% | 144 dias |
| 6m-1 ano | 1.632 | 0,58% | 300 dias |
| 1-2 anos | 9.385 | 3,33% | 559 dias |
| **2+ anos** | **270.524** | **95,86%** | **2.038 dias (~5,6 anos)** |

> **💡 Insight:** O problema **não é aquisição recente**. São usuários antigos da base que perderam engajamento ao longo do tempo.

---

### **2.2 Tempo de Inatividade (Última Transação)**

| Faixa de Inatividade | Total de Usuários | % do Total | Média de Dias Inativo |
|----------------------|-------------------|------------|------------------------|
| 31-90 dias atrás | 17.428 | 6,18% | 55 dias |
| 91-180 dias atrás | 8.797 | 3,12% | 130 dias |
| 6m-1 ano atrás | 11.678 | 4,14% | 273 dias |
| **1+ ano atrás** | **195.077** | **69,12%** | **1.549 dias (~4,2 anos)** |
| **Nunca transacionou** | **49.232** | **17,45%** | — |

> **💡 Insight:** Quase 70% estão **dormentes há mais de 1 ano**. São usuários com baixíssima probabilidade de reativação orgânica.

---

### **2.3 Produtos Mais Usados (Quando Ativos)**

**Top 15 Produtos no Histórico dos Não-MAT:**

| Produto | Usuários Únicos | Total de Transações | % dos Usuários |
|---------|-----------------|---------------------|----------------|
| **PF (PIX P2P)** | 120.662 | 3.286.402 | 51,79% |
| **BIZ** | 90.232 | 1.374.134 | 38,73% |
| **BILLS (Boletos)** | 74.401 | 1.062.384 | 31,93% |
| **P2P_EXTERNAL_SAME_PIX** | 71.690 | 1.122.432 | 30,77% |
| **P2P_EXTERNAL_PIX** | 56.148 | 1.711.873 | 24,10% |
| **PRO** | 54.217 | 580.206 | 23,27% |
| **ECOMMERCE** | 50.167 | 355.019 | 21,53% |
| **P2B_EXTERNAL_PIX** | 48.536 | 1.249.850 | 20,83% |
| **TEF** | 44.313 | 511.067 | 19,02% |
| **TED_CASHOUT** | 42.690 | 297.752 | 18,32% |
| **P2M** | 36.598 | 456.183 | 15,71% |
| **RECARGA_DE_CELULAR** | 29.443 | 304.035 | 12,64% |
| **DIGITALGOODS** | 28.069 | 210.650 | 12,05% |
| **P2P_INTERNAL_PIX** | 22.218 | 129.262 | 9,54% |
| **MOBILITY** | 17.601 | 848.697 | 7,55% |

> **💡 Insight:** Quando ativos, esses usuários eram **heavy users de PIX** (P2P e P2B somados = 52% de penetração). Também tinham comportamento diversificado (Boletos, BIZ, PRO, E-commerce).

---

## 3️⃣ Segmentação dos Não-MAT para Priorização

Com base nos dados, podemos segmentar os 282 mil Não-MAT em **3 grupos estratégicos**:

### **🔴 Grupo 1: Inativos Profundos (69% — 195 mil usuários)**
- **Perfil:** Última transação há mais de 1 ano
- **Característica:** Dormência crítica, baixíssima probabilidade de reativação
- **Recomendação:** **Não priorizar** para aquisição EPIC. Foco em reativação geral da plataforma antes.

### **🟡 Grupo 2: Inativos Recentes (13% — 38 mil usuários)**
- **Perfil:** Última transação entre 31 e 180 dias
- **Característica:** Ainda têm memória da plataforma, janela de oportunidade
- **Recomendação:** **Priorizar** com campanhas de reengajamento antes de ofertar EPIC.

### **⚪ Grupo 3: Nunca Ativos (17% — 49 mil usuários)**
- **Perfil:** Cadastrados mas nunca transacionaram
- **Característica:** Barreira inicial não superada (KYC, primeira transação, confiança)
- **Recomendação:** **Não priorizar** para EPIC. Foco em onboarding básico.

---

## 4️⃣ Alavancas de Aquisição Recomendadas

### **🎯 Alavanca 1: Focar nos 29% Já Engajados (Com MAT)**
**Ação:** Priorizar comunicação para os **115 mil usuários que já transacionam**. Eles já estão ativos, têm oferta, e precisam apenas do "empurrão final" para converter.

**Táticas:**
- Push notification in-app personalizado
- Email marketing com benefícios claros do EPIC
- Banner destacado no app (home, extrato, PIX)
- Campanha de cashback condicional (adere ao EPIC = 2% cashback nos próximos 30 dias)

**Potencial:** Se convertermos 20% desse grupo, teríamos **23 mil novas contratações** (vs taxa atual de conversão muito baixa).

---

### **🎯 Alavanca 2: Reativar os Inativos Recentes (13% — 38 mil)**
**Ação:** Criar jornada de reativação **antes** de ofertar EPIC. Precisam voltar a transacionar para então considerar o produto alta renda.

**Táticas:**
- Campanha de cashback "Volte e Ganhe" (R$ 10 no primeiro PIX)
- SMS/WhatsApp para base que autorizou contato
- Oferta de isenção de tarifas por 30 dias
- Integração com Open Finance (se aplicável) para trazer saldo de volta

**Potencial:** Se reativarmos 30%, teríamos **11 mil usuários voltando ao MAT**, aumentando a base elegível para EPIC.

---

### **🎯 Alavanca 3: Refinar Critério de Ofertas (Scoring Preditivo)**
**Ação:** Criar modelo de propensão para **parar de ofertar EPIC** para quem tem baixíssima chance de converter (Grupo 1 e 3).

**Benefícios:**
- Reduz "poluição" da base de ofertas
- Melhora taxas de conversão reportadas
- Libera esforço de comunicação para público qualificado

**Critérios para Score Baixo (não ofertar):**
- Inativo há mais de 365 dias **OU**
- Nunca transacionou **OU**
- Menos de 5 transações no último ano

**Potencial:** Eliminaria ~244 mil usuários da base de ofertas (~61%), concentrando esforços nos 153 mil com maior potencial.

---

## 5️⃣ Recomendações Priorizadas

### **P0 — Implementar Imediatamente (Próximos 7 dias)**
1. **Campanha focada nos 115 mil Com MAT**
   - Push in-app + Email + Banner home
   - Meta: 20% de conversão = 23 mil contratações
   - KPI: Taxa de abertura (push/email), cliques, contratações

2. **Dashboarding de acompanhamento**
   - Criar painel diário: Ofertas Ativas / Com MAT / Sem MAT / Conversões
   - Alerta se % Sem MAT subir acima de 75%

---

### **P1 — Próximas 2 Semanas**
3. **Jornada de Reativação para Inativos Recentes (38 mil)**
   - Campanha "Volte e Ganhe" com incentivo financeiro
   - Meta: 30% de reativação = 11 mil voltando ao MAT

4. **Modelo de Propensão v1 (Regra Simples)**
   - Criar flag `epic_elegivel` na base de ofertas
   - Critério: `(ultima_tx < 365d) AND (total_txs_vida > 5)`
   - Aplicar filtro nas próximas rodadas de oferta

---

### **P2 — Próximo Ciclo de Planejamento (1-2 meses)**
5. **Modelo de Machine Learning para Propensão**
   - Features: tempo inativo, produtos usados, TPV histórico, geo, idade
   - Target: conversão EPIC (últimos 6 meses)
   - Deploy em produção para scoring em tempo real

6. **Teste A/B: Comunicação Segmentada**
   - Grupo A: Mensagem genérica EPIC
   - Grupo B: Mensagem personalizada por produto histórico (ex: "Você usa muito PIX, o EPIC tem cashback turbinado em PIX")
   - Medir taxa de conversão

---

## 6️⃣ Impacto Estimado

**Cenário Conservador (próximos 30 dias):**
- Alavanca 1 (Com MAT — 20% conversão): **+23 mil contratações**
- Alavanca 2 (Reativação — 30% reativam → 10% convertem): **+1,1 mil contratações**
- **Total:** **+24,1 mil novas contratações EPIC**

**Receita Incremental (MRR):**
- 24.100 contratações × R$ 49,90/mês = **R$ 1.202.590/mês** (+R$ 14,4M/ano)

---

## 7️⃣ Próximos Passos Analíticos

### **Análises Complementares Necessárias:**
1. **Cruzar com MAU App** (aguardando acesso à tabela)
   - Validar se Não-MAU também são Não-MAU App
   - Entender se o problema é ausência de transação OU ausência de acesso ao app

2. **Análise de Contratações Históricas**
   - Pegar quem contratou EPIC nos últimos 6 meses
   - Ver quantos eram Não-MAU no momento da contratação
   - Entender jornada: o que os reativou antes de contratar?

3. **Análise Geográfica e Demográfica**
   - Cruzar Não-MAT com perfil (idade, renda, região)
   - Identificar bolsões de oportunidade (ex: alta renda concentrada em SP/RJ)

---

## 📎 Apêndices

### **A.1 — Queries Executadas**

**Query 1: Cruzamento Ofertas x MAT**
```sql
WITH ofertas_ativas AS (
    SELECT DISTINCT consumer_id
    FROM picpay.epic.offers
    WHERE offer_status = 'ACTIVE'
),
mat_30d AS (
    SELECT DISTINCT consumer_id
    FROM picpay.all_transactions
    WHERE DATE(created_at) >= DATE_SUB(CURRENT_DATE, 30)
      AND DATE(created_at) < CURRENT_DATE
      AND is_approved = TRUE
)
SELECT 
    COUNT(DISTINCT o.consumer_id) AS total_ofertas,
    COUNT(DISTINCT m.consumer_id) AS com_mat,
    COUNT(DISTINCT CASE WHEN m.consumer_id IS NULL THEN o.consumer_id END) AS sem_mat
FROM ofertas_ativas o
LEFT JOIN mat_30d m ON o.consumer_id = m.consumer_id
```

**Query 2: Tempo de Cadastro**
```sql
-- Ver arquivo completo no repositório de análises
```

**Query 3: Tempo de Inatividade**
```sql
-- Ver arquivo completo no repositório de análises
```

**Query 4: Produtos Históricos**
```sql
-- Ver arquivo completo no repositório de análises
```

---

### **A.2 — Fontes de Dados**
- `picpay.epic.offers` — Ofertas EPIC ativas
- `picpay.all_transactions` — Transações consolidadas (MAT)
- `picpay.consumers.consumers` — Cadastro de usuários

---

### **A.3 — Definições**
- **MAT (Monthly Active Transactioners):** Usuários que realizaram ao menos 1 transação aprovada nos últimos 30 dias
- **Não-MAT:** Usuários que não transacionaram nos últimos 30 dias
- **Oferta Ativa:** Status `'ACTIVE'` na tabela `epic.offers`
- **MRR (Monthly Recurring Revenue):** R$ 49,90 por contratação ativa EPIC

---

**Relatório gerado por:** ABA (Analista de Business Analytics) 📊  
**Contato:** heloisa.baccoli@picpay.com  
**Última atualização:** 10/Mar/2026
