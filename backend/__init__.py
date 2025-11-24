"""Backend module for the Protein Secondary Structure Predictor."""

from .placeholders import ExampleRepository, PredictionFacade
from .pipeline import PredictionPipeline
from .types import FeatureProfile, ModelSummary, PredictionResult, ResiduePrediction

__all__ = [
    "ExampleRepository",
    "PredictionFacade",
    "PredictionPipeline",
    "FeatureProfile",
    "ModelSummary",
    "PredictionResult",
    "ResiduePrediction",
]

