import time
from collections import defaultdict
from typing import Callable, Dict, List, Tuple
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        calls: int = 100,
        period: int = 60,
        excluded_paths: List[str] = None
    ):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.excluded_paths = excluded_paths or ["/health", "/docs", "/openapi.json", "/redoc"]
        self.clients: Dict[str, List[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _is_excluded(self, path: str) -> bool:
        return any(path.startswith(excluded) for excluded in self.excluded_paths)

    def _clean_old_calls(self, client_id: str, current_time: float) -> None:
        cutoff = current_time - self.period
        self.clients[client_id] = [
            t for t in self.clients[client_id] if t > cutoff
        ]

    def _should_rate_limit(self, client_id: str) -> Tuple[bool, int]:
        current_time = time.time()
        self._clean_old_calls(client_id, current_time)

        calls_made = len(self.clients[client_id])
        remaining = max(0, self.calls - calls_made)
        reset_time = int(current_time + self.period) if calls_made > 0 else int(current_time + self.period)

        if calls_made >= self.calls:
            return True, reset_time

        self.clients[client_id].append(current_time)
        return False, reset_time

    async def dispatch(self, request: Request, call_next: Callable):
        if self._is_excluded(request.url.path):
            return await call_next(request)

        client_id = self._get_client_ip(request)
        is_limited, reset_time = self._should_rate_limit(client_id)

        if is_limited:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please try again later.",
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "retry_after": reset_time - int(time.time())
                },
                headers={
                    "Retry-After": str(reset_time - int(time.time())),
                    "X-RateLimit-Limit": str(self.calls),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time)
                }
            )

        response = await call_next(request)

        remaining = max(0, self.calls - len(self.clients[client_id]))
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response
