"""
WebSocket Health Monitoring

Implements heartbeat mechanisms, connection cleanup, and health monitoring
for WebSocket connections.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Set

from app.websocket.manager import connection_manager

logger = logging.getLogger(__name__)


class WebSocketHealthMonitor:
    """Monitors WebSocket connection health and performs cleanup."""
    
    def __init__(self):
        self.heartbeat_interval = 30  # seconds
        self.cleanup_interval = 60   # seconds
        self.connection_timeout = 120  # seconds
        self.running = False
        self.tasks: Set[asyncio.Task] = set()
    
    async def start(self):
        """Start the health monitoring tasks."""
        if self.running:
            logger.warning("WebSocket health monitor already running")
            return
        
        self.running = True
        logger.info("Starting WebSocket health monitor")
        
        # Initialize Redis connection for WebSocket manager
        await connection_manager.initialize_redis()
        
        # Start monitoring tasks
        heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        cleanup_task = asyncio.create_task(self._cleanup_loop())
        redis_listener_task = asyncio.create_task(self._redis_listener_loop())
        
        self.tasks.update([heartbeat_task, cleanup_task, redis_listener_task])
        
        logger.info("WebSocket health monitor started")
    
    async def stop(self):
        """Stop the health monitoring tasks."""
        if not self.running:
            return
        
        self.running = False
        logger.info("Stopping WebSocket health monitor")
        
        # Cancel all tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        self.tasks.clear()
        logger.info("WebSocket health monitor stopped")
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeats to all connections."""
        while self.running:
            try:
                await self._send_heartbeats()
                await asyncio.sleep(self.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(self.heartbeat_interval)
    
    async def _cleanup_loop(self):
        """Periodic cleanup of inactive connections."""
        while self.running:
            try:
                await self._cleanup_connections()
                await asyncio.sleep(self.cleanup_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(self.cleanup_interval)
    
    async def _redis_listener_loop(self):
        """Listen to Redis pub/sub messages."""
        while self.running:
            try:
                await connection_manager.listen_to_redis()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in Redis listener loop: {e}")
                await asyncio.sleep(5)  # Short delay before retrying
    
    async def _send_heartbeats(self):
        """Send heartbeat to all active connections."""
        connection_ids = list(connection_manager.active_connections.keys())
        
        if not connection_ids:
            return
        
        logger.debug(f"Sending heartbeats to {len(connection_ids)} connections")
        
        for connection_id in connection_ids:
            try:
                await connection_manager.send_heartbeat(connection_id)
            except Exception as e:
                logger.warning(f"Failed to send heartbeat to {connection_id}: {e}")
    
    async def _cleanup_connections(self):
        """Clean up inactive and dead connections."""
        try:
            await connection_manager.cleanup_inactive_connections()
            
            # Log current statistics
            stats = connection_manager.get_connection_stats()
            logger.info(f"WebSocket stats: {stats}")
            
        except Exception as e:
            logger.error(f"Error during connection cleanup: {e}")
    
    def get_health_status(self) -> Dict:
        """Get current health status of WebSocket system."""
        stats = connection_manager.get_connection_stats()
        
        return {
            "status": "healthy" if self.running else "stopped",
            "monitor_running": self.running,
            "active_tasks": len([t for t in self.tasks if not t.done()]),
            "connections": stats,
            "heartbeat_interval": self.heartbeat_interval,
            "cleanup_interval": self.cleanup_interval,
            "connection_timeout": self.connection_timeout
        }


class WebSocketMetrics:
    """Collect and manage WebSocket metrics."""
    
    def __init__(self):
        self.connection_count_history = []
        self.message_count = 0
        self.error_count = 0
        self.start_time = datetime.utcnow()
    
    def record_connection(self, connected: bool):
        """Record connection/disconnection event."""
        current_time = datetime.utcnow()
        current_count = len(connection_manager.active_connections)
        
        self.connection_count_history.append({
            "timestamp": current_time.isoformat(),
            "count": current_count,
            "event": "connect" if connected else "disconnect"
        })
        
        # Keep only last 1000 entries
        if len(self.connection_count_history) > 1000:
            self.connection_count_history = self.connection_count_history[-1000:]
    
    def record_message(self):
        """Record message sent/received."""
        self.message_count += 1
    
    def record_error(self):
        """Record error occurrence."""
        self.error_count += 1
    
    def get_metrics(self) -> Dict:
        """Get current metrics."""
        uptime = datetime.utcnow() - self.start_time
        current_stats = connection_manager.get_connection_stats()
        
        return {
            "uptime_seconds": uptime.total_seconds(),
            "total_messages": self.message_count,
            "total_errors": self.error_count,
            "current_connections": current_stats,
            "connection_history_size": len(self.connection_count_history),
            "messages_per_minute": self._calculate_rate(self.message_count, uptime),
            "errors_per_minute": self._calculate_rate(self.error_count, uptime)
        }
    
    def _calculate_rate(self, count: int, uptime: timedelta) -> float:
        """Calculate rate per minute."""
        if uptime.total_seconds() == 0:
            return 0.0
        return (count / uptime.total_seconds()) * 60


# Global instances
health_monitor = WebSocketHealthMonitor()
metrics = WebSocketMetrics()


async def initialize_websocket_health():
    """Initialize WebSocket health monitoring."""
    await health_monitor.start()


async def shutdown_websocket_health():
    """Shutdown WebSocket health monitoring."""
    await health_monitor.stop()


def get_websocket_health() -> Dict:
    """Get WebSocket health status."""
    return health_monitor.get_health_status()


def get_websocket_metrics() -> Dict:
    """Get WebSocket metrics."""
    return metrics.get_metrics()