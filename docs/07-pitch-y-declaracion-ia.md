# 07 · Pitch, rúbrica y declaración de IA

## 1. Rúbrica oficial (propuesta de las bases) y cómo ganar cada punto

La guía original usaba otra distribución ("Demostración y Usuario 35 %"). La de las bases es:

| Criterio | Pts | Qué evalúa el jurado | Qué mostramos |
|----------|-----|----------------------|---------------|
| Innovación | 20 | Valor diferencial | IA en el borde (sin enviar imágenes a la nube) + peso/volumen + correlación de eventos a bajo costo |
| **Impacto** | **25** | Relevancia del problema y beneficio | Línea base medida, viajes evitables, kg por tipo (`docs/05`) |
| Viabilidad | 20 | Recursos, costos, aplicación real | BOM con boletas, nube gratuita, plan de piloto con CITE (`docs/04`) |
| Demostración | 20 | Funcionamiento inicial y evidencias | Demo en vivo + tabla funciona/simula/falta + video de respaldo |
| Usuario y presentación | 15 | Necesidades del usuario y respuestas | Personas reales (limpieza, gestión), respuestas ensayadas |

Prioridad: **Impacto y Viabilidad suman 45** y hoy dependen de datos que no tenemos. Más valioso que pulir el dashboard es conseguir la línea base y las boletas.

## 2. Guion de 3 minutos (versión corta) — ajustar a la duración que comunique la organización

| Tiempo | Quién | Qué dice / hace |
|--------|-------|-----------------|
| 0:00–0:30 | Milagros | Problema con **un dato medido** del campus. Usuario: personal de limpieza que recorre rutas a ciegas. |
| 0:30–1:15 | Bryan | Acerca una botella. La cámara clasifica **en el propio tacho**, sin enviar imágenes; el LCD dice "Plástico". Menciona precisión real medida. |
| 1:15–2:00 | Álvaro + Sadith | Deposita la botella. Peso y nivel suben; el mensaje viaja por MQTT (con reconexión automática). |
| 2:00–2:30 | Maricielo | Señala el dashboard: el depósito aparece, `kg por tipo` cambia; todo guardado en MongoDB. |
| 2:30–3:00 | Milagros | Costo real del tacho, plan de piloto con el CITE, qué falta (honesto). |

Versión de 5 minutos: añadir apagado de Wi-Fi 20 s y recuperación, y la tabla de línea base.

## 3. Preguntas probables del jurado (ensayar respuestas)

1. ¿Qué precisión tiene el modelo? → Cifra real de la matriz de confusión, con las condiciones (iluminación, fondo).
2. ¿Qué pasa con objetos que no reconoce? → `No identificado`, no se cuenta; la clase `otros` los agrupa.
3. ¿Cómo evitan que alguien manipule el peso? → Es un prototipo; hay anti-rebote y lectura estable, pero no es antifraude.
4. ¿Se guardan imágenes? → No. Solo la etiqueta y la confianza. (Privacidad.)
5. ¿Cuánto cuesta escalar a 50 tachos? → Costo unitario × 50 con cotización por lote; nube compartida; conectividad por Wi-Fi/LoRaWAN.
6. ¿Qué funciona hoy y qué no? → Matriz de `docs/03-plan-14-dias.md` §2, sin adornos.
7. ¿Quién mantiene los tachos? → Personal de la facultad con un checklist de calibración y limpieza del lente.

## 4. Plan B (contingencias)

| Falla | Respuesta |
|-------|-----------|
| Wi-Fi/hotspot caído | El LCD sigue clasificando local. Dashboard mantiene último estado (icono amarillo). |
| Cable suelto / sensor muerto | Mock Switch en el dashboard (modo datos simulados) **diciéndolo al jurado**. |
| Modelo no acierta con la luz del salón | LED propio + cubierta de la zona de escaneo; llevar objetos de prueba ya validados. |
| Todo falla | Video de respaldo (2 min) + capturas. |

> Nota ética: si se usa el Mock Switch, **se declara**. Presentar datos simulados como reales contradice la regla de las bases de identificar qué funciona y qué se simula.

## 5. Declaración de uso de IA (borrador)

Las bases piden declarar el uso de IA y verificar los resultados. Texto base, a completar:

> "El equipo utilizó asistentes de IA generativa (Gemini y Claude) como apoyo para la planificación, redacción de documentación técnica y revisión de código. Todo el contenido fue revisado, verificado y adaptado por los integrantes, y las pruebas de hardware, entrenamiento del modelo y mediciones fueron realizadas por el equipo. El modelo de clasificación se entrena con la plataforma Edge Impulse sobre imágenes capturadas por el equipo [y el dataset público TrashNet, si se usa]. Los datos de impacto provienen de [mediciones propias / supuestos declarados]."

Si se usa TrashNet o TACO, mencionar su licencia y autores como "aportes de terceros" (regla 8 de las bases).
