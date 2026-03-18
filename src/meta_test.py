import unittest
from dataclasses import dataclass
import pathlib
from src.meta import create_from_json_data  # This import will initially fail


@dataclass
class SimpleConfig:
  name: str
  age: int
  is_active: bool = False


@dataclass(frozen=True)
class AllOptionalConfig:
  name: str = "foo"
  age: int = 20


@dataclass
class NestedConfig:
  id: str
  simple: SimpleConfig
  all_optional: AllOptionalConfig = AllOptionalConfig()


@dataclass
class OptionalPathConfig:
  path: pathlib.Path | None
  description: str


@dataclass
class OptionalNestedConfig:
  id: str
  optional_simple: SimpleConfig | None


class TestCreateFromJsonData(unittest.TestCase):

  def test_simple_config(self):
    data = {"name": "Test", "age": 30, "is_active": True}
    config = create_from_json_data(SimpleConfig, data)
    self.assertEqual(config, SimpleConfig(name="Test", age=30, is_active=True))
    self.assertEqual(data, {})  # data should be empty after consumption

  def test_simple_config_with_default(self):
    data = {"name": "Test", "age": 30}
    config = create_from_json_data(SimpleConfig, data)
    self.assertEqual(config, SimpleConfig(name="Test", age=30, is_active=False))
    self.assertEqual(data, {})

  def test_nested_config(self):
    data = {"id": "nested-1", "simple": {"name": "Nested", "age": 25}}
    config = create_from_json_data(NestedConfig, data)
    self.assertEqual(
        config,
        NestedConfig(
            id="nested-1",
            simple=SimpleConfig(name="Nested", age=25, is_active=False)))
    self.assertEqual(data, {})

  def test_missing_required_field_raises_error(self):
    data = {"age": 30}
    with self.assertRaisesRegex(
        ValueError, r"Missing required field `name` for SimpleConfig"):
      create_from_json_data(SimpleConfig, data)

  def test_unknown_field_raises_error(self):
    data = {"name": "Test", "age": 30, "extra": "foo"}
    with self.assertRaisesRegex(ValueError,
                                r"Unknown field\(s\) for SimpleConfig: extra"):
      create_from_json_data(SimpleConfig, data)

  def test_union_type_optional_field(self):

    @dataclass
    class OptionalStringConfig:
      value: str | None
      id: int

    data = {"id": 123, "value": "hello"}
    config = create_from_json_data(OptionalStringConfig, data)
    self.assertEqual(config, OptionalStringConfig(id=123, value="hello"))
    self.assertEqual(data, {})

    data = {"id": 456}
    config = create_from_json_data(OptionalStringConfig, data)
    self.assertEqual(config, OptionalStringConfig(id=456, value=None))
    self.assertEqual(data, {})

  def test_union_type_optional_path(self):
    data = {"description": "A path", "path": "/tmp/test.txt"}
    config = create_from_json_data(OptionalPathConfig, data)
    self.assertEqual(
        config,
        OptionalPathConfig(
            description="A path", path=pathlib.Path("/tmp/test.txt")))
    self.assertEqual(data, {})

    data = {"description": "No path"}
    config = create_from_json_data(OptionalPathConfig, data)
    self.assertEqual(config,
                     OptionalPathConfig(description="No path", path=None))
    self.assertEqual(data, {})

  def test_union_type_optional_nested_dataclass(self):
    data = {
        "id": "opt-nested-1",
        "optional_simple": {
            "name": "OptNested",
            "age": 35
        }
    }
    config = create_from_json_data(OptionalNestedConfig, data)
    self.assertEqual(
        config,
        OptionalNestedConfig(
            id="opt-nested-1",
            optional_simple=SimpleConfig(
                name="OptNested", age=35, is_active=False)))
    self.assertEqual(data, {})

    data = {"id": "opt-nested-2"}
    config = create_from_json_data(OptionalNestedConfig, data)
    self.assertEqual(
        config, OptionalNestedConfig(id="opt-nested-2", optional_simple=None))
    self.assertEqual(data, {})

  def test_type_mismatch_raises_error(self):
    data = {"name": "Test", "age": "not_an_int"}
    with self.assertRaisesRegex(
        ValueError,
        r"Invalid type for field `age`. Expected int, got str with value `not_an_int`"
    ):
      create_from_json_data(SimpleConfig, data)

  def test_nested_unknown_field_raises_error(self):
    data = {
        "id": "nested-1",
        "simple": {
            "name": "Nested",
            "age": 25,
            "extra_nested": True
        }
    }
    with self.assertRaisesRegex(
        ValueError, r"Unknown field\(s\) for SimpleConfig: extra_nested"):
      create_from_json_data(NestedConfig, data)

  def test_list_of_primitives(self):

    @dataclass
    class ListConfig:
      items: list[int]

    data = {"items": [1, 2, 3]}
    config = create_from_json_data(ListConfig, data)
    self.assertEqual(config, ListConfig(items=[1, 2, 3]))
    self.assertEqual(data, {})

  def test_list_of_paths(self):

    @dataclass
    class ListPathConfig:
      paths: list[pathlib.Path]

    data = {"paths": ["/a/b", "/c/d"]}
    config = create_from_json_data(ListPathConfig, data)
    self.assertEqual(
        config,
        ListPathConfig(paths=[pathlib.Path("/a/b"),
                              pathlib.Path("/c/d")]))
    self.assertEqual(data, {})

  def test_frozenset_of_strings(self):

    @dataclass
    class FrozensetConfig:
      tags: frozenset[str]

    data = {"tags": ["tag1", "tag2"]}
    config = create_from_json_data(FrozensetConfig, data)
    self.assertEqual(config, FrozensetConfig(tags=frozenset(["tag1", "tag2"])))
    self.assertEqual(data, {})

  def test_boolean_from_string(self):

    @dataclass
    class BooleanConfig:
      enabled: bool

    data = {"enabled": "true"}
    config = create_from_json_data(BooleanConfig, data)
    self.assertTrue(config.enabled)
    self.assertEqual(data, {})

    data = {"enabled": "false"}
    config = create_from_json_data(BooleanConfig, data)
    self.assertFalse(config.enabled)
    self.assertEqual(data, {})
