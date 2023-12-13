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
    def valid_boolean(value)-> str:
        accepted_boolean_values = ['Ja', 'Nee']
        if value in accepted_boolean_values:
            return value
        else:
            raise ValidationError(f"{value} is not a valid boolean")

    @staticmethod
    def valid_date(value)-> str: 
        try:
            datetime.strptime(value, '%d-%m-%Y')
        except:
            raise ValidationError(f"{value} is not a valid date")
        return value

    @staticmethod
    def valid_email(value)-> str:
        try:
            validate_email(value)
        except:
            raise ValidationError(
                f"{value} is not a valid email address")
        return value

    @staticmethod
    def valid_integer(value)-> str:
        int_regex = r'^-?\d+(,\d+)?$'
        if re.match(int_regex, value):
            return value
        else:
            raise ValidationError(f"{value} is not a valid number")
        
    @staticmethod
    def valid_string(value)-> str:
        return value

    @staticmethod
    def valid_url(value):
        url = URLValidator()
        try:
            url(value)
        except:
            raise ValidationError(f"{value} is not a valid Url")                
        return value

    @staticmethod
    def valid_choice(location_property, value)-> str:
        # get related choice options, compare value in model with value from field
        # this validation will not work when called from clean() in LocationData because the value should be empty (but this is not enforced in the model)
        allowed_options = location_property.propertyoption_set.values_list(
            'option', flat=True)
        if value in allowed_options:
            return value
        else:
            raise ValidationError(f"{value} is not a valid choice for {location_property.label}")

    @classmethod
    def validate(cls, location_property, value) -> str:
        # match the property_type to the proper validation method
        if location_property.required and value == None:
            raise ValidationError(f'Value required for {location_property.label}')
        if value != None:
            match location_property.property_type:
                case 'BOOL':
                    return cls.valid_boolean(value)
                case 'DATE':
                    return cls.valid_date(value)
                case 'EMAIL':
                    return cls.valid_email(value)
                case 'INT':
                    return cls.valid_integer(value)
                case 'STR':
                    return cls.valid_string(value)
                case 'URL':
                    return cls.valid_url(value)
                case 'CHOICE':
                    return cls.valid_choice(location_property, value)
