# 02 · Hardware: pinout, energía y corrección de puntos críticos

## 1. Correcciones a la guía original

| Tema | Guía original | Corrección |
|------|---------------|-----------|
| LCD I2C en la ESP32-CAM | Reasignar GPIO 1/3 (TX/RX) | **No usar GPIO 1/3**: dejan sin monitor serial y complican depurar. Usar **GPIO 14 (SDA) y GPIO 15 (SCL)** (libres si **no** se usa la microSD; ver nota). |
| Dataset en Edge Impulse | "Edge Impulse Data Forwarder" | El Data Forwarder es para **datos de sensores**, no imágenes. Para fotos: sketch que sirve `/capture` (JPEG) y descarga a PC, o fotos desde el celular, y se suben en *Studio → Data acquisition → Upload data* etiquetando por carpeta. Capturar **dentro del chasis real con el LED encendido**. |
| Latencia < 500 ms | Meta fija | Es optimista para ESP32-CAM. **Medir** y fijar la meta con datos; objetivo realista ≤ 1,5 s. Disparar la inferencia solo cuando hay objeto (no en bucle continuo). |
| Fuente 5 V / 5 A | "Evita brownout" (5 A obligatorio) | La corriente máxima no resuelve picos transitorios: añadir **condensador 470–1000 µF** (electrolítico) y 100 nF cerca de los pines 5V/GND de la ESP32-CAM, y cable de alimentación corto y grueso. |
| HX711 y lógica | No indicado | Alimentar el HX711 a **3,3 V** para que DT/SCK sean 3,3 V seguros para el ESP32. |
| LED blanco | "Instalar un LED" | No conectar el LED directo a un GPIO. Usar **MOSFET de nivel lógico** (p. ej. IRLZ44N o 2N7000 según corriente) con resistencia limitadora desde 5 V. |

## 2. Nodo de sensores (ESP32 DevKit, 30/38 pines)

| Función | Pin | Notas |
|---------|-----|-------|
| HC-SR04 TRIG | GPIO 25 | Salida 3,3 V; el HC-SR04 la acepta |
| HC-SR04 ECHO | GPIO 26 | **A través de divisor** 1 kΩ (serie desde ECHO) + 2 kΩ a GND → ≈ 3,33 V |
| HC-SR04 VCC / GND | 5 V / GND | |
| HX711 DT | GPIO 32 | |
| HX711 SCK | GPIO 33 | |
| HX711 VCC / GND | **3,3 V** / GND | Condensador 10–100 µF entre VCC y GND |
| LED de estado (opcional) | GPIO 27 | con resistencia 330 Ω |
| Pulsadores Plan B (plástico, papel/cartón, otros) | GPIO 18, 19, 21 | `INPUT_PULLUP`, al otro lado GND; la clase se publica con `fuente:"manual"` |

Evitar: GPIO 6–11 (flash), GPIO 0/2/12/15 como pines críticos (strapping), y 34/35/36/39 para salidas (solo entrada).

## 3. Nodo de visión (ESP32-CAM-MB, AI-Thinker)

Pines ocupados por la cámara OV2640: 0, 5, 18, 19, 21, 22, 23, 25, 26, 27, 32, 34, 35, 36, 39. GPIO 16 lo usa la PSRAM. **No tocar.**

| Función | Pin | Notas |
|---------|-----|-------|
| LCD I2C SDA | GPIO 14 | Pull-ups del módulo I2C (a 3,3 V o 5 V según módulo; verificar nivel) |
| LCD I2C SCL | GPIO 15 | |
| LED de iluminación (vía MOSFET) | GPIO 13 | Puerta del MOSFET con 100 Ω; pull-down 10 kΩ |
| LED flash integrado | GPIO 4 | Compartido con microSD; **no usar** si se mantiene el ruteo del LED externo |
| MicroSD | — | **No se usa.** Libera 12/13/14/15. No insertar tarjeta. |

Notas:
- GPIO 12 es pin de *strapping*: debe estar en nivel bajo al arrancar. No conectar nada que lo suba.
- Módulos LCD I2C comunes (PCF8574) trabajan a 5 V: alimentar a 5 V y comprobar que SDA/SCL queden en 3,3 V o usar convertidor de nivel.
- Activar **PSRAM** en la compilación. En PlatformIO usar `board = esp32cam` con:

```ini
[env:esp32cam]
platform = espressif32
board = esp32cam
framework = arduino
monitor_speed = 115200
build_flags =
    -DBOARD_HAS_PSRAM
    -mfix-esp32-psram-cache-issue
board_build.partitions = huge_app.csv
```

(El `platformio.ini` actual de `bryan/ecotacho-ai-node` usa `esp32dev`; cambiar a este entorno cuando llegue la placa.)

- Enfoque manual: la lente OV2640 viene enfocada al infinito. Girarla despacio hasta enfocar a la distancia real del objeto (≈ 15–25 cm). Fijar con una gota de pegamento al final.
- Poner la cámara con **iluminación constante** (LED + zona de escaneo cubierta). Es la mejor medida para que el modelo funcione dentro del tacho.

## 4. Alimentación y tierra

```
Fuente 5 V 5 A ──┬── ESP32 (sensores) VIN
                 ├── ESP32-CAM-MB 5V   (+ 470–1000 µF cerca)
                 ├── HC-SR04 VCC
                 └── LED vía MOSFET
GND común ───────── todos los GND (un solo punto, topología estrella)
```

- Un único nodo de GND (borne o regleta). Cables de potencia AWG 20–22 cortos.
- Medir el consumo real de ambas placas antes de decidir: una fuente de 5 V con ≥ 3 A alcanza si el cableado es corto y grueso (5 A solo si ya la tienen). Poner un **fusible o PTC** acorde en la línea de 5 V.
- No alimentar la ESP32-CAM por USB y por el pin de 5 V a la vez sin verificar la placa.
- Mantener el HX711 y los cables de la celda de carga **lejos de la antena Wi-Fi** y de los cables de potencia.

## 5. Mecánica y calibración

- Celda de carga: "sándwich" de dos bases rígidas; el recipiente de residuos va sobre la base superior y no toca las paredes (si roza, el peso deriva).
- **Tara al encender** con el tacho vacío; opción de tara remota.
- Calibrar con una pesa conocida (p. ej. 1 kg, 500 g) y guardar el factor de escala en NVS/Preferences.
- Anti-rebote: tras un cambio de peso, esperar **2 s de lectura estable** antes de publicar `peso/evento` (con `millis()`).
- Volumen: media móvil N=10 + descartar lecturas fuera de rango (2–400 cm). El sensor debe apuntar al centro, con tapa/boca que evite que un objeto lateral dé falso "lleno".
- "Tacho lleno": `volumen_pct >= 85` mantenido 10 s (evita falsos por objeto que cae).

## 6. Lista de comprobaciones antes de cablear

- [ ] GND común verificado con multímetro (continuidad)
- [ ] Tensión de 5 V medida sin carga y con la cámara capturando (≥ 4,8 V)
- [ ] ECHO del HC-SR04 medido ≤ 3,3 V
- [ ] PSRAM habilitada y reportada en el log serial de arranque
- [ ] Lente enfocada con un objeto de prueba a la distancia real
- [ ] Ningún GPIO 6–11 ni 1/3 usados
