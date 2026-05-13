from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError


class NotFoundError(Exception):
    def __init__(self, detail: str = "资源不存在"):
        self.detail = detail


class ForbiddenError(Exception):
    def __init__(self, detail: str = "无权访问"):
        self.detail = detail


class BadRequestError(Exception):
    def __init__(self, detail: str = "请求参数错误"):
        self.detail = detail


async def not_found_handler(_request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": exc.detail})


async def forbidden_handler(_request: Request, exc: ForbiddenError) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": exc.detail})


async def bad_request_handler(_request: Request, exc: BadRequestError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": exc.detail})


async def integrity_error_handler(_request: Request, _exc: IntegrityError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": "数据冲突，记录已存在"})


async def generic_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    import structlog

    structlog.get_logger().error("unhandled_exception", error=str(exc))
    return JSONResponse(status_code=500, content={"detail": "服务器内部错误"})
