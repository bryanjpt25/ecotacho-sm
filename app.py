from fastapi import FastAPI

# Inicialización de la aplicación FastAPI
app = FastAPI(
    title="Eco Punto Smart - API Ingestion & Gateway",
    description="Backend para recepción de telemetría MQTT y persistencia en MongoDB",
    version="0.1.0"
)

@app.get("/")
async def root():
    """Ruta base para verificar el estado del servidor."""
    return {
        "status": "online",
        "project": "Eco Punto Smart",
        "message": "Servidor FastAPI inicializado correctamente."
    }

@app.get("/health")
async def health_check():
    """Health-check endpoint para monitoreo del backend."""
    return {"status": "ok"}