from core.config import settings
from fastapi import APIRouter, responses
from schemas import health

router = APIRouter()


class HealthResponse(responses.JSONResponse):
    media_type = "application/health+json"


@router.get(
    "/health",
    response_model=health.Health,
    response_class=HealthResponse,
    responses={500: {"model": health.Health}},
)
async def get_health(response: HealthResponse):
    response.headers["Cache-Control"] = "max-age=3600"

    content = {
        "status": health.Status.PASS,
        "version": settings.VERSION,
        "releaseId": settings.RELEASE_ID,
    }

    return content
