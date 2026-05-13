from __future__ import annotations

from functools import lru_cache

from lxml.etree import parse

from ampla_project.model.project import Project
from ampla_project.normalize import normalize


@lru_cache(maxsize=16)
def load_project(path: str) -> Project:
    root = parse(path).getroot()
    return normalize(root)
