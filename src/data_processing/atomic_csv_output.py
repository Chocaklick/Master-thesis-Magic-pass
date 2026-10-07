"""Publish derived CSVs by replacement after a complete temporary write.

Original external inputs are never passed here. A failed replacement leaves
the previous file intact and retains the temporary file for explicit recovery.
"""
import os
import tempfile
from pathlib import Path


def write_csv(frame, path):
    path = Path(path)
    fd, temporary = tempfile.mkstemp(prefix=path.stem + "_", suffix=".csv.tmp", dir=path.parent)
    os.close(fd)
    frame.to_csv(temporary, index=False, lineterminator="\n")
    os.replace(temporary, path)
