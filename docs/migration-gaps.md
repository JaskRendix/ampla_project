# Migration Gap Checklist

This document tracks the migration of the **legacy Ampla normalization pipeline** (XSLT) into the new **Python-based normalization engine** (`ampla_project`).  
Only XSLTs that contain **normalization logic** are considered in scope.  
Legacy **reporting, HTML, Excel, DotML, and mindmap** templates are explicitly **out of scope**.

---

# 1. Core Normalization Pipeline (In Scope)

## ✔ Implemented
- `Project.Normalize.xslt` → `ampla_project.normalize.items`, `properties`, `classes`, `links`
- Class normalization → `ampla_project.normalize.classes`
- Item/property normalization → `ampla_project.normalize.items`, `ampla_project.normalize.properties`
- Property specifics & subscriptions → `ampla_project.normalize.properties`
- Link resolution (LinkFrom/LinkTo) → `ampla_project.normalize.links`
- Expression formatting / `ExpressionConfig` → `ampla_project.normalize.expressions`
- Flow graph creation → `ampla_project.normalize.flow`
- Security extraction → `ampla_project.normalize.security`
- Context, translations, version extraction → `ampla_project.normalize.context`

## ❗ Missing (Normalization Only)
- `Authstore.Normalize.xslt` — authstore merge logic not implemented
- `Project.Translations.xslt` / `Translate.Project.xslt` — translation injection not implemented
- `File.ItemId.Fullname.Type.xslt` — helper for ID/fullname/type mapping not implemented

## Priority
- **High**: Authstore + translation logic (if full parity with legacy normalization is required)
- **Medium**: Helper templates (only needed for legacy‑compatible output)

---

# 2. Security (In Scope)

## ✔ Implemented
- User/scope extraction
- Identity parsing
- Security model normalization

## ❗ Missing
- None (normalization layer complete)

## Out of Scope
- `Excel.Security.xslt`
- `Document.Security.xslt`
- `Document.Security.Text.xslt`

(These are **reporting templates**, not normalization.)

---

# 3. Expressions (In Scope)

## ✔ Implemented
- Expression normalization (`Project.Expressions.xslt` equivalent)

## ❗ Missing
- None (normalization layer complete)

## Out of Scope
- `Document.Expressions.DotML.xslt`
- `Excel.Expressions.xslt`

(Export-only templates.)

---

# 4. Flow & Graph Resolution (In Scope)

## ✔ Implemented
- Flow graph generation (`Project.Flow.xslt`)
- LinkFrom/LinkTo behavior (`Project.LinkFrom.xslt`, `Project.LinkTo.xslt`)

## ❗ Missing
- None (normalization layer complete)

## Out of Scope
- `BuildToDotML.xslt`
- `Project.Mindmap(0.8.1).xslt`
- `Common.Graphs.DotML.xslt`
- `Document.Graphs.DotML.xslt`
- `Include.Graphs.*.xslt`

(These generate **DotML/GraphViz/mindmap outputs**, not normalization.)

---

# 5. Inventory / Equipment / Metrics (Out of Scope)

These XSLTs belong to the **legacy reporting layer**, not the normalization engine.

- `Project.Inventory.xslt`
- `Project.Equipment.xslt`
- `Project.Metrics.xslt`
- `Document.Inventory.*.xslt`
- `Document.Equipment.xslt`
- `Document.Metrics.*.xslt`
- `Include.Graphs.Metrics.xslt`

No Python equivalents are planned.

---

# 6. Excel Export (Out of Scope)

All Excel templates are **presentation-only**:

- `Excel.*.xslt`
- `Excel.Modules.*.xslt`
- `Excel.Property.Tables.xslt`
- `Excel.Types.xslt`

The Python engine intentionally does not replicate these.

---

# 7. Documentation / HTML / Browser Output (Out of Scope)

All `Document.*` and `Bootstrap.*` XSLTs are **UI/reporting templates**, not normalization:

- `Document.*.xslt`
- `Bootstrap.*.xslt`
- `Document.Browser.*.xslt`
- `Document.Properties.*.xslt`
- `Document.Summary.xslt`
- `Document.Warnings.xslt`

These are not part of the migration target.

---

# 8. Other Legacy Export Targets (Out of Scope)

- `Project.Downtime.xslt`
- `Project.OLEDB.xslt`
- `Project.RDF.xslt`
- `FormatStrings.xml`
- `Freemind.xsd`

These are specialized export formats and not part of the normalization engine.

---

# 9. Migration Scope Summary

## ✔ Fully migrated (normalization layer)
- Items  
- Properties  
- Classes  
- Links  
- Flow  
- Expressions  
- Security  
- Context  

## ✔ Partially migrated
- Translations (basic support only)

## ❌ Not migrated (by design)
- HTML reports  
- Excel exports  
- DotML/GraphViz  
- Mindmaps  
- Inventory/Equipment/Metrics reports  
- OLEDB/RDF/Downtime exports  

These belong to the **legacy reporting UI**, not the normalization engine.

---

# 10. Recommended Priority (Realistic Scope)

1. **Authstore normalization** (optional)
2. **Translation injection** (optional)
3. **Helper templates** (optional)
4. Everything else → **explicitly out of scope**
