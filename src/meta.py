import argparse
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
                    prefix: str = '') -> None:
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
