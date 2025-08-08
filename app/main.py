from fastapi import FastAPI
from app.api.v1 import tag

app = FastAPI(
    title="Text Tagger API",
    version="1.0.0",
    description="AI-powered text tagging API"
)

app.include_router(tag.router, prefix="/v1")

@app.get("/health")
def health_check():
    return {"status": "ok"}
