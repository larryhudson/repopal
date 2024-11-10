from fastapi import FastAPI

from repopal.api.routes import router as api_router
from repopal.api.auth import router as auth_router
from repopal.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(api_router, prefix="/api")
app.include_router(auth_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
