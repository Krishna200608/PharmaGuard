"""
PharmaGuard Dashboard Views
===========================
Exports all 4 top-level views.
"""
from __future__ import annotations

from .overview import view_overview
from .per_pair import view_per_pair
from .disagreements import view_disagreements
from .baseline import view_baseline

__all__ = [
    'view_overview',
    'view_per_pair',
    'view_disagreements',
    'view_baseline',
]
