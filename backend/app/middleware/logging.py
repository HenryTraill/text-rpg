"""
Logging middleware for API requests and responses.

This module implements:
- Structured request/response logging
- Performance monitoring
- Error tracking
- Request ID generation
- Sensitive data filtering
"""

import time
import json
import logging
import uuid
from typing import Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse
import traceback

from ..core.config import settings

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive logging middleware for API requests and responses.

    Features:
    - Request/response logging with timing
    - Structured JSON logging format
    - Request ID generation and propagation
    - Sensitive data filtering
    - Error tracking and stack traces
    """

    def __init__(self, app):
        super().__init__(app)

        # Configure structured logging
        self.logger = logging.getLogger("api.requests")

        # Sensitive fields to exclude from logging
        self.sensitive_fields = {
            "password",
            "token",
            "secret",
            "key",
            "authorization",
            "cookie",
            "session",
            "csrf",
            "private",
            "confidential",
        }

        # Paths to exclude from detailed logging
        self.excluded_paths = {"/health", "/metrics", "/favicon.ico"}

        # Maximum response body size to log (in bytes)
        self.max_response_size = 10240  # 10KB

    async def dispatch(self, request: Request, call_next):
        """Process request with comprehensive logging."""
        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Add request ID to request state
        request.state.request_id = request_id

        # Skip detailed logging for excluded paths
        if request.url.path in self.excluded_paths:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response

        # Log request start
        start_time = time.time()

        # Capture request details
        request_data = await self._capture_request_data(request)

        self.logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "event": "request_start",
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "headers": self._filter_headers(dict(request.headers)),
                "client_ip": self._get_client_ip(request),
                "user_agent": request.headers.get("user-agent"),
                "request_size": len(request_data.get("body", "")),
                "timestamp": start_time,
            },
        )

        # Process request and capture response
        try:
            response = await call_next(request)

            # Calculate processing time
            process_time = time.time() - start_time

            # Capture response details
            response_data = await self._capture_response_data(response)

            # Log successful response
            self.logger.info(
                "Request completed",
                extra={
                    "request_id": request_id,
                    "event": "request_complete",
                    "method": request.method,
                    "url": str(request.url),
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "response_size": len(response_data.get("body", "")),
                    "process_time": round(process_time, 4),
                    "timestamp": time.time(),
                },
            )

            # Add performance tracking
            if process_time > 1.0:  # Log slow requests (>1 second)
                self.logger.warning(
                    "Slow request detected",
                    extra={
                        "request_id": request_id,
                        "event": "slow_request",
                        "method": request.method,
                        "path": request.url.path,
                        "process_time": round(process_time, 4),
                        "status_code": response.status_code,
                    },
                )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Calculate processing time for error cases
            process_time = time.time() - start_time

            # Log error with full details
            self.logger.error(
                "Request failed with exception",
                extra={
                    "request_id": request_id,
                    "event": "request_error",
                    "method": request.method,
                    "url": str(request.url),
                    "path": request.url.path,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "process_time": round(process_time, 4),
                    "traceback": traceback.format_exc(),
                    "timestamp": time.time(),
                },
            )

            # Re-raise the exception
            raise

    async def _capture_request_data(self, request: Request) -> Dict[str, Any]:
        """
        Capture request data for logging.

        Args:
            request: FastAPI request object

        Returns:
            Dictionary with request data
        """
        data = {
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "query_params": dict(request.query_params),
        }

        # Capture request body for POST/PUT/PATCH requests
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    # Try to parse as JSON
                    try:
                        json_body = json.loads(body.decode("utf-8"))
                        data["body"] = self._filter_sensitive_data(json_body)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        # If not JSON, store as string (truncated if too long)
                        body_str = body.decode("utf-8", errors="ignore")
                        if len(body_str) > 1000:
                            body_str = body_str[:1000] + "... (truncated)"
                        data["body"] = body_str
            except Exception as e:
                data["body_error"] = str(e)

        return data

    async def _capture_response_data(self, response: Response) -> Dict[str, Any]:
        """
        Capture response data for logging.

        Args:
            response: FastAPI response object

        Returns:
            Dictionary with response data
        """
        data = {"status_code": response.status_code, "headers": dict(response.headers)}

        # Capture response body for non-streaming responses
        if not isinstance(response, StreamingResponse):
            try:
                if hasattr(response, "body"):
                    body = response.body
                    if body and len(body) <= self.max_response_size:
                        try:
                            # Try to parse as JSON
                            json_body = json.loads(body.decode("utf-8"))
                            data["body"] = self._filter_sensitive_data(json_body)
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            # If not JSON, store as string
                            data["body"] = body.decode("utf-8", errors="ignore")
                    elif body:
                        data["body_size"] = len(body)
                        data["body"] = "(response too large to log)"
            except Exception as e:
                data["body_error"] = str(e)

        return data

    def _filter_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """
        Filter sensitive headers from logging.

        Args:
            headers: Request/response headers

        Returns:
            Filtered headers dictionary
        """
        filtered = {}
        for key, value in headers.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in self.sensitive_fields):
                filtered[key] = "[FILTERED]"
            else:
                filtered[key] = value
        return filtered

    def _filter_sensitive_data(self, data: Any) -> Any:
        """
        Recursively filter sensitive data from request/response bodies.

        Args:
            data: Data to filter

        Returns:
            Filtered data
        """
        if isinstance(data, dict):
            filtered = {}
            for key, value in data.items():
                key_lower = key.lower()
                if any(sensitive in key_lower for sensitive in self.sensitive_fields):
                    filtered[key] = "[FILTERED]"
                else:
                    filtered[key] = self._filter_sensitive_data(value)
            return filtered
        elif isinstance(data, list):
            return [self._filter_sensitive_data(item) for item in data]
        else:
            return data

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded IP (behind proxy/load balancer)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        # Check for real IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fall back to direct client IP
        return request.client.host if request.client else "unknown"


def setup_logging():
    """
    Setup structured logging configuration.
    """
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO if not settings.debug else logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            # Add file handler if needed
            # logging.FileHandler('api.log')
        ],
    )

    # Configure API request logger
    api_logger = logging.getLogger("api.requests")
    api_logger.setLevel(logging.INFO)

    # Configure JSON formatter for structured logging
    # In production, you might want to use a JSON formatter
    # formatter = logging.Formatter(
    #     '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s", "extra": %(extra)s}'
    # )

    return api_logger


# Initialize logging on module import
setup_logging()
