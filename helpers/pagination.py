from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPageNumberPagination(PageNumberPagination):
    page_size = 10

    def get_paginated_response(self, data):
        return Response({
            "next": self.get_next_link() or None,
            "prev": self.get_previous_link() or None,
            "count": self.page.paginator.count,
            "number_of_pages": self._calculate_page_number(),
            "results": data
        })

    def _calculate_page_number(self) -> int:
        # No remainder, we have an even number of pages
        if self.page.paginator.count % self.page_size == 0:
            return int(self.page.paginator.count / self.page_size)
        else:
            return int(self.page.paginator.count / self.page_size) + 1
