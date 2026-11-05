"""Extracción de entidades con Regex: cantidad, alimento y plazo de validez."""
import re
import unicodedata
from datetime import datetime, timedelta

# Conversión aproximada a kg cuando la unidad no es peso (valores configurables)
CAJA_KG = 10.0
UNIDAD_KG = 0.5
PORCION_KG = 0.4

# Reglas de validez y urgencia (configurables)
DIAS_POR_MES = 30
UMBRAL_NO_PERECEDERO_DIAS = 30   # desde 30 días de validez se considera no perecedero
URGENCIA_ALTA_DIAS = 3           # vence en 3 días o menos -> ALTA
URGENCIA_MEDIA_DIAS = 7          # entre 4 y 7 días -> MEDIA; más de 7 -> BAJA

UNIDADES = {
    "kg": 1.0, "g": 0.001, "caja": CAJA_KG, "unidad": UNIDAD_KG,
    "porcion": PORCION_KG, "litro": 1.0,
}

RE_CANTIDAD = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*"
    r"(kilogramos?|kilos?|quilos?|kgs?|gramos?|gr|g|cajas?|caixas?|unidades?|unidade|uds?|piezas?|"
    r"porciones?|porcoes|litros?|lts?|l)\b"
)

ALIMENTOS = [
    "tomate", "papa", "patata", "batata", "cebolla", "cebola", "zanahoria", "cenoura", "lechuga", "alface",
    "verdura", "legumbre", "fruta", "manzana", "maca", "platano", "banana", "naranja", "laranja", "limon",
    "uva", "mango", "papaya", "melon", "sandia", "pina", "pan", "pao", "arroz", "frijol", "feijao", "lenteja",
    "pasta", "macarron", "harina", "azucar", "aceite", "leche", "queso", "yogur", "huevo", "ovo", "carne",
    "pollo", "frango", "pescado", "peixe", "salchicha", "jamon", "galleta", "cereal", "tortilla", "comida",
    "sopa", "ensalada", "pastel", "bolo", "jugo", "suco", "agua", "chayote", "calabaza", "brocoli", "espinaca",
    "pepino", "pimiento", "aguacate", "elote", "maiz", "tofu", "atun", "sardina", "mantequilla", "refresco",
]

# Palabras donde termina la descripción del alimento
_CORTE = r"(?:\bque\b|\bvence|\bvenc|\bpara\b|\bpor\b|\bhasta\b|\bhoy\b|\bhoje\b|\bmanana\b|\bamanha\b|\bpasado\b|" \
         r"\ba las\b|\ba la\b|\bas\b|\ben\b|\bem\b|\bse\b|\bcon\b|\bya\b|\bporque\b|\by\b|\be\b|\bsin\b|\bde hoy\b|" \
         r"\bcaduc|[,.;:!?()\d])"
RE_ALIMENTO_TRAS_CANTIDAD = re.compile(r"\s*(?:de|do|da|del)\s+(.+)")


def normalizar(texto: str) -> str:
    """Minúsculas y sin acentos (conserva la longitud para poder recortar el texto original)."""
    sin = "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")
    return sin.lower()


def _base_unidad(u: str) -> str:
    if u.startswith(("kg", "kilo", "quilo")):
        return "kg"
    if u.startswith("gr") or u == "g":
        return "g"
    if u.startswith(("caja", "caixa")):
        return "caja"
    if u.startswith(("unidad", "ud", "pieza")):
        return "unidad"
    if u.startswith("porc"):
        return "porcion"
    return "litro"


def extraer_cantidad(texto: str):
    """Devuelve (cantidad, unidad, cantidad_en_kg, fin_del_match) o None."""
    n = normalizar(texto)
    m = RE_CANTIDAD.search(n)
    if not m:
        return None
    cantidad = float(m.group(1).replace(",", "."))
    unidad = _base_unidad(m.group(2))
    return cantidad, unidad, round(cantidad * UNIDADES[unidad], 3), m.end()


def extraer_alimento(texto: str, fin_cantidad: int = None):
    n = normalizar(texto)
    mismo_largo = len(n) == len(texto)
    fuente = texto if mismo_largo else n

    # 1) Texto que sigue a "<cantidad> <unidad> de ..."
    if fin_cantidad is not None:
        m = RE_ALIMENTO_TRAS_CANTIDAD.match(n[fin_cantidad:])
        if m:
            ini = fin_cantidad + m.start(1)
            frag = n[ini:]
            corte = re.search(_CORTE, frag)
            fin = ini + (corte.start() if corte else len(frag))
            candidato = fuente[ini:fin].strip()
            if len(candidato) >= 3:
                return candidato

    # 2) Primer alimento conocido del vocabulario
    for palabra in ALIMENTOS:
        m = re.search(r"\b" + palabra + r"\w*", n)
        if m:
            return fuente[m.start():m.end()]
    return None


def extraer_validez(texto: str, ahora: datetime = None):
    """Devuelve (fecha_iso, texto_legible) o (None, None).
    Entiende: hoy, mañana, pasado mañana, 18h, dd/mm, "en N días" y "N meses"."""
    ahora = ahora or datetime.now()
    n = normalizar(texto)
    fecha = None

    m_mes = re.search(r"\b(\d{1,2})\s*(?:meses|mes)\b", n)
    m_dia = re.search(r"\b(\d{1,3})\s*dias?\b", n)

    if re.search(r"\bpasado manana\b", n):
        fecha = ahora + timedelta(days=2)
    elif re.search(r"\b(manana|amanha)\b", n):
        fecha = ahora + timedelta(days=1)
    elif re.search(r"\b(hoy|hoje)\b", n):
        fecha = ahora
    elif m_mes:
        fecha = ahora + timedelta(days=DIAS_POR_MES * int(m_mes.group(1)))
    elif m_dia:
        fecha = ahora + timedelta(days=int(m_dia.group(1)))
    else:
        m = re.search(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b", n)
        if m:
            dia, mes = int(m.group(1)), int(m.group(2))
            anio = int(m.group(3)) if m.group(3) else ahora.year
            anio += 2000 if anio < 100 else 0
            try:
                fecha = datetime(anio, mes, dia)
            except ValueError:
                fecha = None

    hora = None
    m = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(?:h|hs|hrs|horas)\b", n) or \
        re.search(r"\ba las?\s+(\d{1,2})(?::(\d{2}))?\b", n) or \
        re.search(r"\b(\d{1,2}):(\d{2})\b", n)
    if m and 0 <= int(m.group(1)) <= 23:
        hora = (int(m.group(1)), int(m.group(2) or 0))

    if fecha is None and hora is None:
        return None, None
    if fecha is None:
        fecha = ahora
    if hora:
        return fecha.strftime("%Y-%m-%d") + f" {hora[0]:02d}:{hora[1]:02d}", \
            fecha.strftime("%d/%m") + f" {hora[0]:02d}:{hora[1]:02d}"
    return fecha.strftime("%Y-%m-%d"), fecha.strftime("%d/%m/%Y")


def clasificar_validez(validez: str, ahora: datetime = None) -> dict:
    """
    A partir de la fecha de validez guardada calcula:
      - dias: días que faltan para vencer
      - perecedero: True si vence en menos de UMBRAL_NO_PERECEDERO_DIAS días (validez en días);
                    False si la validez es de meses (no perecedero)
      - urgencia: ALTA / MEDIA / BAJA / VENCIDA / SIN FECHA
    """
    if not validez:
        return {"dias": None, "perecedero": None, "urgencia": "SIN FECHA"}
    ahora = ahora or datetime.now()
    dias = (datetime.strptime(validez[:10], "%Y-%m-%d").date() - ahora.date()).days
    if dias < 0:
        urgencia = "VENCIDA"
    elif dias <= URGENCIA_ALTA_DIAS:
        urgencia = "ALTA"
    elif dias <= URGENCIA_MEDIA_DIAS:
        urgencia = "MEDIA"
    else:
        urgencia = "BAJA"
    return {"dias": dias, "perecedero": dias < UMBRAL_NO_PERECEDERO_DIAS, "urgencia": urgencia}


def extraer_entidades(texto: str, ahora: datetime = None) -> dict:
    cant = extraer_cantidad(texto)
    fin = cant[3] if cant else None
    validez_iso, validez_txt = extraer_validez(texto, ahora)
    return {
        "alimento": extraer_alimento(texto, fin),
        "cantidad": cant[0] if cant else None,
        "unidad": cant[1] if cant else None,
        "cantidad_kg": cant[2] if cant else None,
        "validez": validez_iso,
        "validez_texto": validez_txt,
        "perecedero": clasificar_validez(validez_iso, ahora)["perecedero"],
        "urgencia": clasificar_validez(validez_iso, ahora)["urgencia"],
    }
