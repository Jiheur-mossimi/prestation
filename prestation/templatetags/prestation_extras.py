from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Récupère un élément d'un dictionnaire par sa clé"""
    return dictionary.get(key)

@register.filter
def format_minutes(minutes):
    """Formate un nombre de minutes en format heures/minutes"""
    if not minutes:
        return "N/A"
    try:
        minutes = int(minutes)
        heures = minutes // 60
        mins = minutes % 60
        return f"{heures}h{mins:02d}"
    except (ValueError, TypeError):
        return "N/A"