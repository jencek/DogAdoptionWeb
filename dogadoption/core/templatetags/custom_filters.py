from django import template

register = template.Library()

@register.filter
def startswith(text, starts):
    """Check if a string starts with the given substring."""
    if isinstance(text, str):
        return text.startswith(starts)
    return False
