"""
Security middleware for API protection.

This module implements:
- Security headers (HSTS, CSP, X-Frame-Options, etc.)
- Enhanced CORS protection
- Request security validation
- IP filtering and blocking
"""

import re
from typing import Set, List, Optional
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
import logging

from ..core.config import settings

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive security middleware for API protection.
    
    Features:
    - Security headers (HSTS, CSP, X-Frame-Options, etc.)
    - Enhanced CORS protection
    - Request validation and sanitization
    - Basic IP filtering
    - Security event logging
    """
    
    def __init__(self, app):
        super().__init__(app)
        
        # Security headers to add to all responses
        self.security_headers = {
            # Strict Transport Security (HTTPS only)
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            
            # Content Security Policy
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self'; "
                "frame-ancestors 'none'"
            ),
            
            # Prevent clickjacking
            "X-Frame-Options": "DENY",
            
            # MIME type sniffing protection
            "X-Content-Type-Options": "nosniff",
            
            # XSS protection
            "X-XSS-Protection": "1; mode=block",
            
            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Permissions policy
            "Permissions-Policy": (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=(), "
                "accelerometer=(), "
                "gyroscope=(), "
                "magnetometer=()"
            ),
            
            # Server information hiding
            "Server": "TextRPG-API",
            
            # Cache control for sensitive endpoints
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
        
        # Allowed origins for CORS (more restrictive than FastAPI CORS)
        self.allowed_origins = {
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "https://localhost:3000"
        }
        
        # Add production origins if configured
        if hasattr(settings, 'allowed_origins'):
            self.allowed_origins.update(settings.allowed_origins)
        
        # Blocked IP addresses (can be loaded from database/config)
        self.blocked_ips: Set[str] = set()
        
        # Suspicious patterns in URLs/headers
        self.suspicious_patterns = [
            re.compile(r'<script[^>]*>', re.IGNORECASE),
            re.compile(r'javascript:', re.IGNORECASE),
            re.compile(r'vbscript:', re.IGNORECASE),
            re.compile(r'onload\s*=', re.IGNORECASE),
            re.compile(r'onerror\s*=', re.IGNORECASE),
            re.compile(r'eval\s*\(', re.IGNORECASE),
            re.compile(r'union\s+select', re.IGNORECASE),
            re.compile(r'drop\s+table', re.IGNORECASE),
            re.compile(r'insert\s+into', re.IGNORECASE),
            re.compile(r'delete\s+from', re.IGNORECASE),
        ]
        
        # Rate limit for security events (prevent log flooding)
        self.security_event_cache: Set[str] = set()
    
    async def dispatch(self, request: Request, call_next):
        """Process request with security checks."""
        
        # 1. IP filtering
        client_ip = self._get_client_ip(request)
        if client_ip in self.blocked_ips:
            logger.warning(f"Blocked IP attempted access: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # 2. Request validation
        security_violations = await self._validate_request_security(request)
        if security_violations:
            self._log_security_event(request, "suspicious_request", security_violations)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid request"
            )
        
        # 3. Enhanced CORS validation for preflight requests
        if request.method == "OPTIONS":
            return await self._handle_preflight(request)
        
        # 4. Process request
        response = await call_next(request)
        
        # 5. Add security headers
        self._add_security_headers(response)
        
        # 6. Enhanced CORS headers
        self._add_cors_headers(request, response)
        
        return response
    
    async def _validate_request_security(self, request: Request) -> List[str]:
        """
        Validate request for security issues.
        
        Returns:
            List of security violations found
        """
        violations = []
        
        # Check URL for suspicious patterns
        url_str = str(request.url)
        for pattern in self.suspicious_patterns:
            if pattern.search(url_str):
                violations.append(f"suspicious_url_pattern: {pattern.pattern}")
        
        # Check headers for suspicious content
        for header_name, header_value in request.headers.items():
            if isinstance(header_value, str):
                for pattern in self.suspicious_patterns:
                    if pattern.search(header_value):
                        violations.append(f"suspicious_header: {header_name}")
        
        # Check for oversized headers
        for header_name, header_value in request.headers.items():
            if len(header_value) > 8192:  # 8KB limit per header
                violations.append(f"oversized_header: {header_name}")
        
        # Check User-Agent (basic bot detection)
        user_agent = request.headers.get("user-agent", "").lower()
        suspicious_agents = ['bot', 'crawler', 'spider', 'scraper']
        if any(agent in user_agent for agent in suspicious_agents):
            # Log but don't block (might be legitimate)
            self._log_security_event(request, "bot_detected", [f"user_agent: {user_agent}"])
        
        # Check for missing required headers in POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type")
            if not content_type:
                violations.append("missing_content_type")
        
        return violations
    
    async def _handle_preflight(self, request: Request) -> StarletteResponse:
        """
        Handle CORS preflight requests with enhanced validation.
        """
        origin = request.headers.get("origin")
        
        # Validate origin
        if origin not in self.allowed_origins:
            logger.warning(f"CORS preflight from unauthorized origin: {origin}")
            return StarletteResponse(status_code=403)
        
        # Create preflight response
        response = StarletteResponse()
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = (
            "Content-Type, Authorization, X-Requested-With, Accept, Origin"
        )
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Max-Age"] = "86400"  # 24 hours
        
        # Add security headers
        self._add_security_headers(response)
        
        return response
    
    def _add_security_headers(self, response: Response):
        """Add security headers to response."""
        for header_name, header_value in self.security_headers.items():
            response.headers[header_name] = header_value
    
    def _add_cors_headers(self, request: Request, response: Response):
        """Add enhanced CORS headers to response."""
        origin = request.headers.get("origin")
        
        # Only add CORS headers for allowed origins
        if origin in self.allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Expose-Headers"] = (
                "X-Request-ID, X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset"
            )
        
        # Add Vary header for proper caching
        response.headers["Vary"] = "Origin, Accept-Encoding"
    
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
    
    def _log_security_event(
        self, 
        request: Request, 
        event_type: str, 
        details: List[str]
    ):
        """
        Log security events with rate limiting to prevent log flooding.
        """
        client_ip = self._get_client_ip(request)
        event_key = f"{event_type}:{client_ip}"
        
        # Simple rate limiting for security events
        if event_key not in self.security_event_cache:
            self.security_event_cache.add(event_key)
            
            logger.warning(
                f"Security event: {event_type}",
                extra={
                    "event_type": event_type,
                    "client_ip": client_ip,
                    "user_agent": request.headers.get("user-agent"),
                    "url": str(request.url),
                    "method": request.method,
                    "details": details
                }
            )
            
            # Clear cache periodically (simple implementation)
            if len(self.security_event_cache) > 1000:
                self.security_event_cache.clear()
    
    def add_blocked_ip(self, ip_address: str):
        """Add IP address to blocked list."""
        self.blocked_ips.add(ip_address)
        logger.info(f"Added IP to blocklist: {ip_address}")
    
    def remove_blocked_ip(self, ip_address: str):
        """Remove IP address from blocked list."""
        self.blocked_ips.discard(ip_address)
        logger.info(f"Removed IP from blocklist: {ip_address}")
    
    def get_blocked_ips(self) -> Set[str]:
        """Get current blocked IP list."""
        return self.blocked_ips.copy()


# Global security middleware instance
security_middleware = None


def get_security_middleware() -> SecurityMiddleware:
    """Get global security middleware instance."""
    global security_middleware
    return security_middleware


def init_security_middleware(app) -> SecurityMiddleware:
    """Initialize and return security middleware."""
    global security_middleware
    security_middleware = SecurityMiddleware(app)
    return security_middleware 