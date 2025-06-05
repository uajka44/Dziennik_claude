"""
Narzędzia do formatowania danych do wyświetlania
"""


def format_profit_points(value):
    """Formatuje profit points (dzieli przez 100 i pokazuje 2 miejsca po przecinku)"""
    if value is None:
        return ""
    adjusted_value = value / 100
    return f"{adjusted_value:.2f}"


def format_checkbox_value(value):
    """Formatuje wartość checkbox do wyświetlenia (1 -> ✓, inne -> "")"""
    return "✓" if value == 1 else ""


def format_price(value, precision=2):
    """Formatuje cenę z określoną precyzją"""
    if value is None:
        return ""
    return f"{value:.{precision}f}"


def format_volume(value):
    """Formatuje wolumen"""
    if value is None:
        return ""
    return f"{value:.2f}"


def safe_float_conversion(value, default=None):
    """Bezpieczna konwersja na float"""
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int_conversion(value, default=None):
    """Bezpieczna konwersja na int"""
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def format_setup_display(setup_value, max_length=15):
    """Formatuje setup do wyświetlenia w tabeli (skraca jeśli za długie)"""
    if not setup_value:
        return ""
    
    if len(setup_value) <= max_length:
        return setup_value
    
    return setup_value[:max_length-3] + "..."


def position_type_to_string(position_type):
    """Konwertuje typ pozycji na string"""
    if position_type == 0:
        return "buy"
    elif position_type == 1:
        return "sell"
    else:
        return "unknown"


def string_to_position_type(type_string):
    """Konwertuje string na typ pozycji"""
    if type_string.lower() == "buy":
        return 0
    elif type_string.lower() == "sell":
        return 1
    else:
        return None


def format_points(value):
    """Formatuje punkty z odpowiednią precyzją"""
    if value is None:
        return ""
    if value == 0.0:
        return "0.0"  # Pokazuj 0.0 jako 0.0, nie pusty string
    return f"{value:.1f}"


def truncate_text(text, max_length=50):
    """Skraca tekst do określonej długości"""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."
