import re
from datetime import datetime
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator, validate_email

class LocationDataValidator():
    """
    Validate data values before further processing
    """
    
    # Function to validate the value depending on the chosen property type
    @staticmethod
    def validate(location_property, value) -> str:
        property_type = location_property.property_type

        # validate value as boolean
        if property_type == 'BOOL':
            accepted_boolean_values = [
                'Ja', 'Nee'
            ]
            if value in accepted_boolean_values:
                return value
            else:
                raise ValidationError(f"{value} is not a valid boolean")

        # validate value as datetime
        if property_type == 'DATE':
            try:
                date = datetime.strptime(value, '%d-%m-%Y')
            except:
                raise ValidationError(f"{value} is not a valid date")
            return value

        # validate value as e-mail address
        if property_type == 'EMAIL':
            try:
                validate_email(value)
            except:
                raise ValidationError(
                    f"{value} is not a valid email address")
            return value

        # validate value as integer
        if property_type == 'INT':
            int_regex = r'^-?\d+(,\d+)?$'
            if re.match(int_regex, value):
                return value
            else:
                raise ValidationError(f"{value} is not a valid number")

        # validate value as string
        if property_type == 'STR':
            return value

        # validate value as url
        if property_type == 'URL':
            url = URLValidator()
            try:
                url(value)
            except:
                raise ValidationError(f"{value} is not a valid Url")                
            return value

        # validate value as choice list
        # get related choice options, compare value in model with value from field
        # this validation will not work when called from clean() in LocationData because the value should be empty (but this is not enforced in the model)
        if property_type == 'CHOICE':
            allowed_options = location_property.propertyoption_set.values_list(
                'option', flat=True)
            if value in allowed_options:
                return value
            else:
                raise ValidationError(f"{value} is not a valid choice")
