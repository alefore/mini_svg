import argparse
from dataclasses import MISSING, fields, is_dataclass
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
      if args and isinstance(args[0], config_class):
        return func(*args, **remaining_kwargs)
      config = config_class(**relevant_kwargs)
      if args and not isinstance(args[0], config_class):
        # Handle `obj.method(...)`. `args` includes `obj`.
        return func(args[0], config, *args[1:], **remaining_kwargs)
      return func(config, *args, **remaining_kwargs)

    return wrapper

  return decorator


def _extend_argparse_field(var_type: Type[Any], name: str, default,
                           parser) -> None:
  origin = get_origin(var_type)
  args = get_args(var_type)
  match (origin, args):
    case (list, (list_type,)):
      parser.add_argument(f"--{name}", type=list_type, action="append")
    case _ if is_dataclass(var_type):
      extend_argparse(var_type, parser, f"{name}_")
    case _ if var_type is frozenset[str]:
      parser.add_argument(
          f"--{name}", type=str, default=default, action="append")
    case _ if var_type is bool:
      parser.add_argument(
          f"--{name}", action=argparse.BooleanOptionalAction, default=default)
    case _ if var_type in [pathlib.Path, float, int, bool, str]:
      parser.add_argument(f"--{name}", type=var_type, default=default)
    case _:
      print(f"Unable to handle parameter {name}: ", var_type)


def extend_argparse(config_class: Type[C],
                    parser: argparse.ArgumentParser,
                    prefix=''):
  type_hints = get_type_hints(config_class)
  for f in fields(cast(Any, config_class)):
    origin = get_origin(f.type)
    args = get_args(f.type)
    name = prefix + f.name
    if origin is UnionType:
      filtered_args = [a for a in args if a is not type(None)]
      assert len(filtered_args) == 1
      nested_arg = filtered_args[0]
      _extend_argparse_field(nested_arg, name, f.default, parser)
    else:
      actual_type = type_hints.get(f.name, f.type)
      if f.default is MISSING:
        _extend_argparse_field(actual_type, name, None, parser)
      else:
        _extend_argparse_field(actual_type, name, f.default, parser)
