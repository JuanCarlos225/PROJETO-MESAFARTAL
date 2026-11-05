"""Motor NLU: clasificador de intenciones (TF-IDF + Regresión Logística) con umbral de confianza."""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline

from src.extraccion import normalizar

UMBRAL = 0.60  # por debajo de este valor se responde con el mensaje de fallback

DATOS_ENTRENAMIENTO = {
    "registrar_donacion": [
        "quiero donar 30 kg de tomates que vencen mañana",
        "tengo 20 cajas de lechuga para donar",
        "me sobraron 15 kg de pan de hoy",
        "voy a donar 50 unidades de yogurt que vencen hoy a las 18h",
        "quiero registrar una donación de arroz",
        "dono 10 kg de frijol",
        "tenemos 40 kg de verduras que se van a echar a perder",
        "hay 12 cajas de fruta para regalar a una ONG",
        "sobraron 25 porciones de comida del restaurante, las quiero donar",
        "registrar donación 5 kg de queso vence mañana",
        "me quedaron 8 kg de plátano maduro para donar",
        "deseo donar leche que vence en 2 días",
        "tengo excedente de carne 20 kg vence hoy",
        "donación de 100 panes para hoy",
        "quiero ofrecer 60 kg de papa",
        "nos sobra pan y queremos donarlo",
        "voy a regalar 15 kg de manzanas",
        "quiero doar 30 kg de tomate que vence amanhã",
        "tenho 20 caixas de alface para doação",
        "sobrou 15 kg de pão hoje, quero doar",
        "quero cadastrar uma doação de arroz",
        "donar 10 litros de leche",
        "tengo comida para donar",
        "quiero hacer una donación de alimentos",
        "mi supermercado quiere donar fruta que vence pronto",
        "tomates 20kg vencen hoy 18h",
        "20 kg de arroz vencen mañana",
        "me sobró pan",
        "sobró comida del día",
        "pan 10 kg hoy",
        "30 kg de papa vencen en 3 días",
    ],
    "solicitar_alimentos": [
        "necesitamos alimentos para el comedor",
        "queremos solicitar comida",
        "somos una ONG y necesitamos verduras",
        "hay donaciones disponibles cerca de nosotros",
        "qué alimentos hay disponibles",
        "necesito arroz y frijol para 80 personas",
        "solicito alimentos para el albergue",
        "tienen donaciones para nosotros",
        "mostrar donaciones disponibles",
        "buscamos alimentos para familias",
        "nos hace falta comida en el comedor",
        "quiero recibir alimentos",
        "hay algo para recoger hoy",
        "ver donaciones asignadas a mi ONG",
        "necesitamos frutas y verduras urgente",
        "precisamos de alimentos para o abrigo",
        "tem doações disponíveis",
        "quais alimentos estão disponíveis",
        "queremos receber comida",
        "preciso de comida para a cozinha comunitária",
        "necesitamos pan para el desayuno del albergue",
        "qué donaciones puedo recoger",
        "pedir comida para la cocina comunitaria",
    ],
    "consultar_estado": [
        "cuál es el estado de mi donación",
        "ya fue recogida mi donación",
        "consultar estado",
        "en qué va mi donación",
        "quién va a recoger mi donación",
        "ver mis donaciones",
        "estatus de mis donaciones",
        "ya asignaron mi donación a una ONG",
        "mi donación ya tiene destino",
        "historial de recolecciones",
        "cómo va el pedido",
        "ya llegaron a recoger",
        "quiero saber el estado de la recolección",
        "status da minha doação",
        "minha doação já foi coletada",
        "consultar status",
        "para onde foi minha doação",
        "cuándo recogen lo que doné",
        "estado de mis entregas",
        "mi último registro en qué estado está",
        "seguimiento de mi donación",
    ],
    "fuera_de_alcance": [
        "hola", "buenos días", "buenas tardes", "gracias", "muchas gracias", "adiós", "qué tal", "ok",
        "cuál es la capital de Francia", "cuéntame un chiste", "qué hora es", "quién ganó el partido de ayer",
        "cómo está el clima hoy", "recomiéndame una película", "quiero pedir una pizza", "cuánto es 2 más 2",
        "ayúdame con mi tarea de matemáticas", "cómo se hace un pastel", "quién eres", "no sé", "asdfgh",
        "quiero comprar un celular", "ayúdame a escribir un correo", "cuál es el mejor equipo de fútbol",
        "olá", "tudo bem", "qual a previsão do tempo", "me conta uma piada", "cuánto cuesta un vuelo a Brasil",
        "traduce esta frase al inglés", "dame una receta de tacos", "qué día es hoy", "háblame de política",
    ],
}


def _crear_modelo():
    vectorizador = FeatureUnion([
        ("palabras", TfidfVectorizer(preprocessor=normalizar, ngram_range=(1, 2))),
        ("caracteres", TfidfVectorizer(preprocessor=normalizar, analyzer="char_wb", ngram_range=(3, 5))),
    ])
    return Pipeline([
        ("tfidf", vectorizador),
        ("clf", LogisticRegression(C=10, max_iter=2000)),
    ])


def entrenar():
    textos, etiquetas = [], []
    for intencion, frases in DATOS_ENTRENAMIENTO.items():
        textos += frases
        etiquetas += [intencion] * len(frases)
    modelo = _crear_modelo()
    modelo.fit(textos, etiquetas)
    return modelo


def clasificar(modelo, texto: str, umbral: float = UMBRAL):
    """Devuelve (intencion, confianza). Si la confianza < umbral, la intención es 'fallback'."""
    probas = modelo.predict_proba([texto])[0]
    i = probas.argmax()
    intencion, confianza = str(modelo.classes_[i]), float(probas[i])
    if confianza < umbral:
        return "fallback", confianza
    return intencion, confianza
