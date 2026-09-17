from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppError(Exception):
    """A domain error that maps directly to the platform error envelope."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


def _envelope(request: Request, code: str, message: str) -> dict:
    request_id = getattr(request.state, "request_id", "unknown")
    return {"error": {"code": code, "message": message, "request_id": request_id}}


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(request, exc.code, exc.message),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=_envelope(request, "VALIDATION_ERROR", "One or more fields are invalid."),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception(request: Request, _: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=_envelope(request, "INTERNAL_ERROR", "An unexpected error occurred."),
        )
