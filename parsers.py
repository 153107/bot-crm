"""
Growth Ops Copilot — Parsers
Funções de parsing para nomes de campanha do Monday.com.

Padrões reais encontrados (326 itens, Mar/2026):

COM briefing_id (238 itens):
  [Area] NNNN - Nome              → mais comum (~160)
  NNNN - Nome                     → sem prefixo (~40)
  [Produto] NNNN - Nome           → ex: [Rendimento], [Wallet], [Cofrinho]
  [Area] - NNNN - Nome            → dash extra antes do briefing
  [Area]  NNNN - Nome             → espaço duplo
  NNNN- Nome                      → sem espaço após dash
  [Area] NNNN Nome                → sem dash (raro, ~3)
  CANCELADA NNNN - Nome           → prefixo de cancelamento
  Ajuste - NNNN - Nome            → prefixo de ajuste
  Ajustes Rouba monte NNNN        → briefing no final (edge case)

SEM briefing_id (88 itens):
  [Area] Nome                     → mais comum
  Nome puro                       → sem nenhum prefixo
  [Produto] Nome                  → ex: [Cofrinho], [Open Finance]

Prefixos [xxx] encontrados:
  Áreas: [Banking], [Segmentos], [Payments], [payments], [Cross], [CROSS]
  Produtos: [Cofrinho], [Rendimento], [Wallet], [Open Finance], [Open Finance Pagamentos],
            [Regulatório], [Lançamento], [IPVA 2026], [Chave Pix milhonária]
"""
import re


def parse_campaign_name(raw_name: str, briefing_id: str | None = None) -> str:
    """
    Extrai o nome limpo de uma campanha do Monday.

    Strips:
    1. Prefixo [qualquer coisa] (área, produto, etc)
    2. Prefixo "CANCELADA" / "Ajuste -" / "Ajustes"
    3. briefing_id + separador (- ou espaço)
    4. Espaços extras

    Args:
        raw_name: Nome bruto do Monday (campo `name`)
        briefing_id: Se fornecido, remove especificamente este ID.
                     Se None, tenta detectar qualquer sequência de 8-15 dígitos.

    Returns:
        Nome limpo da campanha.

    Examples:
        >>> parse_campaign_name("[Segmentos] 11133347224 - PicPay Mais | Carrinho abandonado")
        'PicPay Mais | Carrinho abandonado'

        >>> parse_campaign_name("11491264889 - Alto Propenso - 12X/12%")
        'Alto Propenso - 12X/12%'

        >>> parse_campaign_name("[Banking] Portabilidade | Régua Cross Opf")
        'Portabilidade | Régua Cross Opf'

        >>> parse_campaign_name("[Rendimento] 11503628679 - Rádio - Rendimento de Conta")
        'Rádio - Rendimento de Conta'

        >>> parse_campaign_name("[Cofrinho] Notificação Cofrinhos 3 meses")
        'Notificação Cofrinhos 3 meses'

        >>> parse_campaign_name("[Cross] CANCELADA 10580285147 -  News Novembro/25")
        'News Novembro/25'

        >>> parse_campaign_name("Ajuste - 18080228374 - Sem Parar - Onda 4 - Só Teste B")
        'Sem Parar - Onda 4 - Só Teste B'

        >>> parse_campaign_name("[Banking] - 18276403332 - OPF Enablers | Chave Pix do milhão")
        'OPF Enablers | Chave Pix do milhão'

        >>> parse_campaign_name("[Banking] 18098370999 Cofrinho Turbinado | NÃO MAU 90 Fase 2")
        'Cofrinho Turbinado | NÃO MAU 90 Fase 2'

        >>> parse_campaign_name("Ajustes Rouba monte 9523612013")
        'Ajustes Rouba monte'

        >>> parse_campaign_name("[Segmentos] 10707153955 - RELIGAR RÉGUA E REMOVER WHATSAPP")
        'RELIGAR RÉGUA E REMOVER WHATSAPP'

        >>> parse_campaign_name("11247599996 - [payments] Aviso Feriado carnaval")
        'Aviso Feriado carnaval'

        >>> parse_campaign_name("[payments] 11229999938  -  Ativacao/ reativacao - CB progressivo")
        'Ativacao/ reativacao - CB progressivo'
    """
    if not raw_name:
        return ""

    name = raw_name.strip()

    # ── Step 1: Strip [xxx] prefix from the beginning ──
    # Handles: [Area], [Produto], [Area/Produto com espaço]
    name = re.sub(r"^\[[^\]]*\]\s*", "", name)

    # ── Step 1b: Strip leading dash/separator that might remain after [xxx] ──
    # Handles: "[Banking] - 18276403332 - Nome" → "- 18276403332 - Nome" → "18276403332 - Nome"
    name = re.sub(r"^-\s*", "", name)

    # ── Step 2: Strip status prefixes ──
    # CANCELADA (before briefing). "Ajuste -" only when followed by digits (briefing).
    # "Ajustes" alone is NOT stripped — it can be part of the campaign name.
    name = re.sub(r"^CANCELADA\s+", "", name, flags=re.IGNORECASE)
    name = re.sub(r"^Ajuste\s*-\s*(?=\d)", "", name, flags=re.IGNORECASE)

    # ── Step 3: Strip briefing_id + separator ──
    if briefing_id:
        bid_str = str(briefing_id).strip()
        pattern = re.escape(bid_str)
        # Remove the specific briefing_id followed by optional separator
        # Handles: "NNNN - ", "NNNN- ", "NNNN -", "NNNN "
        name = re.sub(rf"^{pattern}\s*-?\s*", "", name)
        # Also handle briefing at the END (rare: "Ajustes Rouba monte 9523612013")
        name = re.sub(rf"\s*-?\s*{pattern}\s*$", "", name)
        # Also handle a DIFFERENT briefing_id in the name (name has ID X, Monday column has ID Y)
        # This happens when items are copied/reused. Strip any leading digits that look like a briefing.
        name = re.sub(r"^\d{8,15}\s*-?\s*", "", name)
    else:
        # No specific briefing_id provided — detect any 8-15 digit sequence at the start
        name = re.sub(r"^\d{8,15}\s*-?\s*", "", name)
        # Also handle briefing at the end (rare edge case)
        name = re.sub(r"\s*-?\s*\d{8,15}\s*$", "", name)

    # ── Step 4: Strip [xxx] that might appear AFTER briefing_id ──
    # Example: "11247599996 - [payments] Aviso Feriado" → after step 3 becomes "[payments] Aviso Feriado"
    name = re.sub(r"^\[[^\]]*\]\s*", "", name)

    # ── Step 5: Strip leading separator artifacts ──
    # After removing briefing, might have leading "- " or " - "
    name = re.sub(r"^[\s\-]+", "", name)

    # ── Step 6: Clean up whitespace ──
    name = re.sub(r"\s{2,}", " ", name).strip()

    # ── Fallback: if we stripped everything, return the original ──
    if not name:
        return raw_name.strip()

    return name


def extract_campaign_prefix(raw_name: str) -> str | None:
    """
    Extrai o prefixo [xxx] do nome da campanha.
    Retorna o conteúdo dentro dos colchetes (sem os colchetes).

    Useful para identificar área ou produto pelo nome.

    Examples:
        >>> extract_campaign_prefix("[Segmentos] 11133347224 - PicPay Mais")
        'Segmentos'

        >>> extract_campaign_prefix("[Cofrinho] Notificação Cofrinhos 3 meses")
        'Cofrinho'

        >>> extract_campaign_prefix("11491264889 - Alto Propenso")
        None
    """
    match = re.match(r"^\[([^\]]+)\]", (raw_name or "").strip())
    return match.group(1).strip() if match else None


def is_test_campaign(raw_name: str) -> bool:
    """
    Detecta se o nome indica uma campanha de teste (não real).

    Examples:
        >>> is_test_campaign("TESTE")
        True
        >>> is_test_campaign("TESTE JACK AUTOMAÇÃO")
        True
        >>> is_test_campaign("[Segmentos] Teste PicPay+ Alto Valor")
        True
        >>> is_test_campaign("[Banking] 11063647332 - Cofrinho - Metas 2026")
        False
        >>> is_test_campaign("teste 2")
        True
    """
    name = (raw_name or "").strip().upper()
    # Pure test entries
    if re.match(r"^TESTE\b", name):
        return True
    # Short test names (< 30 chars and contains "teste")
    if len(name) < 30 and "TESTE" in name and not re.search(r"\d{8,}", name):
        return True
    # Known test patterns
    test_patterns = [
        r"^TESTE\s",
        r"^TESTE$",
        r"^TESTE\s+DE\s+COLUNA",
        r"^TESTE\s+CRM\b",
        r"^TESTE\s+JACK\b",
        r"^TESTE\s+\w+\s+\w+$",  # "teste felipe Silveira", "teste 2"
    ]
    for p in test_patterns:
        if re.search(p, name):
            return True
    return False


# ═══════════════════════════════════════════════════════════
# Known prefix → area mapping (for prefixes that aren't area names)
# ═══════════════════════════════════════════════════════════
_PREFIX_TO_PRODUCT = {
    "cofrinho": "Cofrinhos",
    "rendimento": "Rendimento",
    "wallet": "Wallet",
    "open finance": "Open Finance",
    "open finance pagamentos": "Open Finance Pagamentos",
    "regulatório": "Regulatório",
    "lançamento": "Lançamento",
    "ipva 2026": "IPVA 2026",
    "chave pix milhonária": "Chave Pix Milhonária",
}


def extract_product_from_prefix(raw_name: str) -> str | None:
    """
    Se o prefixo [xxx] é um produto (não uma área), retorna o nome do produto.

    Examples:
        >>> extract_product_from_prefix("[Cofrinho] 11415988520 - Rádio - Cofrinhos")
        'Cofrinhos'

        >>> extract_product_from_prefix("[Banking] 11063647332 - Cofrinho")
        None
    """
    prefix = extract_campaign_prefix(raw_name)
    if not prefix:
        return None
    return _PREFIX_TO_PRODUCT.get(prefix.lower())
