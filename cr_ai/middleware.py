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
    

import logging
from django.utils.deprecation import MiddlewareMixin

class FullRequestResponseLogger(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)  # Properly initialize the MiddlewareMixin
        self.logger = logging.getLogger('django.request')

    def __call__(self, request):
        # Log the request before passing it down the middleware chain
        self.process_request(request)
        response = self.get_response(request)
        # Log the response after it has been processed by other middlewares/views
        self.process_response(request, response)
        return response

    def process_request(self, request):
        # Extract the client's IP address from request META
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]  # Taking the first IP if there are multiple
        else:
            ip = request.META.get('REMOTE_ADDR', 'Unknown IP')

        # Limit log size by truncating the body, if necessary
        try:
            request_body = request.body[:1000].decode('utf-8')  # Adjust byte size as needed
        except UnicodeDecodeError:
            request_body = 'Could not decode request body.'

        # Log full request data along with the IP
        self.logger.info(f'IP: {ip} - Request Path: {request.path}, Method: {request.method}, Body: {request_body}')

    def process_response(self, request, response):
        # Limit log size by truncating the response content, if necessary
        try:
            response_content = response.content[:1000].decode('utf-8')  # Adjust byte size as needed
        except UnicodeDecodeError:
            response_content = 'Could not decode response content.'

        # Log full response data
        self.logger.info(f'Response Status: {response.status_code}, Content: {response_content}')
        return response

