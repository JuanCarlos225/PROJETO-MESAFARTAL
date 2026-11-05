# Alcance del Proyecto: MESAFARTAI – Logística e Inteligencia Asistiva en el Combate al Hambre

## 1. Problema de Negocio
Diariamente, grandes cantidades de alimentos aptos para el consumo son desechadas por comerciantes de mercados, supermercados, restaurantes y productores agrícolas. Los motivos principales incluyen la proximidad de la fecha de caducidad, pequeños defectos estéticos o exceso de inventario.

Al mismo tiempo, cientos de ONG, refugios y comedores comunitarios luchan a diario contra la escasez de suministros para alimentar a familias en situación de vulnerabilidad.

El principal cuello de botella de esta ecuación no es la falta de comida, sino la **ausencia de una logística ágil y una comunicación eficiente**: los donantes no disponen de tiempo para completar formularios extensos para donar insumos que vencerán en pocas horas. El **MESAFARTAI** nace para resolver este problema automatizando la captación de ofertas a través de chat y realizando el emparejamiento inteligente (*matchmaking*) hacia la institución más cercana en tiempo récord.

---

## 2. Público Objetivo

* **Donantes:** Comerciantes de mercados, supermercados, restaurantes, panaderías, productores rurales y comercios en general que poseen excedentes de alimentos aptos para el consumo y necesitan una forma sencilla y rápida de realizar la donación.
* **ONG (Receptores):** Instituciones sin fines de lucro, refugios, comedores comunitarios y entidades de asistencia social que requieren donaciones de alimentos para apoyar a poblaciones en situación de vulnerabilidad social.

---

## 3. Alcance de las Intenciones Tratadas y Datos Recopilados

### Intenciones (NLU)
El asistente conversacional está diseñado para identificar y procesar las siguientes intenciones de los usuarios:

1. `registrar_donacion`: Registro de nuevos alimentos disponibles para donar por parte de los donantes.
2. `solicitar_alimentos`: Registro de demandas o necesidades de suministros por parte de las ONG.
3. `consultar_estado`: Consulta del estado de donaciones, recolecciones programadas o solicitudes en curso.
4. `fuera_de_alcance`: Captura de mensajes que no tienen relación con el objetivo del sistema, activando una respuesta de alternativa (*fallback*).

### Datos Recopilados en el Chat
Mediante el procesamiento de lenguaje natural y la extracción automatizada (Regex), el chat recopila la siguiente información:

* **Datos del Donante / ONG:** Nombre o Razón Social, tipo de perfil (`Donante` o `ONG`) y ubicación/dirección.
* **Datos de los Alimentos (Donación):**
  * **Tipo de Alimento:** Categoría o producto (ej. tomates, pan, arroz).
  * **Cantidad y Unidad de Medida:** Captura de volúmenes (ej. `30 kg`, `5 cajas`, `100 unidades`).
  * **Fecha de Caducidad / Urgencia:** Fecha o límite de tiempo para la recolección (ej. `hoy`, `mañana`, `hasta las 18:00 h`).
