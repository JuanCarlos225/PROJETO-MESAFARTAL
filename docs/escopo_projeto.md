# MESAFARTAI – Alcance del Proyecto

## 1. Problema de negocio

Diariamente se descartan toneladas de alimentos aptos para el consumo por parte de feriantes, supermercados, restaurantes y productores, debido a la cercanía de la fecha de validez, pequeños defectos estéticos o exceso de inventario. Al mismo tiempo, ONGs, albergues y comedores comunitarios enfrentan escasez de suministros para alimentar a familias en situación de vulnerabilidad.

El cuello de botella no es la falta de comida, sino la falta de logística ágil y comunicación eficiente: un comerciante no tiene tiempo de llenar formularios extensos para donar 30 kg de alimento que vencerán en 24 horas.

**Solución:** un chatbot en Python que entiende mensajes informales, extrae los datos de la donación y asigna automáticamente la ONG más cercana.

## 2. Público objetivo

| Perfil | Descripción | Necesidad |
|---|---|---|
| **Donadores** | Supermercados, restaurantes, feriantes, productores | Registrar una donación en segundos, por chat, sin formularios |
| **ONGs** | Albergues, comedores y cocinas comunitarias | Solicitar alimentos y recibir donaciones cercanas y a tiempo |

## 3. Alcance de las intenciones tratadas

| Intención | Descripción |
|---|---|
| `registrar_donacion` | El donador registra una donación de alimentos |
| `solicitar_alimentos` | La ONG solicita alimentos disponibles |
| `consultar_estado` | Consulta del estado de una donación o recolección |
| `fuera_de_alcance` | Cualquier mensaje ajeno al sistema (activa respuesta de fallback) |

Las frases ambiguas (confianza < 0,60) recibirán una respuesta de fallback amigable.

## 4. Datos recolectados en el chat

- **Alimento:** tipo/descripción del producto.
- **Cantidad:** kg, cajas o unidades.
- **Validez:** plazo (hoy, mañana, hora como "18h", "en 2 días", "6 meses").
- **Perecedero / urgencia:** calculados a partir de la validez (perecedero si vence en menos de 30 días; urgencia ALTA, MEDIA o BAJA).
- **Ubicación:** Código postal del donador/ONG (con latitud y longitud) para calcular distancias.
- **Contacto:** teléfono.
- **Foto (opcional):** imagen del alimento que se va a donar.

## 5. Identidad visual – Prompt del logotipo

Prompt exacto utilizado en el generador de imágenes por IA:

```
[PEGAR AQUÍ EL PROMPT EXACTO QUE USARON]
```

Archivo generado: `assets/logo_mesafartai.png`
