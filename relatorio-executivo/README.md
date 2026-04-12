# Relatório Executivo — Growth & CRM 📬

Relatório HTML visual com KPIs de volumetria e engajamento das comunicações da BU de Wallet & Banking.

## Como gerar

No HubAI Nitro, peça ao agente:

```
"Me gere o relatório executivo do realizado, considerando mês fechado"
"Me gere o relatório executivo do realizado, considerando MTD14"
"Me gere o relatório executivo do realizado de abril, considerando MTD28"
```

### Janelas disponíveis

| Janela | Descrição |
|--------|-----------|
| `mês fechado` | Mês inteiro |
| `MTD7` | Até dia 7 |
| `MTD14` | Até dia 14 |
| `MTD21` | Até dia 21 |
| `MTD28` | Até dia 28 |

## Estrutura

```
relatorio-executivo/
├── README.md              ← este arquivo
├── RACIONAL.md            ← racional completo (queries, regras, parametrização)
└── results/
    ├── growth-crm/        ← relatórios de Growth & CRM
    └── epic-analises/     ← análises Epic (Alta Renda)
```

## Documentação

→ [RACIONAL.md](RACIONAL.md) — racional completo de construção, regras de negócio, queries e parametrização temporal.

## Fonte de dados

- `picpay.self_service_analytics.pf_growth_notifications_reporting`
- `picpay.validation.tb_book_growth_nome_campanhas`
- `picpay.consumers.daily_app_accesses`
