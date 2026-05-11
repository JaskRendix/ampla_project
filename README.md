# Ampla Project Normalization Engine

A Python-based normalization engine for Ampla project XML files.  
This codebase replaces the legacy XSLT system found in the original ProjectAnalysis repository.

## Purpose

The engine reads an Ampla project export and produces a structured representation of:

- **items**  
- **classes**  
- **properties**  
- **links**  
- **flow relationships**  
- **expressions**  
- **security**  

The output can be serialized to JSON for downstream processing.

## Features

- Structured project model  
- Deterministic normalization pipeline  
- LinkFrom and LinkTo graph construction  
- Expression reference resolution  
- Security model extraction  
- JSON serialization  
- Unit tests for all core modules  

## Project Structure

```
ampla_project/
  model/          # Data classes
  normalize/      # Normalization pipeline
  outputs/        # JSON serialization
tests/            # Unit tests
src/              # Legacy XSLT system (not used by Python engine)
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

## Legacy System Notes

The `src` folder contains the original XSLT-based ProjectAnalysis tool.  
The Python engine replaces only the normalization logic.  
Legacy exports such as HTML, Excel, DotML, metrics, and inventory reports are not implemented.

For detailed documentation, see:

- docs/legacy-xslt-architecture.md
- docs/xslt-to-python-mapping.md
- docs/migration-gaps.md

## License

MIT License
