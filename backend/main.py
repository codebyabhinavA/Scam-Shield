from fastapi import FastAPI

app = FastAPI(title="Scam Shield API")


@app.get("/health")
def health():
    return {"status": "ok"}
