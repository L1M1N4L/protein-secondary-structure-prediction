"""
Predictor stubs for the Protein Secondary Structure Predictor.

Once the training data is available these classes will wrap scikit-learn models.
"""

from __future__ import annotations

import random
from typing import List, Sequence

from .types import ModelSummary, ResiduePrediction

STATES = ("α-Helix", "β-Sheet", "Coil")


class BasePredictor:
    name = "BasePredictor"

    def predict(self, sequence: str) -> List[ResiduePrediction]:
        raise NotImplementedError

    def summarize(self) -> ModelSummary:
        return ModelSummary(
            name=self.name,
            accuracy=round(random.uniform(0.72, 0.93), 2),
            precision=round(random.uniform(0.7, 0.92), 2),
            recall=round(random.uniform(0.7, 0.9), 2),
            notes="Placeholder metrics",
        )

    @staticmethod
    def _generate_predictions(sequence: str, model_name: str) -> List[ResiduePrediction]:
        predictions: List[ResiduePrediction] = []
        for idx, residue in enumerate(sequence, start=1):
            state = random.choice(STATES)
            confidence = round(random.uniform(0.45, 0.98), 2)
            predictions.append(
                ResiduePrediction(
                    position=idx,
                    residue=residue,
                    state=state,
                    confidence=confidence,
                    model=model_name,
                )
            )
        return predictions


class RuleBasedPredictor(BasePredictor):
    name = "Rule-Based"

    def predict(self, sequence: str) -> List[ResiduePrediction]:
        return self._generate_predictions(sequence, self.name)


class DecisionTreePredictor(BasePredictor):
    name = "Decision Tree"

    def predict(self, sequence: str) -> List[ResiduePrediction]:
        return self._generate_predictions(sequence, self.name)


class NaiveBayesPredictor(BasePredictor):
    name = "Naive Bayes"

    def predict(self, sequence: str) -> List[ResiduePrediction]:
        return self._generate_predictions(sequence, self.name)


def build_predictors(selected: Sequence[str]) -> List[BasePredictor]:
    mapping = {
        "Rule-Based": RuleBasedPredictor,
        "Decision Tree": DecisionTreePredictor,
        "Naive Bayes": NaiveBayesPredictor,
    }
    predictors: List[BasePredictor] = []
    for name in selected:
        if name not in mapping:
            continue
        predictors.append(mapping[name]())
    return predictors

