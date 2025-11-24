"""
High-level orchestration of data retrieval, feature extraction, and predictions.
"""

from __future__ import annotations

from collections import Counter
from typing import Dict, List, Sequence

from .feature_extractor import FeatureExtractor
from .predictors import BasePredictor, build_predictors
from .types import FeatureProfile, PredictionResult, ResiduePrediction


class PredictionPipeline:
    def __init__(self) -> None:
        self.extractor = FeatureExtractor()

    def run(
        self,
        sequence: str,
        model_names: Sequence[str],
        config: Dict[str, object] | None = None,
    ) -> PredictionResult:
        if not sequence:
            raise ValueError("Sequence is empty.")
        predictors = self._build_predictors(model_names, config)
        all_predictions = self._merge_predictions(sequence, predictors)
        distribution = self._calc_distribution(all_predictions)
        summaries = [predictor.summarize() for predictor in predictors]
        profiles = self._build_feature_profile(sequence, config)

        return PredictionResult(
            residues=all_predictions,
            distribution=distribution,
            model_summaries=summaries,
            feature_profile=FeatureProfile(
                hydrophobicity=profiles["hydrophobicity"],
                polarity=profiles["polarity"],
                molecular_weight=profiles["molecular_weight"],
            ),
        )

    def _build_predictors(
        self, names: Sequence[str], config: Dict[str, object] | None
    ) -> List[BasePredictor]:
        if not names:
            raise ValueError("At least one model must be selected.")
        return build_predictors(names)

    def _merge_predictions(
        self, sequence: str, predictors: Sequence[BasePredictor]
    ) -> List[ResiduePrediction]:
        merged: List[ResiduePrediction] = []
        for predictor in predictors:
            merged.extend(predictor.predict(sequence))
        merged.sort(key=lambda rec: (rec.position, rec.model))
        return merged

    @staticmethod
    def _calc_distribution(predictions: Sequence[ResiduePrediction]) -> Dict[str, float]:
        counter = Counter(rec.state for rec in predictions)
        total = sum(counter.values()) or 1
        return {state: round(count / total * 100, 1) for state, count in counter.items()}

    def _build_feature_profile(
        self, sequence: str, config: Dict[str, object] | None
    ) -> Dict[str, List[float]]:
        if config:
            if "window_size" in config:
                self.extractor.window_size = int(config["window_size"])
            if "smoothing" in config:
                self.extractor.smoothing = float(config["smoothing"])
        return self.extractor.compute_profiles(sequence)

