#include <Arduino.h>

// Configuración de temporización no bloqueante
const unsigned long INFERENCE_INTERVAL_MS = 3000; // Frecuencia de simulación: 3 segundos
unsigned long previousMillis = 0;

// Estructura de datos simulada para TinyML
struct InferenceResult {
    const char* label;
    float confidence;
};

// Banco de pruebas de clasificación de residuos
const InferenceResult MOCK_DATASET[] = {
    {"PLASTICO_PET", 0.94f},
    {"CARTON_PAPEL", 0.89f},
    {"RESIDUO_ORGANICO", 0.96f},
    {"NO_IDENTIFICADO", 0.45f}
};
const size_t DATASET_SIZE = sizeof(MOCK_DATASET) / sizeof(MOCK_DATASET[0]);
size_t currentIndex = 0;

/**
 * Simula la ejecución de inferencia de Edge Impulse (INT8 Quantized Model)
 */
void ejecutarMockInferencia() {
    InferenceResult actual = MOCK_DATASET[currentIndex];
    
    Serial.println("\n-------------------------------------------");
    Serial.println("[TinyML Node] Captura de frame OV2640 completada.");
    Serial.println("[TinyML Node] Procesando tensor de entrada en memoria...");
    
    Serial.print("[TinyML Node] Clasificación: ");
    Serial.println(actual.label);
    Serial.print("[TinyML Node] Confianza: ");
    Serial.print(actual.confidence * 100.0f, 2);
    Serial.println("%");
    Serial.println("-------------------------------------------");

    // Avanzar al siguiente elemento de prueba
    currentIndex = (currentIndex + 1) % DATASET_SIZE;
}

void setup() {
    Serial.begin(115200);
    while (!Serial && millis() < 3000); // Espera inicial de puerto serie
    
    Serial.println("=================================================");
    Serial.println("   EcoTacho SM - Edge AI Node (Mock Engine)    ");
    Serial.println("=================================================");
}

void loop() {
    unsigned long currentMillis = millis();

    // Comprobación no bloqueante del intervalo de ejecución
    if (currentMillis - previousMillis >= INFERENCE_INTERVAL_MS) {
        previousMillis = currentMillis;
        ejecutarMockInferencia();
    }

    // Tareas continuas de fondo (Mantener Wi-Fi, MQTT client.loop(), etc.)
    // Esta sección se ejecuta miles de veces por segundo sin congelarse.
}