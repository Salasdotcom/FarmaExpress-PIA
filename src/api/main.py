from fastapi import FastAPI

app = FastAPI(
    title="FarmaExpress API",
    version="0.1.0",
    description="Lógica de negocio de FarmaExpress (PIA CLN).",
)


@app.get("/health", tags=["infra"])
def health() -> dict:
    return {"status": "ok"}
