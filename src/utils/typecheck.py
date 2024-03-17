from typing import get_origin, get_args, Union


def is_valid_type(value, field_type):
    origin_type = get_origin(field_type)
    if origin_type is Union:
        return any(is_valid_type(value, t) for t in get_args(field_type))
    else:
        return isinstance(value, field_type)


def get_optional_type(opt_type):
    if get_origin(opt_type) is Union:
        return next((t for t in get_args(opt_type) if t is not type(None)), None)
    return opt_type
