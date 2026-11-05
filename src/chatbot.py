"""Orquestador del chatbot: NLU -> extracción (Regex) -> matchmaking (KNN) -> base de datos."""
from src import database as db
from src.extraccion import clasificar_validez, extraer_entidades
from src.matchmaking import ongs_mas_cercanas
from src.nlu import clasificar

MSG_FALLBACK = (
    "No estoy seguro de haber entendido 🤔. Puedo ayudarte con:\n\n"
    "- **Donar alimentos** (donadores): _\"Quiero donar 30 kg de tomates que vencen mañana\"_\n"
    "- **Solicitar alimentos** (ONGs): _\"Necesitamos alimentos para el comedor\"_\n"
    "- **Consultar el estado** de una donación: _\"¿Ya fue recogida mi donación?\"_"
)
MSG_FUERA_ALCANCE = "Solo puedo ayudarte con donaciones de alimentos 🍎. " + MSG_FALLBACK.split("\n\n", 1)[1]


def _fmt_kg(kg):
    return f"{kg:g} kg" if kg is not None else "cantidad no indicada"


def _fmt_validez(v):
    return v if v else "sin fecha de validez"


EMOJI_URGENCIA = {"ALTA": "🔴", "MEDIA": "🟠", "BAJA": "🟢", "VENCIDA": "⚫", "SIN FECHA": "⚪"}


def _fmt_urgencia(validez, ahora=None):
    info = clasificar_validez(validez, ahora)
    tipo = "" if info["perecedero"] is None else (" · perecedero" if info["perecedero"] else " · no perecedero")
    return f"{EMOJI_URGENCIA[info['urgencia']]} urgencia {info['urgencia']}{tipo}"


def _registrar_donacion(usuario, datos, ruta_imagen=None, ahora=None):
    ong_cercanas = ongs_mas_cercanas(usuario["latitud"], usuario["longitud"], db.listar_usuarios("ONG"))
    donacion_id = db.crear_donacion(usuario["id"], datos["alimento"], datos["cantidad_kg"], datos["validez"], ruta_imagen)
    if not ong_cercanas:
        return (f"✅ Donación #{donacion_id} registrada ({_fmt_kg(datos['cantidad_kg'])} de {datos['alimento']}), "
                "pero todavía no hay ONGs registradas para asignarla.")
    mejor = ong_cercanas[0]
    ong = mejor["ong"]
    db.crear_asignacion(donacion_id, ong["id"], mejor["distancia_km"])
    respuesta = (
        f"✅ Donación **#{donacion_id}** registrada: **{_fmt_kg(datos['cantidad_kg'])} de {datos['alimento']}** "
        f"(validez: {_fmt_validez(datos['validez_texto'])}).\n\n"
        f"⏱️ {_fmt_urgencia(datos['validez'], ahora)}\n\n"
        f"📍 ONG más cercana: **{ong['nombre']}** a **{mejor['distancia_km']} km** · 📞 {ong['telefono']}"
    )
    if len(ong_cercanas) > 1:
        alternas = ", ".join(f"{o['ong']['nombre']} ({o['distancia_km']} km)" for o in ong_cercanas[1:])
        respuesta += f"\n\nOtras opciones cercanas: {alternas}."
    return respuesta


def _pedir_faltantes(datos):
    if not datos.get("alimento") and not datos.get("cantidad_kg"):
        return "¿Qué alimento quieres donar y en qué cantidad? (ej.: _30 kg de tomates_)"
    if not datos.get("alimento"):
        return "¿Qué alimento quieres donar? (ej.: _tomates_)"
    return f"¿Qué cantidad de **{datos['alimento']}** vas a donar? (ej.: _30 kg_, _5 cajas_)"


def _completar(pendiente, texto, ahora=None):
    """Mezcla en `pendiente` las entidades nuevas encontradas en `texto` (slot filling)."""
    nuevas = extraer_entidades(texto, ahora)
    for campo, valor in nuevas.items():
        if pendiente.get(campo) is None:
            pendiente[campo] = valor
    # Si solo falta el alimento y el usuario escribió una palabra suelta, se toma como descripción
    if pendiente.get("alimento") is None and nuevas["cantidad_kg"] is None and nuevas["validez"] is None \
            and 0 < len(texto.split()) <= 4:
        pendiente["alimento"] = texto.strip()
    return pendiente


def _registrar(usuario, texto, pendiente, ahora=None, ruta_imagen=None):
    datos = _completar(dict(pendiente or {}), texto, ahora)
    if datos.get("alimento") and datos.get("cantidad_kg"):
        return _registrar_donacion(usuario, datos, ruta_imagen, ahora), None
    return _pedir_faltantes(datos), datos


def _solicitar(usuario):
    items = db.donaciones_de_ong(usuario["id"])
    if not items:
        return "Por ahora no hay donaciones asignadas a tu ONG. Te aparecerán aquí en cuanto un donador cercano registre una."
    lineas = [f"- **#{i['id']}** · {_fmt_kg(i['cantidad_kg'])} de {i['descripcion_alimento']} · "
              f"{i['donador']} ({i['distancia_km']} km, 📞 {i['telefono']}) · validez: {_fmt_validez(i['fecha_validez'])} · {_fmt_urgencia(i['fecha_validez'])}"
              + (" · 📷" if i["ruta_imagen"] else "")
              for i in items]
    return f"📦 Donaciones asignadas a **{usuario['nombre']}** (las que vencen antes, primero):\n\n" + "\n".join(lineas)


def _consultar(usuario):
    if usuario["tipo"] == "ONG":
        return _solicitar(usuario)
    items = db.donaciones_de_donador(usuario["id"])
    if not items:
        return "Aún no tienes donaciones registradas. Escríbeme algo como _\"Quiero donar 20 kg de pan\"_."
    lineas = []
    for i in items:
        destino = f"asignada a **{i['ong']}** ({i['distancia_km']} km)" if i["ong"] else "sin ONG asignada"
        lineas.append(f"- **#{i['id']}** · {_fmt_kg(i['cantidad_kg'])} de {i['descripcion_alimento']} · "
                      f"{i['estado']} · {destino} · {_fmt_urgencia(i['fecha_validez'])}")
    return "📋 Tus últimas donaciones:\n\n" + "\n".join(lineas)


def procesar_mensaje(modelo, usuario, texto, pendiente=None, ahora=None, ruta_imagen=None):
    """
    Procesa un mensaje y devuelve (respuesta, pendiente, intencion, confianza).
    `pendiente` guarda los datos de una donación a medio completar entre mensajes.
    """
    texto = texto.strip()
    if pendiente is not None:
        if texto.lower() in {"cancelar", "cancela", "cancel"}:
            return "Registro cancelado. ¿En qué más te ayudo?", None, "cancelar", 1.0
        respuesta, pendiente = _registrar(usuario, texto, pendiente, ahora, ruta_imagen)
        return respuesta, pendiente, "registrar_donacion", 1.0

    intencion, confianza = clasificar(modelo, texto)

    if intencion == "fallback":
        return MSG_FALLBACK, None, intencion, confianza
    if intencion == "fuera_de_alcance":
        return MSG_FUERA_ALCANCE, None, intencion, confianza

    if intencion == "registrar_donacion":
        if usuario["tipo"] != "DONADOR":
            return "Registrar donaciones es una acción de **donadores**. Cambia tu perfil en la barra lateral.", None, intencion, confianza
        respuesta, pendiente = _registrar(usuario, texto, {}, ahora, ruta_imagen)
        return respuesta, pendiente, intencion, confianza

    if intencion == "solicitar_alimentos":
        if usuario["tipo"] != "ONG":
            return "Solicitar alimentos es una acción de **ONGs**. Cambia tu perfil en la barra lateral.", None, intencion, confianza
        return _solicitar(usuario), None, intencion, confianza

    return _consultar(usuario), None, intencion, confianza
