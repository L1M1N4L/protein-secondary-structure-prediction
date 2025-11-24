"""
Result export stubs for CSV/JSON/report/PDB outputs.

These helpers currently return strings so that the frontend can preview the
export workflow; file writing and richer formatting will follow.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import List

from .types import PredictionResult, ResiduePrediction


class ResultsExporter:
    def export_csv(self, residues: List[ResiduePrediction]) -> str:
        lines = ["position,residue,prediction,confidence,model"]
        for record in residues:
            lines.append(
                f"{record.position},{record.residue},{record.state},{record.confidence},{record.model}"
            )
        return "\n".join(lines)

    def export_json(self, result: PredictionResult) -> str:
        payload = {
            "distribution": result.distribution,
            "modelSummaries": [asdict(summary) for summary in result.model_summaries],
            "residues": [asdict(residue) for residue in result.residues],
        }
        return json.dumps(payload, indent=2)

    def export_text_report(self, result: PredictionResult) -> str:
        report = ["Protein Secondary Structure Prediction Report", "-" * 52]
        report.append("Distribution:")
        for state, pct in result.distribution.items():
            report.append(f"  • {state}: {pct}%")
        report.append("\nModel Metrics:")
        for summary in result.model_summaries:
            report.append(
                f"  • {summary.name}: acc={summary.accuracy}, prec={summary.precision}, rec={summary.recall}"
            )
        report.append("\nResidue Table Preview:")
        for residue in result.residues[:10]:
            report.append(
                f"  - Pos {residue.position:>3} {residue.residue}: {residue.state} ({residue.confidence})"
            )
        if len(result.residues) > 10:
            report.append(f"  ... {len(result.residues) - 10} more residues")
        return "\n".join(report)

