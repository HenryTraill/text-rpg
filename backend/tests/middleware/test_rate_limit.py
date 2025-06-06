"""
Tests for rate limiting middleware.

Tests rate limiting functionality including:
- Redis-backed sliding window algorithm
- Per-user and per-IP rate limiting
- Rate limit headers
- Authentication-based limits
"""

import pytest
import time
from unittest.mock import Mock, patch
from fastapi import Request, HTTPException
from starlette.responses import Response

from app.middleware.rate_limit import RateLimitMiddleware
from app.core.config import settings


class TestRateLimitMiddleware:
    """Test suite for RateLimitMiddleware."""

    @pytest.fixture
    def mock_redis_client(self):
        """Create a mock Redis client."""
        mock_client = Mock()
        mock_client.pipeline.return_value = Mock()
        return mock_client

    @pytest.fixture
    def mock_app(self):
        """Create a mock FastAPI app."""

        async def app(scope, receive, send):
            response = Response("OK", status_code=200)
            await response(scope, receive, send)

        return app

    @pytest.fixture
    def rate_limiter(self, mock_app, mock_redis_client):
        """Create rate limiter with mocked dependencies."""
        with patch("redis.from_url", return_value=mock_redis_client):
            middleware = RateLimitMiddleware(mock_app)
            middleware.redis_client = mock_redis_client
            return middleware

    @pytest.fixture
    def mock_request(self):
        """Create a mock request."""
        request = Mock(spec=Request)
        request.url.path = "/api/v1/test"
        request.method = "GET"
        request.client.host = "127.0.0.1"
        request.headers = {}
        return request

    @pytest.mark.asyncio
    async def test_excluded_paths_no_rate_limit(self, rate_limiter, mock_request):
        """Test that excluded paths bypass rate limiting."""
        mock_request.url.path = "/health"

        async def call_next(request):
            return Response("OK", status_code=200)

        response = await rate_limiter.dispatch(mock_request, call_next)

        assert response.status_code == 200
        # Redis should not be called for excluded paths
        rate_limiter.redis_client.pipeline.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_client_info_authenticated_user(self, rate_limiter, mock_request):
        """Test client info extraction for authenticated user."""
        # Mock JWT token extraction
        with patch.object(
            rate_limiter, "_extract_user_id_from_token", return_value="user123"
        ):
            client_id, rate_limit = await rate_limiter._get_client_info(mock_request)

        assert client_id == "user:user123"
        assert rate_limit == rate_limiter.authenticated_user_limit

    @pytest.mark.asyncio
    async def test_get_client_info_anonymous_user(self, rate_limiter, mock_request):
        """Test client info extraction for anonymous user."""
        # Mock no authentication
        with patch.object(
            rate_limiter, "_extract_user_id_from_token", return_value=None
        ):
            client_id, rate_limit = await rate_limiter._get_client_info(mock_request)

        assert client_id == "ip:127.0.0.1"
        assert rate_limit == rate_limiter.anonymous_ip_limit

    @pytest.mark.asyncio
    async def test_extract_user_id_from_token_valid(self, rate_limiter, mock_request):
        """Test user ID extraction from valid JWT token."""
        mock_request.headers = {"Authorization": "Bearer valid_token"}

        with patch("app.core.auth.auth_utils") as mock_auth:
            mock_auth.verify_token.return_value = {"sub": "user123"}

            user_id = await rate_limiter._extract_user_id_from_token(mock_request)

        assert user_id == "user123"

    @pytest.mark.asyncio
    async def test_extract_user_id_from_token_invalid(self, rate_limiter, mock_request):
        """Test user ID extraction from invalid JWT token."""
        mock_request.headers = {"Authorization": "Bearer invalid_token"}

        with patch("app.core.auth.auth_utils") as mock_auth:
            mock_auth.verify_token.side_effect = Exception("Invalid token")

            user_id = await rate_limiter._extract_user_id_from_token(mock_request)

        assert user_id is None

    @pytest.mark.asyncio
    async def test_extract_user_id_no_auth_header(self, rate_limiter, mock_request):
        """Test user ID extraction when no auth header present."""
        mock_request.headers = {}

        user_id = await rate_limiter._extract_user_id_from_token(mock_request)

        assert user_id is None

    def test_get_client_ip_forwarded(self, rate_limiter, mock_request):
        """Test client IP extraction with X-Forwarded-For header."""
        mock_request.headers = {"X-Forwarded-For": "192.168.1.1, 10.0.0.1"}

        ip = rate_limiter._get_client_ip(mock_request)

        assert ip == "192.168.1.1"

    def test_get_client_ip_real_ip(self, rate_limiter, mock_request):
        """Test client IP extraction with X-Real-IP header."""
        mock_request.headers = {"X-Real-IP": "192.168.1.2"}

        ip = rate_limiter._get_client_ip(mock_request)

        assert ip == "192.168.1.2"

    def test_get_client_ip_direct(self, rate_limiter, mock_request):
        """Test client IP extraction from direct connection."""
        mock_request.headers = {}

        ip = rate_limiter._get_client_ip(mock_request)

        assert ip == "127.0.0.1"

    @pytest.mark.asyncio
    async def test_check_rate_limit_allowed(self, rate_limiter):
        """Test rate limit check when request is allowed."""
        client_id = "user:test123"
        rate_limit = 100
        current_time = int(time.time())

        # Mock Redis pipeline operations
        mock_pipeline = Mock()
        mock_pipeline.execute.return_value = [None, 5, None, None]  # 5 current requests
        rate_limiter.redis_client.pipeline.return_value = mock_pipeline

        allowed, remaining, reset_time = await rate_limiter._check_rate_limit(
            client_id, rate_limit
        )

        assert allowed is True
        assert remaining == 94  # 100 - 5 - 1
        assert reset_time > current_time

    @pytest.mark.asyncio
    async def test_check_rate_limit_exceeded(self, rate_limiter):
        """Test rate limit check when limit is exceeded."""
        client_id = "user:test123"
        rate_limit = 100

        # Mock Redis pipeline operations - limit exceeded
        mock_pipeline = Mock()
        mock_pipeline.execute.return_value = [
            None,
            100,
            None,
            None,
        ]  # 100 current requests
        rate_limiter.redis_client.pipeline.return_value = mock_pipeline
        rate_limiter.redis_client.zrem = Mock()

        allowed, remaining, reset_time = await rate_limiter._check_rate_limit(
            client_id, rate_limit
        )

        assert allowed is False
        assert remaining == 0
        # Should remove the request since it's not allowed
        rate_limiter.redis_client.zrem.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_rate_limit_redis_error(self, rate_limiter):
        """Test rate limit check when Redis error occurs."""
        client_id = "user:test123"
        rate_limit = 100

        # Mock Redis pipeline to raise exception
        rate_limiter.redis_client.pipeline.side_effect = Exception("Redis error")

        allowed, remaining, reset_time = await rate_limiter._check_rate_limit(
            client_id, rate_limit
        )

        # Should allow request on Redis error
        assert allowed is True
        assert remaining == rate_limit - 1

    @pytest.mark.asyncio
    async def test_dispatch_request_allowed(self, rate_limiter, mock_request):
        """Test successful request processing when rate limit not exceeded."""

        async def call_next(request):
            return Response("OK", status_code=200)

        # Mock rate limit check to allow request
        with (
            patch.object(
                rate_limiter, "_get_client_info", return_value=("user:test", 100)
            ),
            patch.object(
                rate_limiter,
                "_check_rate_limit",
                return_value=(True, 99, int(time.time()) + 60),
            ),
        ):
            response = await rate_limiter.dispatch(mock_request, call_next)

        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
        assert response.headers["X-RateLimit-Limit"] == "100"
        assert response.headers["X-RateLimit-Remaining"] == "99"

    @pytest.mark.asyncio
    async def test_dispatch_rate_limit_exceeded(self, rate_limiter, mock_request):
        """Test request processing when rate limit is exceeded."""
        # Mock rate limit check to deny request
        reset_time = int(time.time()) + 60
        with (
            patch.object(
                rate_limiter, "_get_client_info", return_value=("user:test", 100)
            ),
            patch.object(
                rate_limiter, "_check_rate_limit", return_value=(False, 0, reset_time)
            ),
        ):
            with pytest.raises(HTTPException) as exc_info:

                async def call_next(request):
                    return Response("OK", status_code=200)

                await rate_limiter.dispatch(mock_request, call_next)

        assert exc_info.value.status_code == 429
        assert "Rate limit exceeded" in exc_info.value.detail
        assert "X-RateLimit-Limit" in exc_info.value.headers
        assert "X-RateLimit-Remaining" in exc_info.value.headers
        assert "X-RateLimit-Reset" in exc_info.value.headers
        assert "Retry-After" in exc_info.value.headers

    @pytest.mark.asyncio
    async def test_get_rate_limit_info(self, rate_limiter):
        """Test getting rate limit information for a client."""
        client_id = "user:test123"
        rate_limit = 100
        current_time = int(time.time())

        # Mock Redis operations
        rate_limiter.redis_client.zcount.return_value = 25  # 25 current requests

        info = await rate_limiter.get_rate_limit_info(client_id, rate_limit)

        assert info["limit"] == 100
        assert info["remaining"] == 75  # 100 - 25
        assert info["current_requests"] == 25
        assert info["reset"] > current_time

    @pytest.mark.asyncio
    async def test_get_rate_limit_info_redis_error(self, rate_limiter):
        """Test getting rate limit info when Redis error occurs."""
        client_id = "user:test123"
        rate_limit = 100

        # Mock Redis to raise exception
        rate_limiter.redis_client.zcount.side_effect = Exception("Redis error")

        info = await rate_limiter.get_rate_limit_info(client_id, rate_limit)

        # Should return safe defaults on error
        assert info["limit"] == 100
        assert info["remaining"] == 100
        assert info["current_requests"] == 0

    @pytest.mark.asyncio
    async def test_sliding_window_algorithm(self, rate_limiter):
        """Test the sliding window rate limiting algorithm."""
        client_id = "test:sliding_window"
        rate_limit = 5

        # Mock Redis operations for sliding window
        mock_pipeline = Mock()
        rate_limiter.redis_client.pipeline.return_value = mock_pipeline

        # Simulate multiple requests within the window
        results = []
        for i in range(7):  # Try 7 requests with limit of 5
            if i < 5:
                # First 5 requests should be allowed
                mock_pipeline.execute.return_value = [None, i, None, None]
                allowed, remaining, reset_time = await rate_limiter._check_rate_limit(
                    client_id, rate_limit
                )
                results.append((allowed, remaining))
            else:
                # Last 2 requests should be denied
                mock_pipeline.execute.return_value = [None, 5, None, None]
                rate_limiter.redis_client.zrem = Mock()
                allowed, remaining, reset_time = await rate_limiter._check_rate_limit(
                    client_id, rate_limit
                )
                results.append((allowed, remaining))

        # Verify first 5 requests were allowed
        for i in range(5):
            assert results[i][0] is True  # allowed

        # Verify last 2 requests were denied
        for i in range(5, 7):
            assert results[i][0] is False  # denied
            assert results[i][1] == 0  # no remaining requests


class TestRateLimitMiddlewareIntegration:
    """Integration tests for rate limiting middleware."""

    @pytest.mark.asyncio
    async def test_authenticated_vs_anonymous_limits(self):
        """Test different rate limits for authenticated vs anonymous users."""
        mock_app = Mock()

        with patch("redis.from_url") as mock_redis_factory:
            mock_redis_client = Mock()
            mock_redis_factory.return_value = mock_redis_client

            middleware = RateLimitMiddleware(mock_app)

            # Test authenticated user gets higher limit
            mock_request_auth = Mock()
            mock_request_auth.url.path = "/api/v1/test"
            mock_request_auth.headers = {"Authorization": "Bearer valid_token"}
            mock_request_auth.client.host = "127.0.0.1"

            with patch.object(
                middleware, "_extract_user_id_from_token", return_value="user123"
            ):
                client_id, rate_limit = await middleware._get_client_info(
                    mock_request_auth
                )

            assert client_id == "user:user123"
            assert rate_limit == settings.api_rate_limit  # 100 req/min

            # Test anonymous user gets lower limit
            mock_request_anon = Mock()
            mock_request_anon.url.path = "/api/v1/test"
            mock_request_anon.headers = {}
            mock_request_anon.client.host = "127.0.0.1"

            with patch.object(
                middleware, "_extract_user_id_from_token", return_value=None
            ):
                client_id, rate_limit = await middleware._get_client_info(
                    mock_request_anon
                )

            assert client_id == "ip:127.0.0.1"
            assert rate_limit == 20  # Anonymous limit

    @pytest.mark.asyncio
    async def test_rate_limit_headers_format(self):
        """Test that rate limit headers are properly formatted."""
        mock_app = Mock()

        async def call_next(request):
            response = Response("OK", status_code=200)
            return response

        with patch("redis.from_url") as mock_redis_factory:
            mock_redis_client = Mock()
            mock_redis_factory.return_value = mock_redis_client

            middleware = RateLimitMiddleware(mock_app)

            mock_request = Mock()
            mock_request.url.path = "/api/v1/test"
            mock_request.headers = {}
            mock_request.client.host = "127.0.0.1"

            current_time = int(time.time())
            reset_time = current_time + 60

            with (
                patch.object(
                    middleware, "_get_client_info", return_value=("ip:127.0.0.1", 20)
                ),
                patch.object(
                    middleware, "_check_rate_limit", return_value=(True, 19, reset_time)
                ),
            ):
                response = await middleware.dispatch(mock_request, call_next)

            # Verify all required headers are present and correctly formatted
            assert response.headers["X-RateLimit-Limit"] == "20"
            assert response.headers["X-RateLimit-Remaining"] == "19"
            assert response.headers["X-RateLimit-Reset"] == str(reset_time)

            # Headers should be strings
            assert isinstance(response.headers["X-RateLimit-Limit"], str)
            assert isinstance(response.headers["X-RateLimit-Remaining"], str)
            assert isinstance(response.headers["X-RateLimit-Reset"], str)
