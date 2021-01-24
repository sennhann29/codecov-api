from cerberus import Validator
from rest_framework.exceptions import ValidationError

def parse_params(data):
    """
    Validate request params
    """

    # filter out empty values from the data; this makes parsing and setting defaults a bit easier
    non_empty_data = {
        key: value for key, value in data.items() if value not in [None, ""]
    }

    # For critical paths, "owner" and "repo" will be parsed from slug
    params_schema = {
        "commit": {
            "type": "string",
            "required": True,
            "regex": r"^\d+:\w{12}|\w{40}$",
            "coerce": lambda value: value.lower(),
        },
        "slug": {"type": "string", "regex": r"^[\w\-\.\~\/]+\/[\w\-\.]{1,255}$"},
        "token": {
            "type": "string",
            "required": True,
            "regex": r"^[0-9a-f]{8}(-?[0-9a-f]{4}){3}-?[0-9a-f]{12}$"
        },
        # NOTE leaving even though at the moment this should always be "master"
        "branch": {
            "type": "string",
            "nullable": True,
            "coerce": (
                lambda value: None
                if value == "HEAD"
                # if prefixed with "origin/" or "refs/heads", the prefix will be removed
                else value[7:]
                if value[:7] == "origin/"
                else value[11:]
                if value[:11] == "refs/heads/"
                else value,
            ),
        },
        "package": {"type": "string"},
    }

    v = Validator(params_schema, allow_unknown=True)
    if not v.validate(non_empty_data):
        raise ValidationError(v.errors)

    # return validated data, including coerced values
    return v.document
