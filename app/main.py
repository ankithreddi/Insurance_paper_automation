from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from app.routes import router

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="PDF Data Extractor",
        version="1.0.0",
        description="API for extracting data from policy PDFs",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app = FastAPI(
    docs_url="/pdf/docs",
    redoc_url="/pdf/redoc",
    openapi_url="/pdf/openapi.json"
)
app.openapi = custom_openapi
app.include_router(router, prefix="/pdf")

@app.get("/")
async def root():
    return {"message": "Welcome to PDF Data Extractor API"}