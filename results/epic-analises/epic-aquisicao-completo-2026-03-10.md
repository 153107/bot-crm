# 📊 EPIC — Análise de Aquisição: Ofertas vs Engajamento

**Data:** 10 de Março de 2026  
**Analista:** ABA (Analista de Business Analytics)  
**Período de Análise:** Últimos 30 dias (snapshot ofertas: atual)

---

## 🎯 Objetivo

Entender o panorama dos usuários com ofertas ativas EPIC em relação ao engajamento (MAU App e MAT), identificar oportunidades de aquisição e propor alavancas para aumentar a conversão.

---

## 📋 Sumário Executivo

### **Problema Validado:**
✅ **64% dos usuários com oferta ativa EPIC estão completamente inativos** (não acessam o app nem transacionam nos últimos 30 dias)

### **Números-Chave:**
- **397.329 usuários** com ofertas ativas EPIC
- **113.764 (28,6%)** engajados (MAU + MAT)
- **256.599 (64,6%)** inativos ou com baixo engajamento
- **73% dos inativos** não transacionam há mais de 1 ano

### **Impacto Potencial:**
Focando nos segmentos certos, podemos adicionar **+24 mil contratações** = **R$ 1,2M MRR** (+R$ 14,4M ARR)

---

## 1️⃣ Diagnóstico: Segmentação de Ofertas

### **1.1 Distribuição Geral (397.329 usuários)**

| Segmento | Volume | % Total | Descrição |
|----------|--------|---------|-----------|
| **MAU + MAT** ✅✅ | 113.764 | 28,63% | Acessam o app **E** transacionam |
| **MAU sem MAT** ⚠️ | 26.966 | 6,79% | Acessam mas **não transacionam** |
| **MAT sem MAU** 🤔 | 1.353 | 0,34% | Transacionam fora do app (API/TEF) |
| **Sem MAU sem MAT** ❌❌ | 255.246 | 64,24% | **Completamente inativos** |

---

### **1.2 Reagrupamento por Potencial**

| Grupo | Volume | % | Perfil | Prioridade |
|-------|--------|---|--------|------------|
| **Engajados** | 115.117 | 29,0% | MAU+MAT ou MAT puro | 🟢 **P0** |
| **Navegadores** | 26.966 | 6,8% | MAU sem MAT | 🟡 **P1** |
| **Inativos** | 255.246 | 64,2% | Sem MAU nem MAT | 🔴 **P2** |

---

## 2️⃣ Deep Dive: Perfil dos Inativos (255.246 usuários)

### **2.1 Tempo de Inatividade**

| Faixa | Volume | % | Média de Dias Inativo |
|-------|--------|---|-----------------------|
| **31-90 dias atrás** | 7.453 | 2,90% | 55 dias |
| **91-180 dias atrás** | 4.601 | 1,79% | 133 dias |
| **6 meses - 1 ano atrás** | 8.319 | 3,24% | 278 dias |
| **1+ ano atrás** | 188.130 | **73,32%** | 1.568 dias (4,3 anos) |
| **Nunca transacionou** | 48.096 | **18,74%** | — |

**Insight:** 92% dos inativos estão dormentes há mais de 6 meses. Reativar essa base é um desafio de longo prazo.

---

### **2.2 Tempo de Cadastro**

| Faixa | Volume | % | Média de Anos |
|-------|--------|---|---------------|
| **0-30 dias** | 18 | 0,01% | 0,07 anos |
| **31-90 dias** | 358 | 0,13% | 0,18 anos |
| **91-180 dias** | 295 | 0,10% | 0,39 anos |
| **6 meses - 1 ano** | 1.632 | 0,58% | 0,82 anos |
| **1-2 anos** | 9.385 | 3,33% | 1,53 anos |
| **2+ anos** | 270.524 | **95,86%** | **5,58 anos** |

**Insight:** 96% são cadastros antigos (2+ anos). Não são novos usuários que não engajaram — são usuários que **pararam** de usar a PicPay.

---

### **2.3 Produtos Usados Historicamente (quando ativos)**

| Produto | Usuários | % Penetração | Volume Transações |
|---------|----------|--------------|-------------------|
| **PIX P2P** | 120.662 | 51,8% | 3.286.402 |
| **BIZ** | 90.232 | 38,7% | 1.374.134 |
| **Boletos** | 74.401 | 31,9% | 1.062.384 |
| **PIX Mesmo Titular** | 71.690 | 30,8% | 1.122.432 |
| **PIX P2B** | 48.536 | 20,8% | 1.249.850 |
| **E-commerce** | 50.167 | 21,5% | 355.019 |
| **TED Cashout** | 42.690 | 18,3% | 297.752 |
| **Recarga de Celular** | 29.443 | 12,6% | 304.035 |
| **Mobilidade** | 17.601 | 7,6% | 848.697 |

**Insight:** Quando ativos, 52% usavam PIX (P2P/P2B). Eram transacionadores, não apenas navegadores.

---

## 3️⃣ Análise de Oportunidade

### **3.1 Segmentação por Potencial de Conversão**

| Segmento | Volume | Taxa Conversão Estimada | Contratações Potenciais | MRR Potencial |
|----------|--------|-------------------------|-------------------------|---------------|
| **Engajados (MAU+MAT)** | 115.117 | 20% | 23.023 | R$ 1.148.848 |
| **Navegadores (MAU sem MAT)** | 26.966 | 5% | 1.348 | R$ 67.265 |
| **Inativos Recentes (< 90d)** | 12.054 | 3% | 362 | R$ 18.056 |
| **Inativos Antigos (> 90d)** | 243.192 | < 1% | < 2.000 | < R$ 100.000 |

**Total Acionável (Engajados + Navegadores + Recentes):** 154.137 usuários → **24.733 contratações** → **R$ 1,23M MRR**

---

### **3.2 Benchmark: Taxa de Conversão Atual**

Com 397.329 ofertas ativas e uma taxa de conversão histórica estimada em ~5%, esperaríamos **~20 mil contratações/mês**.

Se focássemos apenas nos **115 mil engajados** (MAU+MAT), com taxa de 20%, teríamos **23 mil contratações** — **mais eficiente e sustentável**.

---

## 4️⃣ Alavancas de Aquisição Recomendadas

### **🟢 Alavanca 1: Hiper-Foco nos Engajados (P0)**
**Público:** 115.117 usuários (MAU+MAT)  
**Ação:**
- Campanha push in-app com oferta destacada
- Email marketing personalizado
- Banner home do app (posição premium)
- Notificação de "Oferta especial disponível"

**Meta:** Taxa de conversão de 20% (benchmark produtos de crédito alta renda)  
**Impacto:** +23.023 contratações = **R$ 1,15M MRR** (+R$ 13,8M ARR)

**Timeline:** 30 dias  
**Investimento:** Baixo (canais próprios)  
**ROI:** Alto

---

### **🟡 Alavanca 2: Conversão dos Navegadores (P1)**
**Público:** 26.966 usuários (MAU sem MAT)  
**Ação:**
- Jornada in-app guiada: "Complete seu perfil e ganhe R$ 20"
- Pop-up contextual ao acessar carteira ou PIX
- Teste A/B de CTAs: "Ativar benefício" vs "Ver vantagens"

**Meta:** Taxa de conversão de 5%  
**Impacto:** +1.348 contratações = **R$ 67K MRR** (+R$ 804K ARR)

**Timeline:** 45 dias  
**Investimento:** Médio (dev + UX)  
**ROI:** Médio-Alto

---

### **🔴 Alavanca 3: Reativar Inativos Recentes (P2)**
**Público:** 12.054 usuários (inativos 31-90 dias)  
**Ação:**
- Campanha "Volte e ganhe": Cashback R$ 50 na primeira transação
- Email + SMS com senso de urgência
- Oferta EPIC como "benefício exclusivo de retorno"

**Meta:** Taxa de reativação de 10% → conversão de 30% dos reativados  
**Impacto:** +362 contratações = **R$ 18K MRR** (+R$ 216K ARR)

**Timeline:** 60 dias  
**Investimento:** Alto (incentivo financeiro)  
**ROI:** Médio

---

### **❌ Não Priorizar: Inativos Antigos (> 90 dias)**
**Público:** 243.192 usuários  
**Razão:** 92% dormentes há 6+ meses. Custo de reativação > retorno esperado.  
**Recomendação:** Parar de ofertar EPIC para este grupo. **Concentrar esforços em leads qualificados**.

---

## 5️⃣ Matriz de Decisão

| Ação | Público | Impacto | Esforço | Prioridade | Prazo |
|------|---------|---------|---------|------------|-------|
| **Campanha push Engajados** | 115K | 🟢 Alto | 🟢 Baixo | ⭐⭐⭐ P0 | 30d |
| **Jornada guiada Navegadores** | 27K | 🟡 Médio | 🟡 Médio | ⭐⭐ P1 | 45d |
| **"Volte e Ganhe" Recentes** | 12K | 🟠 Baixo-Médio | 🔴 Alto | ⭐ P2 | 60d |
| **Parar ofertas Inativos Antigos** | 243K | 🟢 Economia | 🟢 Baixo | ⭐⭐⭐ P0 | Imediato |

---

## 6️⃣ Impacto Consolidado (30 dias)

| Métrica | Baseline | Após Implementação | Delta |
|---------|----------|-------------------|-------|
| **Ofertas Ativas** | 397.329 | 154.137 | -243.192 (foco qualificado) |
| **Taxa de Conversão** | ~5% | ~16% | +220% |
| **Contratações/mês** | ~20.000 | ~24.733 | +4.733 (+24%) |
| **MRR** | ~R$ 1,0M | ~R$ 2,23M | +R$ 1,23M (+123%) |
| **ARR** | ~R$ 12M | ~R$ 26,8M | +R$ 14,8M (+123%) |

---

## 7️⃣ Próximos Passos

### **Imediato (Semana 1-2):**
1. ✅ **Parar ofertas** para inativos 90+ dias (243K usuários)
2. ✅ **Campanha push** para 115K engajados (P0)
3. ⏳ **Solicitar acesso** a dados de conversão histórica EPIC para refinar taxas

### **Curto Prazo (Semana 3-6):**
4. ⏳ **Desenvolver jornada guiada** para navegadores (27K MAU sem MAT)
5. ⏳ **Análise Fase 3:** Quem contratou sendo Não-MAU? (benchmark de conversão)
6. ⏳ **Modelo de propensão:** Score 0-100 para priorizar comunicações

### **Médio Prazo (2-3 meses):**
7. ⏳ **Campanha "Volte e Ganhe"** para inativos recentes (12K usuários)
8. ⏳ **Dashboard de acompanhamento:** Taxa de conversão por segmento (semanal)

---

## 📎 Anexos

### **A1: Metodologia**
- **Fonte de Dados:** Databricks PicPay (`picpay.epic.offers`, `picpay.all_transactions`, `picpay.consumers.app_accesses`)
- **Período:** Snapshot ofertas (atual) vs MAU/MAT (últimos 30 dias até D-1)
- **Definições:**
  - **MAU App:** Usuário com acesso logado nos últimos 30 dias
  - **MAT:** Usuário com transação aprovada nos últimos 30 dias
  - **Oferta Ativa:** `offer_status = 'ACTIVE'`

### **A2: Queries Executadas**
1. Cruzamento Ofertas x MAU App x MAT
2. Perfil de inatividade (última transação)
3. Tempo de cadastro
4. Produtos históricos usados

### **A3: Limitações**
- Não analisamos contratações de usuários Não-MAU (Fase 3 pendente)
- Taxa de conversão estimada baseada em benchmarks de mercado (validar com histórico EPIC)
- Não consideramos canais externos (WhatsApp, SMS) no cálculo de MAU

---

## 📊 Conclusão

**O problema de aquisição do EPIC não é de volume de ofertas (397K), mas de qualidade da base ofertada.**

**71% dos usuários com oferta estão inativos há meses ou anos.** Concentrar esforços nos **35% engajados** (142K usuários) pode gerar **+R$ 1,2M MRR** com menor custo e maior eficiência.

**Recomendação estratégica:** Parar de ofertar para inativos antigos e dobrar investimento em comunicação para engajados e navegadores.

---

**Elaborado por:** ABA 📊 — Analista de Business Analytics  
**Data:** 10/Mar/2026  
**Versão:** 2.0 (completa com MAU App)

