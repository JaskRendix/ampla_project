from __future__ import annotations

from fastapi import FastAPI

from .routers import classes, flow, items, links, metrics, project, security

app = FastAPI(title="Ampla Project API")

app.include_router(project.router, prefix="/project", tags=["project"])
app.include_router(items.router, prefix="/items", tags=["items"])
app.include_router(classes.router, prefix="/classes", tags=["classes"])
app.include_router(flow.router, prefix="/flow", tags=["flow"])
app.include_router(links.router, prefix="/links", tags=["links"])
app.include_router(security.router, prefix="/security", tags=["security"])
app.include_router(metrics.router, prefix="/metrics", tags=["metrics"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
