from rest_framework.response import Response


def custom_response(status_code, message, data=None):
    return Response({
        'status_code': status_code,
        'message': message,
        'data': data
    }, status=status_code)
