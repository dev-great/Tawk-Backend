from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    # Extract error messages from response.data
    if isinstance(exc, ValidationError) and response is not None:
        error_messages = []
        for key, value in response.data.items():
            if isinstance(value, list):
                error_messages.extend(value)

        error_string = " ".join(error_messages)
        custom_response_data = {
            "statusCode": response.status_code,
            "message": error_string,
            "error": response.status_text
        }
        response.data = custom_response_data

    return response
