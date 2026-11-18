# 06 · Ficha del proyecto (borrador)

> Las bases piden una ficha breve con: **problema, sector beneficiario, usuarios, solución, recursos e impacto esperado** y dicen que incluyen un formato al final. El PDF que tenemos tiene 3 páginas **y no contiene ese formato**. Pedirlo a cite.fiee@unmsm.edu.pe o en el formulario de inscripción; este texto se pega en él. Los corchetes son datos que el equipo debe completar.

**Nombre:** EcoTacho SM
**Desafío:** Medio ambiente (residuos y reciclaje)
**Representante:** [nombre, correo, teléfono] · **Integrantes (≤ 5):** Álvaro, Bryan, Sadith, Maricielo, Milagros [apellidos y especialidad]

**Problema.** La recolección de residuos en campus y espacios públicos se hace por rutas fijas, sin saber qué puntos están llenos, y la segregación depende de que cada persona acierte el contenedor. Esto genera viajes innecesarios, desborde y material reciclable contaminado. [Dato de línea base medido: ___].

**Sector beneficiario.** Universidades (caso piloto: UNMSM). Extensible a municipalidades y empresas.

**Usuarios.** Estudiantes y personal (depositan), personal de limpieza (recolecta), gestión ambiental (decide y reporta).

**Solución.** Tacho inteligente de bajo costo con dos nodos:
1. *Nodo de visión*: una ESP32-CAM clasifica el residuo localmente con TinyML (plástico, papel/cartón, otros; orgánico si alcanza el tiempo) y lo indica en una pantalla LCD.
2. *Nodo de sensores*: una ESP32 mide peso y nivel de llenado.
Los datos viajan por MQTT a un backend con MongoDB y se muestran en un dashboard en tiempo real con alertas de "tacho lleno" y estadísticas por tipo de residuo para priorizar rutas.

**Qué funciona, qué se simula y qué falta** (actualizar el 1 dic; ver `docs/03-plan-14-dias.md` §2):
- Funciona: [ ]
- Se simula: [ ] (p. ej. red de varios tachos en el dashboard)
- Falta: [ ] (p. ej. LoRaWAN, carcasa final, validación en campo prolongada)

**Recursos.** Hardware COTS ≈ S/ [total real con boletas] por tacho. Software abierto (Mosquitto, MongoDB, FastAPI, Next.js) y Edge Impulse gratuito. Equipo de 5 (2 electrónica, 3 telecomunicaciones). Apoyo deseado del CITE: pruebas en un punto real del campus, asesoría en entrenamiento del modelo y comunicaciones de largo alcance.

**Impacto esperado.** [Viajes de recolección evitados por semana: ___ (fuente: ___)] · [Kg de reciclables correctamente segregados: ___] · Retroalimentación educativa en el punto de depósito · Datos para reportes ambientales. Cifras solo con datos medidos (`docs/05`).

**Evidencias.** Repositorio https://github.com/bryanjpt25/ecotacho-sm · Video de la demo [enlace] · Fotos del prototipo [enlace].

**Declaración de uso de IA.** Ver `docs/07-pitch-y-declaracion-ia.md`.
