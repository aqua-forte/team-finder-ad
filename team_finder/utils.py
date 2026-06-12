from django.core.paginator import Paginator


def paginate_queryset(queryset, page_number, limit):
    """
    Generic pagination utility to return a specific page of a queryset.
    """
    paginator = Paginator(queryset, limit)
    return paginator.get_page(page_number)
