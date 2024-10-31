from drf_standardized_errors.formatter import ExceptionFormatter
from drf_standardized_errors.types import ErrorResponse


class MyExceptionFormatter(ExceptionFormatter):
    def format_error_response(self, error_response: ErrorResponse):
        error = error_response.errors[0]
        return {
            "status_code": error.code,
            "message": error.detail,
            "type": error_response.type,
            "data": error.attr
        }
