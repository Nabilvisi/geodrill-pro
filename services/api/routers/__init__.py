"""Routers package for GeoDrill Pro v0.9."""
from .projects import router as projects_router
from .directional import router as directional_router
from .engineering import router as engineering_router
from .qualification import router as qualification_router
from .wells import router as wells_router

__all__ = [
    "projects_router",
    "directional_router",
    "engineering_router",
    "qualification_router",
    "wells_router",
]
