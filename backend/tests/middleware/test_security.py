"""
Tests for security middleware.

Tests security functionality including:
- Security headers injection
- CORS protection and validation
- Request validation and sanitization
- IP filtering and blocking
- Security event logging
"""

import pytest
from unittest.mock import Mock, patch
from fastapi import Request, HTTPException
from starlette.responses import Response

from app.middleware.security import SecurityMiddleware


class TestSecurityMiddleware:
    """Test suite for SecurityMiddleware."""

    @pytest.fixture
    def mock_app(self):
        """Create a mock FastAPI app."""

        async def app(scope, receive, send):
            response = Response("OK", status_code=200)
            await response(scope, receive, send)

        return app

    @pytest.fixture
    def security_middleware(self, mock_app):
        """Create security middleware instance."""
        return SecurityMiddleware(mock_app)

    @pytest.fixture
    def mock_request(self):
        """Create a mock request."""
        request = Mock(spec=Request)
        request.url.path = "/api/v1/test"
        request.method = "GET"
        request.url = Mock()
        request.url.__str__ = Mock(return_value="http://localhost:8000/api/v1/test")
        request.client.host = "127.0.0.1"
        request.headers = {}
        return request

    def test_security_headers_added(self, security_middleware):
        """Test that security headers are properly added to responses."""
        response = Response("OK", status_code=200)

        security_middleware._add_security_headers(response)

        # Check all expected security headers
        assert (
            response.headers["Strict-Transport-Security"]
            == "max-age=31536000; includeSubDomains; preload"
        )
        assert "Content-Security-Policy" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert "Permissions-Policy" in response.headers
        assert response.headers["Server"] == "TextRPG-API"
        assert (
            response.headers["Cache-Control"] == "no-cache, no-store, must-revalidate"
        )

    def test_cors_headers_allowed_origin(self, security_middleware):
        """Test CORS headers are added for allowed origins."""
        request = Mock()
        request.headers = {"origin": "http://localhost:3000"}
        response = Response("OK", status_code=200)

        security_middleware._add_cors_headers(request, response)

        assert (
            response.headers["Access-Control-Allow-Origin"] == "http://localhost:3000"
        )
        assert response.headers["Access-Control-Allow-Credentials"] == "true"
        assert "Access-Control-Expose-Headers" in response.headers
        assert response.headers["Vary"] == "Origin, Accept-Encoding"

    def test_cors_headers_disallowed_origin(self, security_middleware):
        """Test CORS headers are not added for disallowed origins."""
        request = Mock()
        request.headers = {"origin": "http://malicious-site.com"}
        response = Response("OK", status_code=200)

        security_middleware._add_cors_headers(request, response)

        assert "Access-Control-Allow-Origin" not in response.headers
        assert response.headers["Vary"] == "Origin, Accept-Encoding"

    def test_get_client_ip_forwarded(self, security_middleware, mock_request):
        """Test client IP extraction with X-Forwarded-For header."""
        mock_request.headers = {"x-forwarded-for": "192.168.1.1, 10.0.0.1"}

        ip = security_middleware._get_client_ip(mock_request)

        assert ip == "192.168.1.1"

    def test_get_client_ip_real_ip(self, security_middleware, mock_request):
        """Test client IP extraction with X-Real-IP header."""
        mock_request.headers = {"x-real-ip": "192.168.1.2"}

        ip = security_middleware._get_client_ip(mock_request)

        assert ip == "192.168.1.2"

    def test_get_client_ip_direct(self, security_middleware, mock_request):
        """Test client IP extraction from direct connection."""
        mock_request.headers = {}

        ip = security_middleware._get_client_ip(mock_request)

        assert ip == "127.0.0.1"

    @pytest.mark.asyncio
    async def test_validate_request_security_clean(
        self, security_middleware, mock_request
    ):
        """Test request security validation with clean request."""
        mock_request.headers = {"user-agent": "Mozilla/5.0 Chrome"}

        violations = await security_middleware._validate_request_security(mock_request)

        assert violations == []

    @pytest.mark.asyncio
    async def test_validate_request_security_suspicious_url(
        self, security_middleware, mock_request
    ):
        """Test request security validation with suspicious URL patterns."""
        mock_request.url.__str__ = Mock(
            return_value="http://localhost:8000/api/v1/test?q=<script>alert('xss')</script>"
        )

        violations = await security_middleware._validate_request_security(mock_request)

        assert len(violations) > 0
        assert any("suspicious_url_pattern" in v for v in violations)

    @pytest.mark.asyncio
    async def test_validate_request_security_suspicious_header(
        self, security_middleware, mock_request
    ):
        """Test request security validation with suspicious headers."""
        mock_request.headers = {"x-custom-header": "javascript:alert('xss')"}

        violations = await security_middleware._validate_request_security(mock_request)

        assert len(violations) > 0
        assert any("suspicious_header" in v for v in violations)

    @pytest.mark.asyncio
    async def test_validate_request_security_oversized_header(
        self, security_middleware, mock_request
    ):
        """Test request security validation with oversized headers."""
        large_header = "x" * 10000  # 10KB header
        mock_request.headers = {"x-large-header": large_header}

        violations = await security_middleware._validate_request_security(mock_request)

        assert len(violations) > 0
        assert any("oversized_header" in v for v in violations)

    @pytest.mark.asyncio
    async def test_validate_request_security_bot_detection(
        self, security_middleware, mock_request
    ):
        """Test bot detection in user agent."""
        mock_request.headers = {"user-agent": "Googlebot/2.1"}

        with patch.object(security_middleware, "_log_security_event") as mock_log:
            violations = await security_middleware._validate_request_security(
                mock_request
            )

        # Bot detection should log but not violate
        assert violations == []
        mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_request_security_missing_content_type(
        self, security_middleware, mock_request
    ):
        """Test validation fails for POST request without content type."""
        mock_request.method = "POST"
        mock_request.headers = {}

        violations = await security_middleware._validate_request_security(mock_request)

        assert len(violations) > 0
        assert any("missing_content_type" in v for v in violations)

    @pytest.mark.asyncio
    async def test_handle_preflight_allowed_origin(
        self, security_middleware, mock_request
    ):
        """Test CORS preflight handling for allowed origin."""
        mock_request.headers = {"origin": "http://localhost:3000"}

        response = await security_middleware._handle_preflight(mock_request)

        assert response.status_code == 200
        assert (
            response.headers["Access-Control-Allow-Origin"] == "http://localhost:3000"
        )
        assert "Access-Control-Allow-Methods" in response.headers
        assert "Access-Control-Allow-Headers" in response.headers
        assert response.headers["Access-Control-Allow-Credentials"] == "true"
        assert response.headers["Access-Control-Max-Age"] == "86400"

    @pytest.mark.asyncio
    async def test_handle_preflight_disallowed_origin(
        self, security_middleware, mock_request
    ):
        """Test CORS preflight handling for disallowed origin."""
        mock_request.headers = {"origin": "http://malicious-site.com"}

        with patch("app.middleware.security.logger") as mock_logger:
            response = await security_middleware._handle_preflight(mock_request)

        assert response.status_code == 403
        mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatch_blocked_ip(self, security_middleware, mock_request):
        """Test request handling for blocked IP address."""
        # Add IP to blocked list
        security_middleware.add_blocked_ip("127.0.0.1")

        async def call_next(request):
            return Response("OK", status_code=200)

        with pytest.raises(HTTPException) as exc_info:
            await security_middleware.dispatch(mock_request, call_next)

        assert exc_info.value.status_code == 403
        assert "Access denied" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_dispatch_security_violations(
        self, security_middleware, mock_request
    ):
        """Test request handling with security violations."""
        # Mock security validation to return violations
        with patch.object(
            security_middleware,
            "_validate_request_security",
            return_value=["test_violation"],
        ):

            async def call_next(request):
                return Response("OK", status_code=200)

            with pytest.raises(HTTPException) as exc_info:
                await security_middleware.dispatch(mock_request, call_next)

        assert exc_info.value.status_code == 400
        assert "Invalid request" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_dispatch_preflight_request(self, security_middleware, mock_request):
        """Test handling of OPTIONS preflight request."""
        mock_request.method = "OPTIONS"
        mock_request.headers = {"origin": "http://localhost:3000"}

        async def call_next(request):
            return Response("OK", status_code=200)

        response = await security_middleware.dispatch(mock_request, call_next)

        # Should handle preflight without calling next
        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" in response.headers

    @pytest.mark.asyncio
    async def test_dispatch_successful_request(self, security_middleware, mock_request):
        """Test successful request processing."""

        async def call_next(request):
            return Response("OK", status_code=200)

        response = await security_middleware.dispatch(mock_request, call_next)

        assert response.status_code == 200
        # Should have security headers
        assert "Strict-Transport-Security" in response.headers
        assert "X-Frame-Options" in response.headers
        # Should have CORS headers if origin is allowed
        assert "Vary" in response.headers

    def test_add_blocked_ip(self, security_middleware):
        """Test adding IP to blocked list."""
        ip = "192.168.1.100"

        security_middleware.add_blocked_ip(ip)

        assert ip in security_middleware.blocked_ips

    def test_remove_blocked_ip(self, security_middleware):
        """Test removing IP from blocked list."""
        ip = "192.168.1.100"
        security_middleware.add_blocked_ip(ip)

        security_middleware.remove_blocked_ip(ip)

        assert ip not in security_middleware.blocked_ips

    def test_get_blocked_ips(self, security_middleware):
        """Test getting blocked IP list."""
        ips = ["192.168.1.100", "10.0.0.5"]

        for ip in ips:
            security_middleware.add_blocked_ip(ip)

        blocked_ips = security_middleware.get_blocked_ips()

        assert blocked_ips == set(ips)
        # Should return a copy, not the original set
        assert blocked_ips is not security_middleware.blocked_ips

    def test_log_security_event(self, security_middleware, mock_request):
        """Test security event logging."""
        event_type = "test_event"
        details = ["detail1", "detail2"]

        with patch("app.middleware.security.logger") as mock_logger:
            security_middleware._log_security_event(mock_request, event_type, details)

        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        assert event_type in call_args[0][0]

    def test_log_security_event_rate_limiting(self, security_middleware, mock_request):
        """Test security event logging with rate limiting."""
        event_type = "test_event"
        details = ["detail1"]

        with patch("app.middleware.security.logger") as mock_logger:
            # First call should log
            security_middleware._log_security_event(mock_request, event_type, details)
            # Second call with same event should not log due to rate limiting
            security_middleware._log_security_event(mock_request, event_type, details)

        # Should only be called once due to rate limiting
        assert mock_logger.warning.call_count == 1

    def test_suspicious_patterns_detection(self, security_middleware):
        """Test that suspicious patterns are properly compiled and work."""
        patterns = security_middleware.suspicious_patterns

        # Test script tag detection
        assert any(
            pattern.search("<script>alert('xss')</script>") for pattern in patterns
        )

        # Test javascript: URL detection
        assert any(pattern.search("javascript:alert('xss')") for pattern in patterns)

        # Test SQL injection patterns
        assert any(pattern.search("UNION SELECT * FROM users") for pattern in patterns)
        assert any(pattern.search("DROP TABLE users") for pattern in patterns)

        # Test clean content doesn't match
        assert not any(pattern.search("normal content here") for pattern in patterns)


class TestSecurityMiddlewareIntegration:
    """Integration tests for security middleware."""

    @pytest.mark.asyncio
    async def test_full_request_processing_flow(self):
        """Test complete request processing flow with all security checks."""
        mock_app = Mock()
        middleware = SecurityMiddleware(mock_app)

        # Create a request that should pass all security checks
        request = Mock()
        request.url.path = "/api/v1/test"
        request.method = "GET"
        request.url.__str__ = Mock(return_value="http://localhost:8000/api/v1/test")
        request.client.host = "127.0.0.1"
        request.headers = {
            "user-agent": "Mozilla/5.0 Chrome",
            "origin": "http://localhost:3000",
        }

        async def call_next(req):
            return Response("Success", status_code=200)

        response = await middleware.dispatch(request, call_next)

        # Should succeed and have all security headers
        assert response.status_code == 200
        assert "Strict-Transport-Security" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "Access-Control-Allow-Origin" in response.headers
        assert (
            response.headers["Access-Control-Allow-Origin"] == "http://localhost:3000"
        )

    @pytest.mark.asyncio
    async def test_security_headers_comprehensive(self):
        """Test that all required security headers are present."""
        mock_app = Mock()
        middleware = SecurityMiddleware(mock_app)

        request = Mock()
        request.url.path = "/api/v1/test"
        request.method = "GET"
        request.url.__str__ = Mock(return_value="http://localhost:8000/api/v1/test")
        request.client.host = "127.0.0.1"
        request.headers = {}

        async def call_next(req):
            return Response("Success", status_code=200)

        response = await middleware.dispatch(request, call_next)

        # Verify all critical security headers are present
        required_headers = [
            "Strict-Transport-Security",
            "Content-Security-Policy",
            "X-Frame-Options",
            "X-Content-Type-Options",
            "X-XSS-Protection",
            "Referrer-Policy",
            "Permissions-Policy",
            "Cache-Control",
        ]

        for header in required_headers:
            assert header in response.headers, f"Missing security header: {header}"

    @pytest.mark.asyncio
    async def test_malicious_request_blocking(self):
        """Test that malicious requests are properly blocked."""
        mock_app = Mock()
        middleware = SecurityMiddleware(mock_app)

        # Create a request with XSS attempt
        request = Mock()
        request.url.path = "/api/v1/test"
        request.method = "GET"
        request.url.__str__ = Mock(
            return_value="http://localhost:8000/api/v1/test?q=<script>alert('xss')</script>"
        )
        request.client.host = "127.0.0.1"
        request.headers = {}

        async def call_next(req):
            return Response("Success", status_code=200)

        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(request, call_next)

        assert exc_info.value.status_code == 400
        assert "Invalid request" in exc_info.value.detail
