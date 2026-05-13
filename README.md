# Ampla Project Normalization Engine

A Python implementation of the Ampla project normalization pipeline.  
This package replaces the normalization logic from the XSLT‑based ProjectAnalysis tool.

## Overview

The engine loads an Ampla project XML export and builds a structured model of:

- items  
- classes  
- properties  
- links  
- flow relationships  
- expressions  
- security  

The model can be serialized to JSON for downstream tools.

The project focuses on the normalization layer only.  
Legacy HTML, Excel, DotML, metrics, and inventory exports are not included.

## Features

- clear project model  
- deterministic normalization pipeline  
- LinkFrom and LinkTo graph construction  
- expression reference resolution  
- security model extraction  
- JSON serialization  
- test suite for core modules  

## Metrics

The engine computes project‑level metrics after normalization, including:

- item counts by type  
- link totals and broken link counts  
- orphaned items  
- class counts  
- unused classes  
- class inheritance depth  
- class inheritance cycles  
- user role count  

Metrics are stored in ProjectMetrics and included in the JSON output.

## API Layer (FastAPI)

A FastAPI service exposes the normalized project model over HTTP.  
The API loads a project, normalizes it, and returns the JSON model.

Available endpoints:

- /project  
- /items  
- /items/{id}  
- /classes  
- /flow  
- /links  
- /security  
- /metrics  
- /health  

The API is optional and does not modify the normalization engine.  
It is located in the api directory.

## Project Structure

```
ampla_project/
  model/          # data classes
  normalize/      # normalization pipeline
  outputs/        # JSON serialization
api/              # FastAPI service
docs/             # documentation
tests/            # unit tests
```

## Installation

```
pip install -e .
```

Python 3.12 or later is required.

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
The legacy tool includes a reporting system that is not part of this package.

## Documentation

- docs/legacy-xslt-architecture.md  
- docs/xslt-to-python-mapping.md  
- docs/migration-gaps.md  

## License

MIT License
