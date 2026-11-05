# Migration Gap Checklist

This document tracks the migration of the **legacy Ampla normalization pipeline** (XSLT) into the new **Python-based normalization engine** (`ampla_project`).  
Only XSLTs that contain **normalization logic** are considered in scope.  
Legacy **reporting, HTML, Excel, DotML, and mindmap** templates are explicitly **out of scope**.

---

# 1. Core Normalization Pipeline (In Scope)

## ✔ Implemented
- `Project.Normalize.xslt` → `ampla_project.normalize.items`, `properties`, `classes`, `links`
- `Authstore.Normalize.xslt` → `ampla_project.normalize.security` (optional AuthStore input)
- Class normalization → `ampla_project.normalize.classes`
- Item/property normalization → `ampla_project.normalize.items`, `ampla_project.normalize.properties`
- Property specifics & subscriptions → `ampla_project.normalize.properties`
- DecisionMatrix inputs/rules, source defaults, SOAP adapter fields, and Favorites structures
- Link resolution (LinkFrom/LinkTo) → `ampla_project.normalize.links`
- Expression formatting / `ExpressionConfig` → `ampla_project.normalize.expressions`
- Expression dependencies, source-item relationships, declared streams, and stream
  property links → `ampla_project.normalize.expression_model`
- Flow graph and source-compatible root/immediate-link flow structure →
  `ampla_project.normalize.flow`
- `File.ItemId.Fullname.Type.xslt` → `ampla_project.outputs.item_mapping`
- Security extraction → `ampla_project.normalize.security`
- Context, translations, version extraction → `ampla_project.normalize.context`
- Translation injection and supported `DisplayName` generation → `ampla_project.normalize.items`

## ❗ Missing (Normalization Only)
- None currently identified in the documented normalization scope.

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
- Expression dependency extraction and source-item relationships
- Declared-stream selection and expression property links
- Expression reference and dependency serialization, including unresolved targets
- Expression formatting / `ExpressionConfig` fallback behavior

## ❗ Missing
- None (normalization layer complete)

## Out of Scope
- `Document.Expressions.DotML.xslt`
- `Excel.Expressions.xslt`

(Export-only templates.)

---

# 4. Flow & Graph Resolution (In Scope)

## ✔ Implemented
- Flow graph generation, root selection, ordering, and immediate child links
  (`Project.Flow.xslt`)
- LinkFrom/LinkTo behavior (`Project.LinkFrom.xslt`, `Project.LinkTo.xslt`)

`Project.Flow.xslt` passes `current` to `alreadyVisited`, whose declared parameter
is `hash`. The source transform therefore emits only immediate linked items under
each root. The normalized `flow` model preserves this observed behavior; the
separate flat `flow_graph` and `/flow` API remain unchanged.

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

1. **Remaining translation edge cases** (basic translation support exists)
2. Revalidate source-specific normalization cases as new representative fixtures become available.
3. Everything else → **explicitly out of scope**
