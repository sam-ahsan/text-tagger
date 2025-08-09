from fastapi import FastAPI
from app.api.v1 import tag

app = FastAPI(
    title="Text Tagger API",
    version="0.1.0",
    description="AI-powered text tagging API"
)

app.include_router(tag.router, prefix="/v1", tags=["tagging"])

@app.get("/", tags=["root"])
def root():
    return {
        "message": "Welcome to the text-tagger-api. See /docs for API documentation."
    }

@app.get("/favicon", include_in_schema=False)
def favicon():
    return {
        "message": "This is the favicon endpoint."
    }

@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }
