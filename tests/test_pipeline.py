"""Pruebas del pipeline completo. Ejecutar desde la raíz:  python -m pytest tests  (o python tests/test_pipeline.py)"""
import os
import sys
import tempfile
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import database as db  # noqa: E402

db.DB_PATH = os.path.join(tempfile.mkdtemp(), "test.db")  # base temporal para no tocar la real
db.inicializar_base()

from src.chatbot import procesar_mensaje  # noqa: E402
from src.extraccion import clasificar_validez, extraer_entidades  # noqa: E402
from src.nlu import entrenar  # noqa: E402

MODELO = entrenar()
AHORA = datetime(2026, 10, 9, 10, 0)
DONADOR = db.listar_usuarios("DONADOR")[0]
ONG = db.listar_usuarios("ONG")[0]


def test_extraccion():
    e = extraer_entidades("Quiero donar 30 kg de tomates que vencen mañana a las 18h", AHORA)
    assert e["alimento"] == "tomates" and e["cantidad_kg"] == 30 and e["validez"] == "2026-10-10 18:00"
    e = extraer_entidades("tengo 5 cajas de lechuga, vence hoy", AHORA)
    assert e["cantidad_kg"] == 50 and e["alimento"] == "lechuga" and e["validez"] == "2026-10-09"
    e = extraer_entidades("quero doar 500 g de queijo amanhã", AHORA)
    assert e["cantidad_kg"] == 0.5 and e["validez"] == "2026-10-10"


def test_fallback_por_umbral():
    resp, _, intencion, _ = procesar_mensaje(MODELO, DONADOR, "algo", None, AHORA)
    assert intencion == "fallback" and "No estoy seguro" in resp


def test_donacion_completa_y_match():
    resp, pendiente, intencion, _ = procesar_mensaje(
        MODELO, DONADOR, "Quiero donar 30 kg de tomates que vencen mañana", None, AHORA)
    assert intencion == "registrar_donacion" and pendiente is None and "ONG más cercana" in resp
    assert db.donaciones_de_donador(DONADOR["id"])[0]["estado"] == "ASIGNADA"


def test_slot_filling():
    resp, pendiente, _, _ = procesar_mensaje(MODELO, DONADOR, "quiero donar pan", None, AHORA)
    assert pendiente is not None and "cantidad" in resp.lower()
    resp, pendiente, _, _ = procesar_mensaje(MODELO, DONADOR, "20 kg", pendiente, AHORA)
    assert pendiente is None and "registrada" in resp


def test_ong_consulta_y_perfil_incorrecto():
    resp, _, _, _ = procesar_mensaje(MODELO, ONG, "necesitamos alimentos para el comedor", None, AHORA)
    assert "Donaciones asignadas" in resp or "no hay donaciones" in resp
    resp, _, _, _ = procesar_mensaje(MODELO, ONG, "quiero donar 10 kg de arroz", None, AHORA)
    assert "donadores" in resp


def test_foto_opcional():
    resp, _, _, _ = procesar_mensaje(MODELO, DONADOR, "Quiero donar 12 kg de pan", None, AHORA,
                                     ruta_imagen="fotos/prueba.jpg")
    assert "registrada" in resp
    ong_id = [d for d in db.historial_completo() if d["alimento"] == "pan"][0]["imagen"]
    assert ong_id == "fotos/prueba.jpg"
    assert any(d["ruta_imagen"] == "fotos/prueba.jpg" for u in db.listar_usuarios("ONG")
               for d in db.donaciones_de_ong(u["id"]))
    procesar_mensaje(MODELO, DONADOR, "Quiero donar 3 kg de arroz", None, AHORA)  # sin foto sigue funcionando


def test_perecedero_y_urgencia():
    e = extraer_entidades("Estamos doando 35 kg de leite fresco que vence em 2 dias!", AHORA)
    assert e["cantidad_kg"] == 35 and e["perecedero"] is True and e["urgencia"] == "ALTA"
    e = extraer_entidades("20 kg de arroz con validez de 6 meses", AHORA)
    assert e["perecedero"] is False and e["urgencia"] == "BAJA"
    e = extraer_entidades("10 cajas de alface que vencem em 5 dias", AHORA)
    assert e["perecedero"] is True and e["urgencia"] == "MEDIA"
    assert clasificar_validez(None)["urgencia"] == "SIN FECHA"
    assert clasificar_validez("2026-10-01", AHORA)["urgencia"] == "VENCIDA"


def test_respuesta_muestra_urgencia():
    resp, _, _, _ = procesar_mensaje(MODELO, DONADOR, "Quiero donar 8 kg de leche que vence en 2 días", None, AHORA)
    assert "urgencia ALTA" in resp and "perecedero" in resp


def test_estres_mensajes_raros():
    for texto in ["", "   ", "🍎🍎🍎", "a" * 2000, "DROP TABLE usuarios;", "30", "kg kg kg"]:
        procesar_mensaje(MODELO, DONADOR, texto, None, AHORA)


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if nombre.startswith("test_"):
            fn()
            print("OK", nombre)
