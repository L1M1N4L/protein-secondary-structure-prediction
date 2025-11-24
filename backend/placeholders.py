"""
Placeholder backend components for the Protein Secondary Structure Predictor.

These shims allow the frontend to be exercised before the real data retrieval,
feature extraction, prediction, visualization, and export layers are wired in.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from typing import Dict, Iterable, List, Sequence

from .data_retriever import ProteinDataRetriever
from .exporter import ResultsExporter
from .pipeline import PredictionPipeline
from .types import PredictionResult


class ExampleRepository:
    """Stores bundled sequences for demos, tutorials, and offline testing."""

    def __init__(self) -> None:
        self._examples: Dict[str, str] = {
            "Hemoglobin (human)": (
                "VLSPADKTNVKAAWGKVGAHAGEYGAEALERMFLSFPTTKTYFPHFDLSHGSAQVK"
                "GHGKKVADALTNAVAHVDDMPNALSALSDLHAHKLRVDPVNFKLLSHCLLVTLAAHL"
                "PAEFTPAVHASLDKFLASVSTVLTSKYR"
            ),
            "Myoglobin (sperm whale)": (
                "GLSDGEWQQVLNVWGKVEADIPGHGQEVLIRLFKGHPETLEKFDKFKHLKTEAEMK"
                "ASEDLKKHGATVLTALGGILKKKGHHEAELKPLAQSHATKHKIPVKYLEFISEAIIH"
                "VLHSRHPGDFGADAQGAMNKALELFRKDIAAKYKELGFQG"
            ),
            "Lysozyme (chicken)": (
                "KVFGRCELAAAMKRHGLDNYRGYSLGNWVCAAKFESNFNTQATNRNTDGSTDYGIL"
                "QINSRWWCNDGRTPGSRNLCNIPCSALLSSDITASVNCAKKIVSDGNGMNAWVAWRN"
                "RCKGTDVQAWIRGCRL"
            ),
        }

    @property
    def sequences(self) -> Dict[str, str]:
        return dict(self._examples)

    def list_names(self) -> List[str]:
        return list(self._examples.keys())

    def get(self, name: str) -> str:
        if name not in self._examples:
            raise KeyError(f"Unknown example sequence: {name}")
        return self._examples[name]


class PredictionFacade:
    """
    High-level service the UI talks to.

    At this stage it still produces mock predictions but it already mirrors the
    layering we will need once the scientific backend is implemented.
    """

    def __init__(self) -> None:
        self.examples = ExampleRepository()
        self.retriever = ProteinDataRetriever(self.examples.sequences)
        self.pipeline = PredictionPipeline()
        self.exporter = ResultsExporter()

    # ---------------------------- Sequence helpers ----------------------------
    def fetch_sequence(self, uniprot_id: str) -> str:
        return self.retriever.fetch_by_uniprot(uniprot_id)

    def load_example(self, name: str) -> str:
        return self.examples.get(name)

    def parse_fasta(self, content: str) -> str:
        return self.retriever.parse_fasta(content)

    def describe_sequence(self, sequence: str) -> Dict[str, object]:
        if not sequence:
            return {"length": 0, "composition": {}, "is_valid": False}
        counts = Counter(sequence)
        total = len(sequence)
        composition = {res: round(count / total * 100, 1) for res, count in counts.items()}
        return {
            "length": total,
            "composition": composition,
            "is_valid": all(ch.isalpha() for ch in sequence),
        }

    # --------------------------- Prediction helpers ---------------------------
    def run_predictions(
        self, sequence: str, model_names: Sequence[str], config: Dict[str, object] | None = None
    ) -> PredictionResult:
        return self.pipeline.run(sequence, model_names, config)

    def export_payloads(self, result: PredictionResult) -> Dict[str, str]:
        return {
            "csv": self.exporter.export_csv(result.residues),
            "json": self.exporter.export_json(result),
            "report": self.exporter.export_text_report(result),
        }

    def serialize_result(self, result: PredictionResult) -> Dict[str, object]:
        return {
            "distribution": result.distribution,
            "modelSummaries": [asdict(summary) for summary in result.model_summaries],
            "residues": [asdict(residue) for residue in result.residues],
            "featureProfile": {
                "hydrophobicity": result.feature_profile.hydrophobicity,
                "polarity": result.feature_profile.polarity,
                "molecular_weight": result.feature_profile.molecular_weight,
            },
        }

