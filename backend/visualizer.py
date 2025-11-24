"""
Visualizer stubs that will later emit matplotlib objects.

For now these helpers return plain dictionaries so the frontend can preview the
data that will eventually feed real charts.
"""

from __future__ import annotations

from typing import Dict, List

from .types import FeatureProfile, PredictionResult


class Visualizer:
    @staticmethod
    def sequence_colors(residues: List[str]) -> List[str]:
        palette = {"α-Helix": "#f44336", "β-Sheet": "#2196f3", "Coil": "#4caf50"}
        return [palette.get(state, "#9e9e9e") for state in residues]

    @staticmethod
    def distribution_chart(distribution: Dict[str, float]) -> Dict[str, float]:
        return distribution

    @staticmethod
    def feature_lines(profile: FeatureProfile) -> Dict[str, List[float]]:
        return {
            "Hydrophobicity": profile.hydrophobicity,
            "Polarity": profile.polarity,
            "Molecular Weight": profile.molecular_weight,
        }

    @staticmethod
    def build_visual_payload(result: PredictionResult) -> Dict[str, object]:
        states = [res.state for res in result.residues]
        return {
            "sequence_colors": Visualizer.sequence_colors(states),
            "distribution": Visualizer.distribution_chart(result.distribution),
            "feature_lines": Visualizer.feature_lines(result.feature_profile),
        }

