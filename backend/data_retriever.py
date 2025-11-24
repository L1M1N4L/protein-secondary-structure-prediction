"""
Data access utilities for fetching and parsing protein sequences.

Real implementations will integrate the UniProt REST API and advanced parsing.
"""

from __future__ import annotations

import random
from typing import Dict


class ProteinDataRetriever:
    """Facade that will later talk to UniProt; currently serves mock data."""

    def __init__(self, example_sequences: Dict[str, str]):
        self._examples = example_sequences

    def fetch_by_uniprot(self, uniprot_id: str) -> str:
        if not uniprot_id:
            raise ValueError("UniProt ID cannot be empty.")
        # TODO: Replace with actual UniProt REST request/response parsing.
        return random.choice(list(self._examples.values()))

    def parse_fasta(self, content: str) -> str:
        if not content.strip():
            raise ValueError("FASTA content is empty.")
        lines = [
            line.strip()
            for line in content.splitlines()
            if line and not line.startswith(">")
        ]
        sequence = "".join(lines)
        if not sequence:
            raise ValueError("No sequence data found in FASTA file.")
        return sequence.upper()

