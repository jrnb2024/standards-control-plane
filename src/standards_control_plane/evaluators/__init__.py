"""Evaluator entry points."""

from .architecture import evaluate_architecture
from .governance import evaluate_governance

__all__ = ["evaluate_architecture", "evaluate_governance"]
