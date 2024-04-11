import logging
from django.utils.deprecation import MiddlewareMixin


class RequestResponseLoggerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('django.request')

    def __call__(self, request):
        # Log the request data
        self.logger.info(f'Request path: {request.path}, Method: {request.method}')
        
        # Get the response
        response = self.get_response(request)

        # Log response data
        self.logger.info(f'Response status: {response.status_code}')

        return response
    

class FullRequestResponseLogger(MiddlewareMixin):
    def __init__(self, get_response=None):
        self.get_response = get_response
        self.logger = logging.getLogger('django.request')

    def process_request(self, request):
        # Extract the client's IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        # Log full request data along with IP
        request_body = request.body.decode('utf-8')[:1000]  # Limit log size, adjust as needed
        self.logger.info(f'IP: {ip} - Request Path: {request.path} Method: {request.method} Body: {request_body}')

    def process_response(self, request, response):
        # Log full response data
        response_content = response.content.decode('utf-8')[:1000]  # Limit log size, adjust as needed
        self.logger.info(f'Response Status: {response.status_code} Content: {response_content}')
        return response

