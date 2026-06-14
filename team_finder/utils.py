from django.core.paginator import Paginator


def paginate_queryset(queryset, page_number, limit):
    """Возвращает конкретную страницу набора данных."""
    paginator = Paginator(queryset, limit)
    return paginator.get_page(page_number)
