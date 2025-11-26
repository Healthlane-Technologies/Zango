"""
Utility functions for audit log formatting and processing.
"""

import ast

from dateutil import parser

from django.core.exceptions import ObjectDoesNotExist


def format_field_value(field, value, tenant=None):
    """
    Format a field value for display based on field type.

    This function handles formatting for various Django field types to provide
    human-readable representations in audit logs.

    Args:
        field: Django field object
        value: Raw value to format (string or primitive type)
        tenant: Tenant object for timezone-aware datetime formatting (optional)

    Returns:
        str: Formatted value for display

    Examples:
        - DateField: "2024-01-01" → "Jan 01, 2024"
        - BooleanField: "True" → "Yes"
        - ForeignKey: "123" → "Object Name" (fetches related object)
        - ChoiceField: "active" → "Active"
    """
    from zango.core.utils import get_datetime_str_in_current_timezone

    # Handle None/empty values
    if value in [None, "", "None", "null"]:
        return "N/A"

    try:
        field_type = field.get_internal_type()
    except AttributeError:
        return str(value)

    # DateTimeField, DateField, TimeField
    if field_type in ["DateTimeField", "DateField", "TimeField"]:
        try:
            parsed_date = parser.parse(str(value))
            if field_type == "DateField":
                return parsed_date.strftime("%b %d, %Y")
            elif field_type == "TimeField":
                return parsed_date.strftime("%I:%M %p")
            else:  # DateTimeField
                if tenant:
                    return get_datetime_str_in_current_timezone(parsed_date, tenant)
                return parsed_date.strftime("%b %d, %Y %I:%M %p")
        except (ValueError, TypeError):
            return str(value)

    # BooleanField
    elif field_type == "BooleanField":
        if isinstance(value, bool):
            return "Yes" if value else "No"
        return "Yes" if str(value).lower() in ["true", "1", "yes"] else "No"

    # ForeignKey, OneToOneField (including ZForeignKey, ZOneToOneField)
    elif field_type in ["ForeignKey", "OneToOneField", "ZForeignKey", "ZOneToOneField"]:
        try:
            related_model = field.related_model
            if value and value != "None":
                try:
                    # Try to convert value to appropriate type
                    pk_value = field.related_model._meta.pk.to_python(value)
                    obj = related_model.objects.get(pk=pk_value)
                    return str(obj)
                except (ObjectDoesNotExist, ValueError, TypeError):
                    return f"Deleted (ID: {value})"
            return "N/A"
        except Exception:
            return str(value)

    # Choice fields
    elif hasattr(field, "choices") and field.choices:
        choices_dict = dict(field.choices)
        # Try to evaluate if value is a string representation
        try:
            evaluated_value = ast.literal_eval(str(value))
            return choices_dict.get(evaluated_value, str(value))
        except (ValueError, SyntaxError):
            return choices_dict.get(value, str(value))

    # DecimalField, FloatField
    elif field_type in ["DecimalField", "FloatField"]:
        try:
            return f"{float(value):.2f}"
        except (ValueError, TypeError):
            return str(value)

    # Default: return as string
    return str(value)
