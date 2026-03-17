from typing import Type, TypeVar, overload, Any, Callable, cast
from dataclasses import fields
from functools import wraps

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
