from abc import ABC, abstractmethod
import datetime
import pathlib
import time


class FileWatcher(ABC):

  @abstractmethod
  def add_file(self, path: pathlib.Path) -> None:
    pass

  @abstractmethod
  def wait_for_changes(self) -> None:
    pass


class NullFileWatcher(FileWatcher):

  def add_file(self, path: pathlib.Path) -> None:
    pass

  def wait_for_changes(self) -> None:
    raise RuntimeError("Unable to wait for changes with NullFileWatcher.")


class FileWatcherImpl(FileWatcher):

  def __init__(self) -> None:
    self._paths: list[pathlib.Path] = []
    self._mtimes: list[float] = []

  def _get_mtimes(self) -> list[float]:
    return [f.stat().st_mtime for f in self._paths]

  def add_file(self, path: pathlib.Path) -> None:
    if path == pathlib.Path("/dev/stdin"):
      raise RuntimeError("Unable to watch /dev/stdin.")

    self._paths.append(path)
    self._mtimes.append(path.stat().st_mtime)

  def wait_for_changes(self) -> None:
    print(f"Waiting for changes: {' '.join(str(p) for p in self._paths)}\n")
    while True:
      new_values = self._get_mtimes()
      assert len(self._mtimes) == len(new_values)
      if self._mtimes != self._get_mtimes():
        changes = [i for i, v in enumerate(new_values) if v != self._mtimes[i]]
        assert changes
        print(f"Changes: {' '.join(str(self._paths[i]) for i in changes)}\n")
        self._paths = []
        self._mtimes = []
        return
      time.sleep(1)
