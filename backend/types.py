"""Common dataclasses and type aliases for the prediction pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ResiduePrediction:
    position: int
    residue: str
    state: str
    confidence: float
    model: str


@dataclass
class ModelSummary:
    name: str
    accuracy: float
    precision: float
    recall: float
    notes: str = ""


@dataclass
class FeatureProfile:
    hydrophobicity: List[float] = field(default_factory=list)
    polarity: List[float] = field(default_factory=list)
    molecular_weight: List[float] = field(default_factory=list)


@dataclass
class PredictionResult:
    residues: List[ResiduePrediction]
    distribution: Dict[str, float]
    model_summaries: List[ModelSummary]
    feature_profile: FeatureProfile

