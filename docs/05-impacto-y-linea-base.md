# 05 · Impacto, línea base y métricas

> *Impacto* vale **25 puntos** (el criterio más pesado): "relevancia del problema y beneficio para los usuarios". Hoy la guía no tiene **ningún dato propio**. Este documento define cómo conseguirlos en pocos días sin inventar cifras.

## 1. Problema (para la ficha)

Los puntos de acumulación de residuos se vacían por **ruta fija**, sin saber cuáles están llenos, y la **segregación** depende de que cada persona acierte el contenedor correcto. Resultado: viajes de limpieza innecesarios, tachos desbordados y material reciclable contaminado.

- **Sector:** universidades (UNMSM como caso piloto); extensible a municipalidades y empresas.
- **Usuarios:** (1) estudiantes y personal que depositan residuos; (2) personal de limpieza / gestión ambiental que recolecta; (3) responsables de gestión ambiental que deciden rutas y reportan.

## 2. Qué medir antes del 2 de diciembre (línea base)

Con autorización de la facultad/administración (las bases exigen autorización para pruebas en infraestructura real). Si no hay autorización, medir en un punto de la facultad o en un punto doméstico y **decirlo**.

| Dato | Cómo medirlo | Tiempo |
|------|-------------|--------|
| Frecuencia actual de recolección en 1–2 puntos | Preguntar al personal de limpieza / observar 2–3 días | 1 h |
| % del tacho lleno al momento de vaciarlo | Foto + estimación al pasar el recolector | 2–3 días |
| Peso por vaciado | Balanza de piso o la propia celda de carga | 2–3 días |
| % de contaminación (residuos mal ubicados) | Revisar una muestra de 1 bolsa y contar | 1 h |
| Precisión del modelo en el chasis | Matriz de confusión con 30 objetos reales por clase | 1 día |

Anotar en una hoja (fecha, lugar, dato, responsable). Estos datos van a la ficha y al pitch **con su fuente**.

## 3. KPIs del sistema

| KPI | Definición | Fuente |
|-----|-----------|--------|
| Kg depositados por tipo | Σ `delta_kg` por `clase` en `deposits` | MongoDB |
| % clasificación válida | eventos con `clase` distinta de `no_seguro` / total de eventos de visión | MongoDB |
| Precisión del modelo | aciertos / pruebas manuales en chasis | Matriz de confusión |
| Latencia de inferencia | Mediana y p95 medidas en el log serial durante las pruebas (no viaja en el contrato) | Log serial |
| Latencia extremo a extremo | depósito → gráfico actualizado | Medida con cronómetro/log |
| Uptime de nodos | % del tiempo `online` | `node_status` |
| Recolecciones evitables | Veces que se vació con `volumen_pct` < 60 % en el esquema actual | Línea base |

## 4. Cálculo de impacto (con supuestos explícitos)

Rellenar los corchetes con **datos medidos**; si no hay, marcar "supuesto".

- Recolecciones por semana hoy = **[R_hoy]**.
- Recolecciones con aviso al 85 % = **[R_nueva]** (estimar con la serie de llenado de las pruebas).
- Viajes evitados por semana = R_hoy − R_nueva.
- Ahorro = viajes evitados × tiempo por viaje **[min]** × costo por minuto **[S/]** (preguntar a administración, o decir "sin costo estimado").
- Material recuperable = Σ kg de `plastico` + `papel_carton` correctamente segregados.

> **No afirmar** reducciones porcentuales ni cifras de ahorro que no salgan de estas fórmulas con datos reales. Un jurado técnico lo pregunta.

## 5. Beneficio cualitativo (verificable)

- El personal de limpieza ve en el dashboard qué tachos están ≥ 85 % y prioriza.
- Retroalimentación inmediata al usuario ("Plástico detectado") para enseñar la segregación.
- Dato histórico para reportes de gestión ambiental sin planillas manuales.

## 6. Limitaciones a declarar

- Precisión limitada por el hardware (ESP32-CAM, imágenes de baja resolución).
- Objetos mixtos o sucios pueden confundirse; la clase `otros` agrupa metal y vidrio.
- Prototipo de un solo tacho; la red de tachos se demuestra con datos simulados (se dice explícitamente).
- Privacidad: la cámara solo procesa localmente y **no guarda ni transmite imágenes**. Solo se envía la etiqueta.
