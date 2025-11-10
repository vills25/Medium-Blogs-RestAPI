import time
from loguru import logger

class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        
        logger.bind(API_REQUEST=True).info(f"🌐 {request.method} {request.path} - RequestLoggingMiddleware Incoming request")

        response = self.get_response(request)
        duration = time.time() - start_time
        
        username = getattr(request.user, 'username', 'Anonymous')

        # Log response with username
        logger.bind(API_REQUEST=True).info(f"📡 {request.method} {request.path} - User: {username} - "f"Status: {response.status_code} - Duration: {duration:.2f}s")
        logger.bind(API_REQUEST=True).info("")

        return response