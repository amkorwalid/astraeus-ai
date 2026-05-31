from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse


class AstraeusException(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AstraeusException):
    def __init__(self, resource: str):
        super().__init__(f"{resource} not found", 404)


class UnauthorizedError(AstraeusException):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, 401)


class ForbiddenError(AstraeusException):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, 403)


class ConflictError(AstraeusException):
    def __init__(self, message: str):
        super().__init__(message, 409)


class ValidationError(AstraeusException):
    def __init__(self, message: str):
        super().__init__(message, 422)


def setup_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AstraeusException)
    async def astraeus_exception_handler(request: Request, exc: AstraeusException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.message},
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail},
        )
