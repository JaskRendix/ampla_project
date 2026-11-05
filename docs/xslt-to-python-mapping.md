# XSLT → Python Normalization Mapping

This document maps the **legacy Ampla XSLT normalization pipeline** (`src/StyleSheets`) to the **modern Python implementation** in `ampla_project`.  
Only XSLTs that contain **normalization logic** are included.  
All **HTML, Excel, DotML, mindmap, and reporting templates** are explicitly **out of scope**.

---

## 1. Core Project Normalization

| Legacy XSLT | Purpose | Python Equivalent |
|------------|----------|-------------------|
| `Project.Normalize.xslt` | Main normalization pipeline | `normalize.items`, `normalize.properties`, `normalize.classes`, `normalize.links` |
| `Translate.Project.xslt` | Inject translated DisplayName for supported item types | `normalize.context`, `normalize.items` |
| `Project.Translations.xslt` | HTML translation upload page | Out of scope (presentation output) |
| `Document.Common.xslt` | Shared normalization helpers | `normalize.context` |
| `Document.Properties.xslt` | Property extraction | `normalize.properties` |
| `Document.ItemTypes.xslt` | Item type resolution | `normalize.items` |
| `File.ItemId.Fullname.Type.xslt` | Pipe-delimited ID/full-name/type mapping | `outputs.item_mapping` |

---

## 2. Class Definitions & Hierarchy

| XSLT | Purpose | Python Equivalent |
|------|---------|------------------|
| `Document.Hierarchy.xslt` | Item hierarchy | `normalize.items` |
| `Document.Interfaces.xslt` | Class/interface definitions | `normalize.classes` |
| `Project.Expressions.xslt` | Expression dependency/source/stream model | `normalize.expression_model` |
| `Project.Normalize.xslt` (ExpressionConfig templates) | Expression formatting and reference resolution | `normalize.expressions` |

---

## 3. Link Resolution (LinkFrom / LinkTo)

| XSLT | Purpose | Python Equivalent |
|------|---------|------------------|
| `Project.LinkFrom.xslt` | Forward link extraction and resolution | `normalize.links` |
| `Project.LinkTo.xslt` | Reverse link construction | `normalize.links` |
| `Document.Graphs.DotML.xslt` | Graph link extraction | `normalize.flow` |

---

## 4. Security & Permissions

| XSLT | Purpose | Python Equivalent |
|------|---------|------------------|
| `Project.Security.xslt` | Security model extraction | `normalize.security` |
| `Authstore.Normalize.xslt` | AuthStore merge: operations, role definitions, scope assignments, and members | `normalize.security` |
| `Document.Security.xslt` | Security details | `normalize.security` |
| `Document.Security.Text.xslt` | Security text output | `outputs.json` (serialization only) |

---

## 5. Flow Graph & Dependencies

| XSLT | Purpose | Python Equivalent |
|------|---------|------------------|
| `Project.Flow.xslt` | Flow graph plus source-compatible flow roots and immediate links | `normalize.flow` |
| `Document.Graphs.DotML.xslt` | Graph structure | `normalize.flow` |

---

## 6. Expressions & Calculations

| XSLT | Purpose | Python Equivalent |
|------|---------|------------------|
| `Document.Expressions.DotML.xslt` | Expression visualization/export | Out of scope |
| `Excel.Expressions.xslt` | Expression export | Out of scope |

---

## 7. Out‑of‑Scope XSLTs (Reporting Layer)

These XSLTs belong to the **legacy reporting/export UI**, not the normalization engine.  
They have **no Python equivalent by design**.

- `Document.Inventory.*.xslt`
- `Document.Metrics.*.xslt`
- `Document.ReportingPoints.xslt`
- `Excel.*.xslt`
- `Bootstrap.*.xslt`
- `Document.*.xslt`
- `Include.Graphs.*.xslt`
- `Project.Inventory.xslt`
- `Project.Equipment.xslt`
- `Project.Metrics.xslt`
- `Project.Downtime.xslt`
- `Project.OLEDB.xslt`
- `Project.RDF.xslt`
- `Project.Mindmap(0.8.1).xslt`
- `BuildToDotML.xslt`
- `FormatStrings.xml`
- `Freemind.xsd`

These templates generate **HTML, Excel, DotML, mindmaps, and UI documents**.  
They are intentionally excluded from the Python migration.

---

## Summary

### Fully replaced by Python
- Items  
- Properties  
- Classes  
- Links  
- Flow  
- Expressions  
- Security  
- Context  

### Partially replaced  
- Translation HTML/upload output from `Project.Translations.xslt` (intentionally out of scope)

`Translate.Project.xslt` model behavior is implemented: translation lookup, item/class
translation metadata, and translated `DisplayName` generation for item types that
declare that property.

### Not replaced (intentionally)
- HTML reports  
- Excel exports  
- DotML/GraphViz  
- Mindmaps  
- Inventory/Equipment/Metrics reports  
- OLEDB/RDF/Downtime exports  
