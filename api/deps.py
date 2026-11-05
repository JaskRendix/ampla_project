from __future__ import annotations

from functools import lru_cache

from lxml.etree import parse

from ampla_project.model.project import Project
from ampla_project.normalize import normalize


@lru_cache(maxsize=16)
def load_project(
    path: str,
    authstore_path: str | None = None,
    language_path: str | None = None,
) -> Project:
    root = parse(path).getroot()
    authstore_doc = parse(authstore_path).getroot() if authstore_path else None
    language_doc = parse(language_path).getroot() if language_path else None
    return normalize(root, language_doc=language_doc, authstore_doc=authstore_doc)
