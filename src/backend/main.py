from fastapi import FastAPI

from backend.api.routes.documents import router as documents_router

# Now here creating object of FastAPI class
app = FastAPI(
    title="IntelliDocs API",
    description="AI-powered document knowledge base using Vector Database",
    version="1.0.0",
)

app.include_router(documents_router)
