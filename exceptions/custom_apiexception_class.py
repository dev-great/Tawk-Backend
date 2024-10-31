from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework import status


class CustomAPIException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'A server error occurred.'
    default_code = 'error'

    def __init__(self, detail=None, status_code=None, data=None):
        if detail is not None:
            self.detail = detail
        if status_code is not None:
            self.status_code = status_code
        if data is not None:
            self.data = data

        super().__init__(detail=detail)

    def get_full_details(self):
        return Response({
            'status_code': self.status_code,
            'message': self.detail,
            "type": self.default_detail,
            'data': getattr(self, 'data', None)
        }, status=self.status_code)

    def __str__(self):
        return f"{self.detail} (status code: {self.status_code})"
