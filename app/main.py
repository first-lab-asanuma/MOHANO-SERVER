import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import ServiceError


logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")

    @app.exception_handler(ServiceError)
    async def handle_service_error(_: Request, error: ServiceError) -> JSONResponse:
        return JSONResponse(
            status_code=error.status_code,
            content={"code": error.code, "message": error.message},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_: Request, error: Exception) -> JSONResponse:
        # 개인정보·credential을 남기지 않도록 예외 본문이나 요청값은 로그에 쓰지 않는다.
        logger.error("Unhandled server error: %s", type(error).__name__)
        return JSONResponse(
            status_code=500,
            content={
                "code": "internal_server_error",
                "message": "The server could not complete this request.",
            },
        )

    if settings.cors_origins or settings.cors_origin_regex:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_origin_regex=settings.cors_origin_regex or None,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
            allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
        )

    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
