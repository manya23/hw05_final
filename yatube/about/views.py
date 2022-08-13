from django.views.generic.base import TemplateView


class AboutAuthorPage(TemplateView):
    """Возвращает статичную страницу с информацией об авторе."""
    template_name = 'about/author_info.html'


class AboutTechPage(TemplateView):
    """Возвращает статичную страницу с информацией
    о примененных в проекте технологиях."""
    template_name = 'about/tech_info.html'
