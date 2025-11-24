"""
Feature extraction utilities for amino acid sequences.

Current implementation produces pseudo-random profiles so the frontend can
visualize data before the scientific pipeline is ready.
"""

from __future__ import annotations

import random
from typing import Dict, List

import numpy as np


class FeatureExtractor:
    def __init__(self, window_size: int = 7, smoothing: float = 0.5):
        self.window_size = window_size
        self.smoothing = smoothing

    def compute_profiles(self, sequence: str) -> Dict[str, List[float]]:
        if not sequence:
            raise ValueError("Sequence is empty.")
        length = len(sequence)
        base = np.linspace(0.2, 0.8, length)

        def noisy_profile(scale: float) -> List[float]:
            noise = np.random.normal(0, scale, length)
            smoothed = (1 - self.smoothing) * base + self.smoothing * (base + noise)
            return np.clip(smoothed, 0, 1).round(3).tolist()

        return {
            "hydrophobicity": noisy_profile(0.15),
            "polarity": noisy_profile(0.12),
            "molecular_weight": noisy_profile(0.18),
        }

