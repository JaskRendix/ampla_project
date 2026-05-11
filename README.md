# Ampla Project Normalization Engine

A Python implementation of the Ampla project normalization pipeline.  
This package replaces the normalization logic from the legacy XSLT‑based ProjectAnalysis tool.

## Overview

The engine loads an Ampla project XML export and builds a structured model of:

- **items**  
- **classes**  
- **properties**  
- **links**  
- **flow relationships**  
- **expressions**  
- **security**  

The model can be serialized to JSON for downstream tools.

The project focuses on the normalization layer only.  
Legacy HTML, Excel, DotML, metrics, and inventory exports are not included.

## Features

- Clear project model  
- Deterministic normalization pipeline  
- LinkFrom and LinkTo graph construction  
- Expression reference resolution  
- Security model extraction  
- JSON serialization  
- Full test suite for core modules  

## Project Structure

```
ampla_project/
  model/          # Data classes
  normalize/      # Normalization pipeline
  outputs/        # JSON serialization
docs/             # Developer documentation
tests/            # Unit tests
```

## Installation

```
pip install -e .
```

Requires Python 3.10 or later.

## Usage

```python
from lxml.etree import parse
from ampla_project.normalize import normalize
from ampla_project.outputs.json import project_to_json

root = parse("AmplaProject.xml").getroot()
project = normalize(root)
data = project_to_json(project)

print(data)
```

## Running Tests

```
pytest -q
```

## Legacy Reference

This project re‑implements the normalization logic from the original Ampla ProjectAnalysis tool:

[https://github.com/Ampla/ProjectAnalysis](https://github.com/Ampla/ProjectAnalysis)

The Python engine replaces the normalization layer only.  
The legacy tool includes a full reporting system that is not part of this package.

## Documentation

- `docs/legacy-xslt-architecture.md` — structure of the original XSLT system  
- `docs/xslt-to-python-mapping.md` — mapping between XSLT templates and Python modules  
- `docs/migration-gaps.md` — features covered and features outside the project scope  

## License

MIT License
