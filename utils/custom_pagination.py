from django.core.paginator import Paginator, EmptyPage
from rest_framework.response import Response

from utils.custom_response import custom_response


class CustomPagination:
    def paginate_queryset(self, queryset, request, view=None):
        page_size = request.query_params.get('page_size', 24)
        paginator = Paginator(queryset, page_size)
        page_number = request.query_params.get('page', 1)

        try:
            page = paginator.page(page_number)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)

        self.count = paginator.count
        self.page = page
        self.request = request
        return list(page)

    def get_paginated_response(self, data):
        return custom_response(status_code=200, message="Success", data={
            'count': self.count,
            'next': self.page.has_next() and self.page.next_page_number() or None,
            'previous': self.page.has_previous() and self.page.previous_page_number() or None,
            'num_pages': self.page.paginator.num_pages,
            'results': data
        })
