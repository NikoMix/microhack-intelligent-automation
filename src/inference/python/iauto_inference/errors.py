"""Typed error hierarchy for the inference layer."""

from __future__ import annotations


class InferenceError(Exception):
    """Base error for all inference-layer failures."""


class InferenceConfigError(InferenceError):
    """Raised when provider configuration is missing or inconsistent.

    Carries an actionable message so learners can self-correct in the labs.
    """
