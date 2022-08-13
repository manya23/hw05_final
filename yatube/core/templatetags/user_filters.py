from django import template
register = template.Library()


@register.filter
def addclass(field, css):
    """Функция-фильтр. Возвращает объект field, содержащий
    дополнительные атрибуты из параметра css."""
    return field.as_widget(attrs={'class': css})
