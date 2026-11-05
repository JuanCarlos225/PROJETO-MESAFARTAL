# MESAFARTAI – Logística e Inteligência Assistiva no Combate à Fome

![Logo MESAFARTAI](assets/logo_mesafartai.png)

## Descripción

MESAFARTAI es una aplicación conversacional en Python que conecta a donadores de alimentos (supermercados, restaurantes, feriantes, productores) con ONGs y comedores comunitarios. El donador escribe un mensaje informal por chat; el sistema entiende la intención (NLU), extrae productos, cantidades y fechas de validez (Regex) y encuentra la ONG más cercana mediante un algoritmo KNN, evitando que alimentos aptos para el consumo sean desperdiciados.

## Alineación con la ODS 2 de la ONU (Hambre Cero)

El Objetivo de Desarrollo Sostenible 2: Hambre Cero de la ONU busca acabar con el hambre, lograr la seguridad alimentaria, mejorar la nutrición y promover la agricultura sostenible. Esta solución se alinea directamente con dichos propósitos a través de las siguientes líneas de acción:

- **Seguridad alimentaria y nutrición:** Facilita la disponibilidad, el acceso y la distribución eficiente de alimentos nutritivos y de calidad, reduciendo las pérdidas en la cadena de suministro e impactando positivamente en las comunidades vulnerables.
- **Sostenibilidad y resiliencia agrícola:** Promueve prácticas responsables en la producción y consumo de alimentos, optimizando el uso de recursos y mitigando el impacto ambiental.
- **Inclusión e impacto social:** Fortalece la colaboración entre productores, distribuidores y comunidades para garantizar un sistema alimentario más justo, inclusivo y resiliente.

## Integrantes

| Nombre completo | RA |
|---|---|
| Brayan Daniel Rangel Urbina | [COMPLETAR] |
| Juan Carlos Rosales Vargas | [COMPLETAR] |

## Cómo funciona

1. El usuario escribe un mensaje informal en el chat (por ejemplo: _"Tengo 30 kg de tomates que vencen mañana a las 18h"_).
2. **NLU** (TF-IDF + Regresión Logística, Scikit-Learn) clasifica la intención: `registrar_donacion`, `solicitar_alimentos`, `consultar_estado` o `fuera_de_alcance`. Si la confianza es menor a 0,60 responde con un mensaje de *fallback*.
3. **Regex** extrae alimento, cantidad (kg, g, cajas, unidades, porciones, litros) y validez (hoy, mañana, 18h, dd/mm, en N días, N meses). Con la validez se calcula si el alimento es **perecedero** (menos de 30 días) o **no perecedero** (validez en meses) y su **urgencia**: ALTA (≤ 3 días), MEDIA (4 a 7 días) o BAJA (más de 7 días).
4. Si el donador lo desea, puede adjuntar una **foto opcional** de la donación; las ONGs la ven en el chat y en el dashboard.
5. **KNN** (distancia haversine sobre latitud/longitud) encuentra la ONG más cercana y guarda el *match* en **SQLite3**.
6. Streamlit muestra el chat (perfil **Soy Donador / Soy ONG**) y un dashboard de impacto social.

## Cómo ejecutar

```bash
pip install -r requirements.txt
python src/database.py        # crea mesafartai.db con datos de prueba
streamlit run app.py          # abre la aplicación
python tests/test_pipeline.py # pruebas del pipeline
```

## Estructura del repositorio

```
PROJETO-MESAFARTAI/
├── app.py               # interfaz Streamlit (chat + dashboard)
├── requirements.txt
├── assets/              # logotipo (logo_mesafartai.png)
├── docs/                # regras.txt, escopo_projeto.md, diagramas
├── src/
│   ├── database.py      # SQLite3: tablas, datos de prueba y consultas
│   ├── nlu.py           # clasificador de intenciones + umbral
│   ├── extraccion.py      # extracción de entidades con Regex
│   ├── matchmaking.py   # KNN para asignar la ONG más cercana
│   └── chatbot.py       # orquesta todo el flujo
├── desafios/            # desafío Regex para Colab (desafio_regex_mesafartai.py)
└── tests/test_pipeline.py
```
