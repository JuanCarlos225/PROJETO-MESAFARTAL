import re

# =====================================================================
# MESAFARTAI - "O Filtro Anti-Desperdício" (Desafio Regex)
# =====================================================================
# Mensagem de teste que o aluno deve processar:
mensagem = "Atenção: estamos doando 35 kg de leite fresco que vence em 2 dias!"

UNIDADES = r'(?:kg|quilos?|g|caixas?|unidades?|litros?)'

# 1) Quantidade + unidade: um número (com ponto ou vírgula) seguido de unidade
padrao_qtd = r'(\d+(?:[.,]\d+)?)\s*(' + UNIDADES + r')\b'
# 2) Tipo de alimento: a primeira palavra depois de "<unidade> de"
padrao_alimento = r'\b' + UNIDADES + r'\s+de\s+(\w+)'
# 3) Validade: em dias (perecível) ou em meses (não perecível)
padrao_dias = r'(\d+)\s*dias?\b'
padrao_meses = r'(\d+)\s*(?:meses|m[eê]s)\b'


def analisar(texto):
    qtd = re.search(padrao_qtd, texto, re.IGNORECASE)
    alimento = re.search(padrao_alimento, texto, re.IGNORECASE)
    dias = re.search(padrao_dias, texto, re.IGNORECASE)
    meses = re.search(padrao_meses, texto, re.IGNORECASE)

    quantidade = float(qtd.group(1).replace(",", ".")) if qtd else None
    unidade = qtd.group(2).lower() if qtd else ""
    nome = alimento.group(1).capitalize() if alimento else "Não identificado"
    quantidade_txt = f"{quantidade} {unidade}" if qtd else "Não identificada"

    if dias:  # perecível: a validade é medida em dias
        n = int(dias.group(1))
        urgencia = "ALTA" if n <= 3 else "MÉDIA" if n <= 7 else "BAIXA"
        detalhe = f"Vence em {n} {'dia' if n == 1 else 'dias'}"
    elif meses:  # não perecível: a validade é medida em meses
        n = int(meses.group(1))
        urgencia = "BAIXA"
        detalhe = f"Não perecível - validade em {n} meses"
    else:
        urgencia, detalhe = "NÃO INFORMADA", "Sem validade na mensagem"

    return f"Alimento: {nome} | Quantidade: {quantidade_txt} | Urgência: {urgencia} ({detalhe})"


print(f"Mensagem: {mensagem}")
print(analisar(mensagem))

# Testes extras (opcional): outros casos para mostrar que o filtro funciona
print("\n--- Testes extras ---")
for extra in [
    "Temos 20 kg de arroz com validade de 6 meses para doar",
    "Sobraram 10 caixas de alface que vencem em 1 dia",
    "Quero doar 12,5 kg de feijão, vence em 8 dias",
]:
    print(analisar(extra))
