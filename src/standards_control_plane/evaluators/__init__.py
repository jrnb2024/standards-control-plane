"""Evaluator entry points."""

from .architecture import evaluate_architecture
from .design import evaluate_design
from .governance import evaluate_governance
from .product import evaluate_product
from .ux import evaluate_ux

__all__ = [
    "evaluate_architecture",
    "evaluate_design",
    "evaluate_governance",
    "evaluate_product",
    "evaluate_ux",
]
