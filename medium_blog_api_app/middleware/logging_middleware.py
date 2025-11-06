import time
from loguru import logger

class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        
        # Log request
        logger.bind(API_REQUEST=True).info(
            f"🌐 {request.method} {request.path} - User: {getattr(request.user, 'username', 'Anonymous')}"
        )

        response = self.get_response(request)

        duration = time.time() - start_time
        
        # Log response
        logger.bind(API_REQUEST=True).info(
            f"📡 {request.method} {request.path} - Status: {response.status_code} - Duration: {duration:.2f}s"
        )

        return response