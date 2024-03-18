from typing import get_origin, get_args, Union


def is_valid_type(value, field_type):
    origin = get_origin(field_type)
    if origin is not None:
        if origin is Union:
            return any(is_valid_type(value, t) for t in get_args(field_type))
        if isinstance(value, origin):
            args = get_args(field_type)
            if len(args) == 1:
                return is_valid_type(value, args[0])
            return all(is_valid_type(v, t) for v, t in zip(value, args))
    else:
        return isinstance(value, field_type)


def get_optional_type(opt_type):
    if get_origin(opt_type) is Union:
        return next((t for t in get_args(opt_type) if t is not type(None)), None)
    return opt_type
