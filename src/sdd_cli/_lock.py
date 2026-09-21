"""Tiny cross-process file lock for the few SDD writes that must not race.

Two agent sessions can incorporate track stages at the same moment (each takes
"the next free NNN"). The lock is a file created with ``O_EXCL``: atomic on every
platform the CLI supports, no dependencies, and self-healing when a crashed
process leaves it behind (a stale lock is broken after ``stale`` seconds).
"""

from __future__ import annotations

import contextlib
import json
import os
import time
from collections.abc import Iterator
from pathlib import Path


class LockTimeout(TimeoutError):
    """Raised when the lock stays held past the timeout."""


def _age(path: Path) -> float:
    try:
        return time.time() - path.stat().st_mtime
    except OSError:
        return 0.0


@contextlib.contextmanager
def file_lock(path: Path, *, timeout: float = 15.0, stale: float = 60.0,
              poll: float = 0.05) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout
    while True:
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            if _age(path) > stale:
                with contextlib.suppress(OSError):
                    path.unlink()  # crashed holder: break the stale lock
                continue
            if time.monotonic() >= deadline:
                raise LockTimeout(f"{path.name} is held by another sdd process") from None
            time.sleep(poll)
            continue
        try:
            os.write(fd, json.dumps({"pid": os.getpid(), "at": time.time()}).encode("utf-8"))
        finally:
            os.close(fd)
        break
    try:
        yield
    finally:
        with contextlib.suppress(OSError):
            path.unlink()
