from django import template

register = template.Library()

@register.filter
def inr(value):
    """
    Format a number as Indian Rupee (INR).
    E.g., 1000000 -> 10,00,000
    """
    try:
        value = float(value)
    except (ValueError, TypeError):
        return value

    is_negative = value < 0
    value = abs(value)
    
    # Extract integer part as string
    int_part = str(int(value))
    
    # Format integer part with Indian commas
    if len(int_part) > 3:
        last_three = int_part[-3:]
        other_numbers = int_part[:-3]
        if other_numbers:
            # insert commas every 2 digits from the end of other_numbers
            other_numbers = ','.join([other_numbers[max(0, i-2):i] for i in range(len(other_numbers), 0, -2)][::-1])
            int_part = other_numbers + ',' + last_three
            
    res = int_part
    if is_negative:
        res = '-' + res
        
    return res
