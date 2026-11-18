# 04 · Lista de materiales (BOM) y costos

> **Estado: estimación.** Los precios son rangos de mercado local en soles **sin verificar**. Antes de la exposición hay que reemplazar cada rango por el **precio real de boleta/cotización** (guardar fotos de las boletas). Un número respaldado por boletas vale más ante el jurado (criterio *Viabilidad*, 20 pts) que una cifra redonda.

## 1. BOM del prototipo (1 tacho)

| # | Componente | Cant. | S/ mín | S/ máx |
|---|-----------|-------|--------|--------|
| 1 | ESP32-CAM con base MB (OV2640) | 1 | 45 | 65 |
| 2 | ESP32 DevKit (30/38 pines) | 1 | 28 | 40 |
| 3 | Sensor ultrasónico HC-SR04 | 1 | 6 | 10 |
| 4 | Celda de carga 50 kg + módulo HX711 | 1 | 20 | 35 |
| 5 | LCD 16x2 con módulo I2C | 1 | 15 | 25 |
| 6 | Fuente 5 V 5 A (adaptador de pared) | 1 | 30 | 50 |
| 7 | LED blanco de alto brillo + MOSFET nivel lógico + resistencias | 1 | 8 | 15 |
| 8 | Condensadores (10 µF, 100 µF, 470–1000 µF, 100 nF) | 1 kit | 4 | 8 |
| 9 | Resistencias (1 kΩ, 2 kΩ, 330 Ω, 10 kΩ, 100 Ω) | 1 kit | 3 | 6 |
| 10 | Protoboard + placa perforada | 1 | 15 | 25 |
| 11 | Cables dupont, AWG 22, borneras, fusible/PTC | 1 kit | 15 | 30 |
| 12 | Tacho / recipiente base (20–40 L) | 1 | 25 | 60 |
| 13 | Acrílico / MDF para sándwich de la celda y soportes | 1 | 25 | 50 |
| 14 | Señalética / vinil / impresos | 1 | 10 | 25 |
| | **Subtotal prototipo** | | **249** | **444** |
| 15 | Repuestos críticos (1 ESP32-CAM-MB + 1 ESP32) | 1 | 73 | 105 |
| | **Total con repuestos** | | **322** | **549** |

Software y nube: Mosquitto y MongoDB en Docker local o MongoDB Atlas (plan gratuito), hotspot del celular, Edge Impulse (plan gratuito para desarrolladores), Next.js/FastAPI (código abierto). **S/ 0** de licencias.

## 2. Qué decir sobre costos

- La guía original afirmaba **S/ 600–950**. Esa cifra **no se sostiene con este BOM**: el rango estimado es ≈ **S/ 250–450** (prototipo) o ≈ **S/ 320–550** con repuestos. Es una mejor noticia para *Viabilidad*, **siempre que se confirme con boletas**.
- Usar en el pitch el total **real** (boletas), con el desglose a mano por si preguntan.
- Si se incluyen horas de trabajo del equipo, decirlo aparte; no se mezclan con el costo de hardware.

## 3. Escalabilidad (para responder al jurado)

| Concepto | Prototipo | Versión piloto (referencia a calcular) |
|----------|-----------|------------------------------------------|
| Hardware por tacho | S/ 250–450 | Baja con compra por lote; **cotizar** 10 unidades |
| Conectividad | Hotspot | Wi-Fi del campus o LoRaWAN (trabajo futuro) |
| Nube | S/ 0 (nivel gratuito) | Un VPS pequeño compartido por todos los tachos |
| Mantenimiento | — | Calibración periódica de celda de carga; limpieza del lente |

> No inventar cifras de ahorro. Las de impacto se calculan con la fórmula de `docs/05` usando mediciones reales o supuestos declarados como tales.

## 4. Riesgos de compra

- Plazos de envío: pedir hoy ESP32-CAM-MB, celda de carga y fuente; tener alternativa de tienda física en Lima.
- Comprar **repuestos** de ESP32/ESP32-CAM (se queman con facilidad al cablear mal).
- Verificar que la fuente entregue 5 V estable (medir con multímetro) antes de conectar las placas.
