// EN PLATFORMIO, ESTA LÍNEA ES OBLIGATORIA
// En Arduino IDE está oculta, pero aquí estás programando en C++ real.
#include <Arduino.h> 

void setup() {
  Serial.begin(115200);
  Serial.println("Iniciando nodo de Edge AI...");
}

void loop() {
  Serial.println("Esperando modelo TinyML...");
  delay(2000); // Usaremos millis() más adelante, este delay es solo para probar la consola
}