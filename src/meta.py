import argparse
import json
from dataclasses import MISSING, fields, is_dataclass, field
from functools import wraps
import pathlib
from typing import Type, TypeVar, overload, Any, Callable, cast, get_origin, get_args, get_type_hints
from types import UnionType

T = TypeVar("T")


@overload
def value_with_default(value: T | None, default: None) -> T | None:
  ...


@overload
def value_with_default(value: T | None, default: T) -> T:
  ...


def value_with_default(value: T | None, default: T | None) -> T | None:
  if value is not None:
    return value
  return default


C = TypeVar("C")
R = TypeVar("R")


def with_config(
    config_class: Type[C]) -> Callable[[Callable[..., R]], Callable[..., R]]:
  config_fields = {f.name for f in fields(cast(Any, config_class))}

  def decorator(func: Callable[..., R]) -> Callable[..., R]:

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> R:
      relevant_kwargs = {k: v for k, v in kwargs.items() if k in config_fields}
      remaining_kwargs = {
          k: v for k, v in kwargs.items() if k not in config_fields
      }
      if args and any(isinstance(arg, config_class) for arg in args):
        return func(*args, **remaining_kwargs)
      config = config_class(**relevant_kwargs)
      if args and not isinstance(args[0], config_class):
        # Handle `obj.method(...)`. `args` includes `obj`.
        return func(args[0], config, *args[1:], **remaining_kwargs)
      return func(config, *args, **remaining_kwargs)

    return wrapper

  return decorator


def _extend_argparse_field(var_type: Type[Any], name: str, default: Any,
                           parser: argparse.ArgumentParser,
                           is_required: bool) -> None:
  origin = get_origin(var_type)
  args = get_args(var_type)
  match (origin, args):
    case (list, (list_type,)):
      parser.add_argument(f"--{name}", type=list_type, action="append")
    case _ if is_dataclass(var_type):
      extend_argparse(var_type, parser, is_required, f"{name}_")
    case _ if var_type is frozenset[str]:
      parser.add_argument(
          f"--{name}", type=str, default=default, action="append")
    case _ if var_type is bool:
      parser.add_argument(
          f"--{name}", action=argparse.BooleanOptionalAction, default=default)
    case _ if var_type in [pathlib.Path, float, int, bool, str]:
      parser.add_argument(
          f"--{name}", type=var_type, default=default, required=is_required)
    case _:
      print(f"Unable to handle parameter {name}: ", var_type)


def extend_argparse(config_class: Type[C],
                    parser: argparse.ArgumentParser,
                    is_required: bool = True,
                    prefix: str = "") -> None:
  type_hints = get_type_hints(config_class)
  for f in fields(cast(Any, config_class)):
    origin = get_origin(f.type)
    args = get_args(f.type)
    name = prefix + f.name
    if origin is UnionType:
      filtered_args = [a for a in args if a is not type(None)]
      assert len(filtered_args) == 1
      nested_arg = filtered_args[0]
      _extend_argparse_field(nested_arg, name, f.default, parser, False)
    else:
      actual_type = type_hints.get(f.name, f.type)
      if f.default is MISSING:
        _extend_argparse_field(actual_type, name, None, parser, is_required)
      else:
        _extend_argparse_field(actual_type, name, f.default, parser, False)


def create_from_args(args: argparse.Namespace,
                     config_class: Type[C],
                     prefix: str = "") -> C | None:
  kwargs: dict[str, Any] = {}
  type_hints = get_type_hints(config_class)
  for f in fields(cast(Any, config_class)):
    arg_name = prefix + f.name
    field_type = type_hints.get(f.name, f.type)
    origin = get_origin(field_type)
    type_args = get_args(field_type)

    value = getattr(args, arg_name, None)
    is_required = True

    if origin is UnionType:
      filtered_args = [a for a in type_args if a is not type(None)]
      assert len(filtered_args) == 1
      field_type = filtered_args[0]
      origin = get_origin(field_type)
      type_args = get_args(field_type)
      is_required = False

    if is_dataclass(field_type):
      nested_config = create_from_args(args, cast(Type[C], field_type),
                                       f"{arg_name}_")
      if nested_config:
        kwargs[f.name] = nested_config
    elif origin is list and len(type_args) == 1:
      if value is not None:
        kwargs[f.name] = value

    elif field_type is frozenset[str]:
      if value is not None:
        kwargs[f.name] = frozenset(cast(list[str], value))

    elif field_type is pathlib.Path:
      if value is not None:
        kwargs[f.name] = pathlib.Path(cast(str, value))

    elif value is not None:
      kwargs[f.name] = value

  if not kwargs:
    return None
  return config_class(**kwargs)


def _convert_json_value(value: Any, target_type: Type[Any],
                        field_name: str) -> Any:
  """Converts a raw JSON value to the target Python type."""
  origin = get_origin(target_type)
  args = get_args(target_type)

  if is_dataclass(target_type):
    if not isinstance(value, dict):
      raise ValueError(
          f"Expected dictionary for nested dataclass field `{field_name}`, got {type(value).__name__}"
      )
    output = create_from_json_data(target_type, value)
    if value:
      raise ValueError(
          f"Unknown fields in nested configuration `{field_name}`: {', '.join(value)}"
      )
    return output

  if origin is tuple:
    assert len(args) == 2
    assert args[1] == Ellipsis
    list_item_type = args[0]
    if not isinstance(value, list):
      raise ValueError(
          f"Expected list for field `{field_name}`, got {type(value).__name__}")
    processed_list = []
    for item in value:
      processed_list.append(
          _convert_json_value(item, list_item_type, field_name))
    return tuple(processed_list)

  if target_type is pathlib.Path:
    if not isinstance(value, str):
      raise ValueError(f"Expected string for Path field ", {field_name},
                       ", got ", {type(value).__name__})
    return pathlib.Path(value)

  if origin in [frozenset, tuple] and args == (str,):
    if not isinstance(value, list):
      raise ValueError(f"Expected list for frozenset field ", {field_name},
                       ", got ", {type(value).__name__})
    return origin(value)

  if target_type is bool:
    if not isinstance(value, bool):
      if isinstance(value, str) and value.lower() in ("true", "false"):
        return value.lower() == "true"
      raise ValueError(
          f"Invalid type for field `{field_name}`. Expected bool, got {type(value).__name__} with value `{value}`"
      )
    return value

  if target_type in [str, int, float]:
    if not isinstance(value, target_type):
      try:
        return target_type(value)
      except (TypeError, ValueError):
        raise ValueError(
            f"Invalid type for field `{field_name}`. Expected {target_type.__name__}, got {type(value).__name__} with value `{value}`"
        )
    return value

  raise ValueError(
      f"Unsupported type for field `{field_name}` ({origin=}): {target_type=}, found {type(value).__name__}"
  )


def create_from_json_data(config_class: Type[C], data: dict[str, Any]) -> C:
  kwargs: dict[str, Any] = {}
  type_hints = get_type_hints(config_class)

  errors: list[str] = []
  for f in fields(cast(Any, config_class)):
    field_name = f.name
    field_type = type_hints.get(field_name, f.type)
    origin = get_origin(field_type)
    type_args = get_args(field_type)

    try:
      if origin is UnionType:
        filtered_args = [a for a in type_args if a is not type(None)]
        if len(filtered_args) != 1:
          raise ValueError(
              f"Unsupported Union type for field `{field_name}`: {field_type}")
        field_type = filtered_args[0]
        default_value = None
      elif f.default is not MISSING:
        default_value = f.default
      else:
        default_value = MISSING

      if field_name not in data:
        if default_value is MISSING:
          raise ValueError(
              f"Missing required field `{field_name}` for {config_class.__name__}"
          )
        else:
          kwargs[field_name] = default_value
        continue

      value = data.pop(field_name)

      kwargs[field_name] = _convert_json_value(value, field_type, field_name)
    except ValueError as e:
      errors.append(str(e))

  if data:
    errors.append(
        f"Unknown field(s) for {config_class.__name__}: {', '.join(data)}")

  if errors:
    raise ValueError("\n".join(errors))

  return config_class(**kwargs)
