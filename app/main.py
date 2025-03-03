from api.v1.routers import agent, consultant, file, health
from bson.errors import InvalidId
from core.config import settings
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

app = FastAPI(title=settings.APP_TITLE)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    router=health.router, prefix=settings.API_V1_STR, tags=["health"]
)

app.include_router(
    router=consultant.router, prefix=settings.API_V1_STR, tags=["consultant"]
)

app.include_router(
    router=agent.router, prefix=settings.API_V1_STR, tags=["agent"]
)
app.include_router(
    router=file.router, prefix=settings.API_V1_STR, tags=["files"]
)


@app.get("/", include_in_schema=False)
async def index() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.exception_handler(InvalidId)
async def id_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Invalid ID"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=1200)
