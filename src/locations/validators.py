import re
from datetime import datetime
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator, validate_email
from django.utils.deconstruct import deconstructible


def valid_boolean(value)-> str:
    """Validator for Boolean type location property"""
    accepted_boolean_values = ['Ja', 'Nee']
    if value in accepted_boolean_values:
        return value
    else:
        raise ValidationError(f"'{value}' is geen geldige boolean.")

def valid_date(value)-> str: 
    """Validator for Date type location property"""
    try:
        datetime.strptime(value, '%d-%m-%Y')
    except:
        raise ValidationError(f"'{value}' is geen geldige datum.")
    return value

def valid_email(value)-> str:
    """Validator for Email type location property"""
    try:
        validate_email(value)
    except:
        raise ValidationError(
            f"'{value}' is geen geldig e-mail adres.")
    return value

def valid_geolocation(value)-> str:
    """Validator for Geolocation type location property"""
    # Resolution is up 1mm (8 decimals)
    geolocation_regex = r'^\d{1,2}\.\d{1,8}$'
    # Check for geolocation format
    if re.match(geolocation_regex, value):
        return value
    else:
        raise ValidationError(f"'{value}' is geen geldige geo coördinaat.")

def valid_number(value)-> str:
    """Validator for number type location property"""
    num_regex = r'^-?\d+(,\d+)?$'
    if re.match(num_regex, value):
        return value
    else:
        raise ValidationError(f"'{value}' is geen geldig getal.")

def valid_memo(value)-> str:
    """Validator for Memo type location property"""
    if isinstance(value, str):
        return value
    else:
        raise ValidationError(f"'{value}' is geen geldige tekst.")

def valid_postal_code(value)-> str:
    """Validator for Postal Code type location property"""
    postal_code_regex = r'^[1-9][0-9]{3}\s?(?!SA|SD|SS)[A-Z]{2}$'
    if re.match(postal_code_regex, value):
        return value
    else:
        raise ValidationError(f"'{value}' is geen geldige postcode.")

def valid_string(value)-> str:
    """Validator for String type location property"""
    if isinstance(value, str):
        return value
    else:
        raise ValidationError(f"'{value}' is geen geldige tekst.")

def valid_url(value) -> str:
    """Validator for Url type location property"""
    url = URLValidator()
    try:
        url(value)
    except:
        raise ValidationError(f"'{value}' is geen geldige url.")                
    return value


@deconstructible
class ChoiceValidator:
    """Validator for Choice type location property"""
    def __init__(self, location_property):
        self.location_property = location_property

    def __call__(self, value)-> str:
        # get related choice options, compare value in model with value from field
        # this validation will not work when called from clean() in LocationData because the value should be empty (but this is not enforced in the model)
        allowed_options = self.location_property.propertyoption_set.values_list('option', flat=True)
        # Check for multiple flag, because only those values should be split by a pipe character 
        if self.location_property.multiple:
            if not type(value) == list:
                values = value.split('|')
            else:
                values = value
        else:
            values = [value]

        for v in values:
            if v not in allowed_options:
                raise ValidationError(f"'{v}' is geen geldige invoer voor {self.location_property.label}.")
        return value

def get_locationdata_validator(location_property, value):
    """
    Based upon the location property instance, the appropriate validator will be called for a
    """
    if value != None:
        # match the property_type to the proper validation method
        match location_property.property_type:
            case 'BOOL':
                return valid_boolean(value)
            case 'DATE':
                return valid_date(value)
            case 'EMAIL':
                return valid_email(value)
            case 'GEO':
                return valid_geolocation(value)
            case 'NUM':
                return valid_number(value)
            case 'MEMO':
                return valid_memo(value)
            case 'POST':
                return valid_postal_code(value)
            case 'STR':
                return valid_string(value)
            case 'URL':
                return valid_url(value)
            case 'CHOICE':
                validator = ChoiceValidator(location_property)
                return validator(value)


@deconstructible
class LocationNameValidator():
    """Custom validation to check if the name is unique"""
    def __init__(self, pandcode):
        self.pandcode = pandcode

    def __call__(self, value)-> str:
        from locations.models import Location

        # An existing instance mustn't be included in the queryset; otherwise you can't update the instance itself
        if self.pandcode:
            if Location.objects.filter(name__iexact=value).exclude(pandcode=self.pandcode).exists():
                raise ValidationError(f"Er bestaat al een locatie met de naam '{value}'.")
        else:
            if Location.objects.filter(name__iexact=value).exists():
                raise ValidationError(f"Er bestaat al een locatie met de naam '{value}'.")
        return value