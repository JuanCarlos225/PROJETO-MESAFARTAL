"""MESAFARTAI - Interfaz web (Streamlit): chat conversacional + dashboard de impacto social."""
import os
import uuid

import pandas as pd
import streamlit as st

from src import database as db
from src.chatbot import procesar_mensaje
from src.extraccion import clasificar_validez
from src.nlu import entrenar

COMIDAS_POR_KG = 2  # estimación: 1 kg de alimento ≈ 2 comidas
CARPETA_IMAGENES = "fotos"

st.set_page_config(page_title="MESAFARTAI", page_icon="🍽️", layout="wide")
db.inicializar_base()

# Oculta el botón "Deploy" de la barra superior
st.markdown(
    "<style>.stAppDeployButton, [data-testid='stAppDeployButton'] {display: none !important;}</style>",
    unsafe_allow_html=True,
)


@st.cache_resource
def cargar_modelo():
    return entrenar()


def guardar_imagen(archivo):
    """Guarda la foto subida en la carpeta fotos/ y devuelve su ruta."""
    os.makedirs(CARPETA_IMAGENES, exist_ok=True)
    extension = os.path.splitext(archivo.name)[1].lower()
    ruta = os.path.join(CARPETA_IMAGENES, uuid.uuid4().hex + extension)
    with open(ruta, "wb") as f:
        f.write(archivo.getbuffer())
    return ruta


modelo = cargar_modelo()

# ---------------------------- Barra lateral ----------------------------
logo = os.path.join("assets", "logo_mesafartai.png")
if os.path.exists(logo):
    st.sidebar.image(logo, width="stretch")
st.sidebar.title("MESAFARTAI")
perfil = st.sidebar.radio("Perfil", ["Soy Donador", "Soy ONG"])
tipo = "DONADOR" if perfil == "Soy Donador" else "ONG"
usuarios = db.listar_usuarios(tipo)
nombres = {u["nombre"]: u for u in usuarios}
nombre = st.sidebar.selectbox("Usuario", list(nombres))
usuario = nombres[nombre]

tab_chat, tab_dash = st.tabs(["💬 Chat", "📊 Dashboard de impacto"])

# ------------------------------- Chat ---------------------------------
with tab_chat:
    st.header("🍽️ MESAFARTAI – Logística y Inteligencia Asistiva contra el Hambre")
    clave = f"chat_{usuario['id']}"
    if clave not in st.session_state:
        saludo = ("¡Hola! Cuéntame qué alimentos quieres donar, por ejemplo: "
                  "_\"Tengo 30 kg de tomates que vencen mañana\"_." if tipo == "DONADOR" else
                  "¡Hola! Escribe _\"¿Qué donaciones hay para nosotros?\"_ para ver los alimentos asignados a tu ONG.")
        st.session_state[clave] = {"mensajes": [{"role": "assistant", "content": saludo}], "pendiente": None}
    estado = st.session_state[clave]

    for m in estado["mensajes"]:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            fotos_chat = [f for f in m.get("imagenes", []) if os.path.exists(f["ruta"])]
            if fotos_chat:
                columnas = st.columns(min(4, len(fotos_chat)))
                for i, f in enumerate(fotos_chat):
                    columnas[i % len(columnas)].image(f["ruta"], caption=f["pie"])

    # Foto opcional de la donación (solo donadores)
    foto = None
    if tipo == "DONADOR":
        foto = st.file_uploader(
            "📷 Foto de lo que vas a donar (opcional)",
            type=["jpg", "jpeg", "png"],
            key=f"foto_{usuario['id']}_{estado.get('n_foto', 0)}",
        )

    if texto := st.chat_input("Escribe tu mensaje..."):
        if foto is None:
            estado["imagen"] = None
        elif not estado.get("imagen"):
            estado["imagen"] = guardar_imagen(foto)

        estado["mensajes"].append({"role": "user", "content": texto})
        respuesta, estado["pendiente"], intencion, confianza = procesar_mensaje(
            modelo, usuario, texto, estado["pendiente"], ruta_imagen=estado.get("imagen"))
        mensaje = {"role": "assistant", "content": respuesta}
        if tipo == "ONG" and intencion in ("solicitar_alimentos", "consultar_estado"):
            mensaje["imagenes"] = [
                {"ruta": d["ruta_imagen"], "pie": f"#{d['id']} · {d['descripcion_alimento']}"}
                for d in db.donaciones_de_ong(usuario["id"]) if d["ruta_imagen"]
            ]
        estado["mensajes"].append(mensaje)

        if intencion == "registrar_donacion" and estado["pendiente"] is None:
            estado["imagen"] = None                          # la foto ya quedó guardada con la donación
            estado["n_foto"] = estado.get("n_foto", 0) + 1   # limpia el cuadro de subida
        st.rerun()

# ----------------------------- Dashboard ------------------------------
with tab_dash:
    st.header("📊 Dashboard logístico de impacto social")
    historial = pd.DataFrame(db.historial_completo())
    if historial.empty:
        st.info("Todavía no hay donaciones registradas. Registra una desde el chat 👈")
    else:
        clasificacion = historial["validez"].apply(clasificar_validez)
        historial["urgencia"] = clasificacion.apply(lambda c: c["urgencia"])
        historial["perecedero"] = clasificacion.apply(lambda c: {True: "Sí", False: "No", None: "—"}[c["perecedero"]])
        asignadas = historial[historial["estado"] == "ASIGNADA"]
        kg_total = float(historial["kg"].fillna(0).sum())
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Donaciones registradas", len(historial))
        c2.metric("Kg de alimento rescatados", f"{asignadas['kg'].fillna(0).sum():g}")
        c3.metric("Comidas estimadas", f"{int(asignadas['kg'].fillna(0).sum() * COMIDAS_POR_KG)}")
        c4.metric("Distancia promedio", f"{asignadas['distancia_km'].mean():.2f} km" if not asignadas.empty else "—")
        c5.metric("Urgentes (ALTA)", int((historial["urgencia"] == "ALTA").sum()))
        st.caption(f"Comidas estimadas = kg × {COMIDAS_POR_KG}. Kg totales registrados: {kg_total:g}.")

        izq, der = st.columns(2)
        with izq:
            st.subheader("Kg recibidos por ONG")
            st.bar_chart(asignadas.groupby("ong")["kg"].sum())
        with der:
            st.subheader("Kg donados por donador")
            st.bar_chart(historial.groupby("donador")["kg"].sum())

        st.subheader("Mapa de donadores y ONGs")
        todos = pd.DataFrame(db.listar_usuarios())
        st.map(todos.rename(columns={"latitud": "lat", "longitud": "lon"})[["lat", "lon"]])

        st.subheader("Historial de donaciones y recolecciones")
        st.dataframe(historial.drop(columns=["imagen"]), width="stretch", hide_index=True)

        fotos = historial[historial["imagen"].notna()]
        if not fotos.empty:
            st.subheader("📷 Fotos de las donaciones")
            cols = st.columns(4)
            for i, f in enumerate(fotos.itertuples()):
                if os.path.exists(f.imagen):
                    cols[i % 4].image(f.imagen, caption=f"#{f.id} · {f.alimento}")
