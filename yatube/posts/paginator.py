from django.core.paginator import Paginator
from django.conf import settings


def make_pagination(request, pages):
    """Разбивает список объектов на пачки по page_len"""
    paginator = Paginator(pages, settings.PAGINATOR_PAGE_LEN)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return page_obj
