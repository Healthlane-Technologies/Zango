from datetime import datetime

import pytz

from celery import current_app
from redis import from_url
from redis.exceptions import ConnectionError, RedisError, TimeoutError
from rest_framework.views import APIView

from django.conf import settings
from django.core.cache import CacheKeyWarning, caches
from django.db import connection

from zango.core.api import get_api_response


class HealthCheckAPIV1(APIView):
    AVAILABLE_SERVICES = ["redis", "cache", "celery", "celery_beat", "database"]

    def check_redis(self):
        try:
            with from_url(settings.REDIS_URL) as conn:
                conn.ping()
                return {"success": True, "message": "Redis connection is healthy"}
        except (ConnectionRefusedError, TimeoutError, ConnectionError):
            return {"success": False, "message": "Failed to connect to Redis"}
        except Exception as e:
            return {"success": False, "message": f"Unexpected Redis error: {str(e)}"}

    def check_celery_beat(self):
        try:
            from django_celery_beat.models import PeriodicTask

            hc = PeriodicTask.objects.filter(name="health_check_periodic_task").last()
            now = datetime.now(tz=pytz.utc)

            if not hc.last_run_at:
                return {
                    "success": False,
                    "message": "Periodic health check task not started, celery might be down or celery beat is just starting",
                }

            time_difference = (now - hc.last_run_at).total_seconds()
            if time_difference <= 60:  # Check if last run was within a minute
                return {
                    "success": True,
                    "message": "Celery beat is healthy and scheduling tasks",
                }

            return {"success": False, "message": "Celery beat might be down"}

        except Exception as e:
            return {
                "success": False,
                "message": "Error getting celery beat health check task",
            }

    def check_cache(self):
        cache = caches["default"]
        try:
            cache.set("health_check", "itworks")
            if cache.get("health_check") == "itworks":
                return {"success": True, "message": "Cache is working properly"}
            return {"success": False, "message": "Cache read/write verification failed"}
        except (CacheKeyWarning, ValueError, ConnectionError, RedisError) as e:
            return {"success": False, "message": f"Cache error: {str(e)}"}

    def check_celery(self):
        try:
            app = current_app
            inspector = app.control.inspect()
            active_workers = inspector.active()

            if not active_workers:
                return {"success": False, "message": "No active Celery workers found"}

            return {
                "success": True,
                "message": f"Celery is healthy with {len(active_workers)} active workers",
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Celery health check failed: {str(e)}",
            }

    def check_db(self):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return {"success": True, "message": "Database connection is healthy"}
        except Exception as e:
            return {
                "success": False,
                "message": f"Database connection failed: {str(e)}",
            }

    def get(self, request, *args, **kwargs):
        services = request.GET.get("services", "").strip()
        requested_services = (
            services.split(",") if services else self.AVAILABLE_SERVICES
        )

        invalid_services = set(filter(None, requested_services)) - set(
            self.AVAILABLE_SERVICES
        )
        if invalid_services:
            return get_api_response(
                success=False,
                response_content={
                    "error": f'Invalid services: {", ".join(invalid_services)}',
                    "available_services": self.AVAILABLE_SERVICES,
                },
                status=400,
            )

        service_checks = {
            "redis": self.check_redis,
            "cache": self.check_cache,
            "celery": self.check_celery,
            "celery_beat": self.check_celery_beat,
            "database": self.check_db,
        }

        health_checks = {
            service: service_checks[service]()
            for service in requested_services
            if service
        }

        is_healthy = all(
            check.get("success", False) for check in health_checks.values()
        )

        return get_api_response(
            success=True if is_healthy else False,
            response_content={
                "status": "healthy" if is_healthy else "unhealthy",
                "timestamp": datetime.now(tz=pytz.utc).isoformat(),
                "services": health_checks,
            },
            status=200 if is_healthy else 503,
        )
