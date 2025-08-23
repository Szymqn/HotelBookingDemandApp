from django import template

register = template.Library()


@register.filter
def trending_tag(value):
    if value >= 0:
        return "trending_up"
    else:
        return "trending_down"
