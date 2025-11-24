"""
Tkinter frontend for the Protein Secondary Structure Predictor.

The UI is intentionally rich so the backend can be wired in incrementally while
stakeholders already see the full workflow and interaction design.
"""

from __future__ import annotations

import itertools
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Dict, Iterable, List, Sequence

from backend import PredictionFacade, PredictionResult
from backend.visualizer import Visualizer


class ProteinStructureApp(tk.Tk):
    def __init__(self, backend: PredictionFacade | None = None) -> None:
        super().__init__()
        self.title("Protein Secondary Structure Predictor (Frontend Prototype)")
        self.geometry("1280x800")

        self.backend = backend or PredictionFacade()
        self.visualizer = Visualizer()

        self.sequence_var = tk.StringVar()
        self.sequence_source_var = tk.StringVar(value="No sequence loaded")
        self.sequence_length_var = tk.StringVar(value="0")
        self.sequence_valid_var = tk.StringVar(value="–")
        self.status_var = tk.StringVar(value="Ready.")
        self.progress_var = tk.IntVar(value=0)
        self.prediction_result: PredictionResult | None = None

        self._build_menu()
        self._build_layout()

    # --------------------------- UI scaffolding ---------------------------
    def _build_menu(self) -> None:
        menu_bar = tk.Menu(self)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Export Results...", command=self._handle_export_results)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)
        menu_bar.add_cascade(label="File", menu=file_menu)

        tools_menu = tk.Menu(menu_bar, tearoff=0)
        tools_menu.add_command(label="Preferences", command=self._not_implemented)
        menu_bar.add_cascade(label="Tools", menu=tools_menu)

        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="Documentation", command=self._not_implemented)
        help_menu.add_command(label="About", command=self._open_about_popup)
        menu_bar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menu_bar)

    def _build_layout(self) -> None:
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)

        self.nb = ttk.Notebook(container)
        self.nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self._build_input_tab()
        self._build_prediction_tab()
        self._build_results_tab()
        self._build_visualization_tab()
        self._build_about_tab()

        status_bar = ttk.Frame(self)
        status_bar.pack(fill=tk.X, padx=10, pady=(0, 5))
        ttk.Progressbar(status_bar, variable=self.progress_var, maximum=100, length=200).pack(side=tk.RIGHT, padx=5)
        ttk.Label(status_bar, textvariable=self.status_var, anchor=tk.W).pack(side=tk.LEFT, fill=tk.X, expand=True)

    # ------------------------------ Tabs ----------------------------------
    def _build_input_tab(self) -> None:
        frame = ttk.Frame(self.nb)
        self.nb.add(frame, text="Input")

        uniprot_frame = ttk.LabelFrame(frame, text="UniProt Search")
        uniprot_frame.pack(fill=tk.X, padx=10, pady=8)
        ttk.Label(uniprot_frame, text="UniProt ID:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.uniprot_entry = ttk.Entry(uniprot_frame, width=25)
        self.uniprot_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Button(uniprot_frame, text="Fetch", command=self._handle_uniprot_fetch).grid(row=0, column=2, padx=5, pady=5)

        paned = ttk.PanedWindow(frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        manual_frame = ttk.LabelFrame(paned, text="Sequence Editor")
        paned.add(manual_frame, weight=3)
        self.sequence_text = tk.Text(manual_frame, height=10, wrap=tk.WORD)
        self.sequence_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        btn_row = ttk.Frame(manual_frame)
        btn_row.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(btn_row, text="Load FASTA...", command=self._handle_fasta_upload).pack(side=tk.LEFT)
        ttk.Button(btn_row, text="Use Sequence", command=lambda: self._apply_manual_sequence("Manual Entry")).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(btn_row, text="Clear", command=lambda: self.sequence_text.delete("1.0", tk.END)).pack(side=tk.LEFT)

        diagnostics = ttk.LabelFrame(paned, text="Sequence Diagnostics")
        paned.add(diagnostics, weight=2)

        ttk.Label(diagnostics, text="Source:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=3)
        ttk.Label(diagnostics, textvariable=self.sequence_source_var).grid(row=0, column=1, sticky=tk.W, padx=5, pady=3)
        ttk.Label(diagnostics, text="Length:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=3)
        ttk.Label(diagnostics, textvariable=self.sequence_length_var).grid(row=1, column=1, sticky=tk.W, padx=5, pady=3)
        ttk.Label(diagnostics, text="Valid:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=3)
        ttk.Label(diagnostics, textvariable=self.sequence_valid_var).grid(row=2, column=1, sticky=tk.W, padx=5, pady=3)

        ttk.Label(diagnostics, text="Residue Composition (%)").grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=5, pady=(10, 3))
        self.composition_table = ttk.Treeview(
            diagnostics, columns=("Residue", "Percent"), show="headings", height=6
        )
        self.composition_table.heading("Residue", text="Residue")
        self.composition_table.heading("Percent", text="%")
        self.composition_table.column("Residue", width=80, anchor=tk.CENTER)
        self.composition_table.column("Percent", width=80, anchor=tk.CENTER)
        self.composition_table.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        diagnostics.grid_rowconfigure(4, weight=1)

        example_frame = ttk.LabelFrame(frame, text="Example Sequences")
        example_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.example_list = tk.Listbox(example_frame, height=5)
        for name in self.backend.examples.list_names():
            self.example_list.insert(tk.END, name)
        self.example_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        ttk.Button(example_frame, text="Load Example", command=self._insert_example_sequence).pack(
            side=tk.LEFT, padx=5, pady=5
        )

    def _build_prediction_tab(self) -> None:
        frame = ttk.Frame(self.nb)
        self.nb.add(frame, text="Prediction")

        models_frame = ttk.LabelFrame(frame, text="Models")
        models_frame.pack(fill=tk.X, padx=10, pady=8)
        self.model_vars: Dict[str, tk.BooleanVar] = {}
        for idx, name in enumerate(("Rule-Based", "Decision Tree", "Naive Bayes")):
            var = tk.BooleanVar(value=idx == 0)
            self.model_vars[name] = var
            ttk.Checkbutton(models_frame, text=name, variable=var).grid(row=0, column=idx, padx=10, pady=5)

        features_frame = ttk.LabelFrame(frame, text="Feature Configuration")
        features_frame.pack(fill=tk.X, padx=10, pady=8)

        ttk.Label(features_frame, text="Window Size").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.window_size = tk.IntVar(value=7)
        ttk.Spinbox(features_frame, from_=3, to=21, increment=2, textvariable=self.window_size, width=5).grid(
            row=0, column=1, padx=5, pady=5, sticky=tk.W
        )

        ttk.Label(features_frame, text="Hydrophobicity Scale").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.scale_choice = tk.StringVar(value="Kyte-Doolittle")
        ttk.Combobox(
            features_frame,
            values=["Kyte-Doolittle", "Hopp-Woods", "Eisenberg"],
            textvariable=self.scale_choice,
            width=18,
            state="readonly",
        ).grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)

        ttk.Label(features_frame, text="Smoothing").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.smoothing = tk.DoubleVar(value=0.5)
        ttk.Scale(features_frame, from_=0, to=1, orient=tk.HORIZONTAL, variable=self.smoothing).grid(
            row=1, column=1, columnspan=3, sticky="we", padx=5, pady=5
        )

        advanced_frame = ttk.LabelFrame(frame, text="Advanced Controls")
        advanced_frame.pack(fill=tk.X, padx=10, pady=8)

        ttk.Label(advanced_frame, text="Confidence Threshold").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.conf_threshold = tk.DoubleVar(value=0.55)
        ttk.Scale(advanced_frame, from_=0.2, to=0.95, orient=tk.HORIZONTAL, variable=self.conf_threshold).grid(
            row=0, column=1, padx=5, pady=5, sticky="we"
        )

        self.ensemble_enabled = tk.BooleanVar(value=True)
        self.noise_aug = tk.BooleanVar(value=False)
        ttk.Checkbutton(advanced_frame, text="Enable Ensemble Voting", variable=self.ensemble_enabled).grid(
            row=1, column=0, padx=5, pady=5, sticky=tk.W
        )
        ttk.Checkbutton(advanced_frame, text="Noise Augmentation", variable=self.noise_aug).grid(
            row=1, column=1, padx=5, pady=5, sticky=tk.W
        )

        training_frame = ttk.LabelFrame(frame, text="Training Options")
        training_frame.pack(fill=tk.X, padx=10, pady=8)

        ttk.Label(training_frame, text="Training Split (%)").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.training_split = tk.IntVar(value=80)
        ttk.Spinbox(training_frame, from_=50, to=90, increment=5, textvariable=self.training_split, width=5).grid(
            row=0, column=1, padx=5, pady=5, sticky=tk.W
        )
        ttk.Button(training_frame, text="Load Training Data...", command=self._not_implemented).grid(
            row=0, column=2, padx=10, pady=5
        )

        ttk.Label(training_frame, text="Cross-Validation Folds").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Spinbox(training_frame, from_=3, to=10, width=5).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        action_frame = ttk.Frame(frame)
        action_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(action_frame, text="Run Predictions", command=self._handle_run_predictions).pack(side=tk.LEFT)
        ttk.Button(action_frame, text="Compare Models", command=self._not_implemented).pack(side=tk.LEFT, padx=10)
        ttk.Button(action_frame, text="Reset", command=self._reset_predictions).pack(side=tk.LEFT)

        log_frame = ttk.LabelFrame(frame, text="Pipeline Log")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.log_text = tk.Text(log_frame, height=8, state=tk.DISABLED, background="#111", foreground="#0f0")
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _build_results_tab(self) -> None:
        frame = ttk.Frame(self.nb)
        self.nb.add(frame, text="Results")

        summary_frame = ttk.LabelFrame(frame, text="Summary")
        summary_frame.pack(fill=tk.X, padx=10, pady=10)
        self.summary_var = tk.StringVar(value="No predictions yet.")
        ttk.Label(summary_frame, textvariable=self.summary_var).pack(side=tk.LEFT, padx=10, pady=5)

        inner_nb = ttk.Notebook(frame)
        inner_nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        table_frame = ttk.Frame(inner_nb)
        inner_nb.add(table_frame, text="Residue Predictions")
        columns = ("Position", "Residue", "Model", "Prediction", "Confidence")
        self.results_table = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        for col in columns:
            self.results_table.heading(col, text=col)
            self.results_table.column(col, stretch=True, width=110)
        self.results_table.pack(fill=tk.BOTH, expand=True)

        model_frame = ttk.Frame(inner_nb)
        inner_nb.add(model_frame, text="Model Comparison")
        model_cols = ("Model", "Accuracy", "Precision", "Recall", "Notes")
        self.model_summary_table = ttk.Treeview(model_frame, columns=model_cols, show="headings", height=8)
        for col in model_cols:
            self.model_summary_table.heading(col, text=col)
            self.model_summary_table.column(col, stretch=True, width=120)
        self.model_summary_table.pack(fill=tk.BOTH, expand=True)

        profile_frame = ttk.Frame(inner_nb)
        inner_nb.add(profile_frame, text="Feature Profiles")
        self.feature_profile_table = ttk.Treeview(
            profile_frame, columns=("Index", "Hydrophobicity", "Polarity", "Mol Weight"), show="headings", height=10
        )
        for col in ("Index", "Hydrophobicity", "Polarity", "Mol Weight"):
            self.feature_profile_table.heading(col, text=col)
            self.feature_profile_table.column(col, anchor=tk.CENTER, width=120)
        self.feature_profile_table.pack(fill=tk.BOTH, expand=True)

        ttk.Button(frame, text="Export...", command=self._handle_export_results).pack(pady=5)

    def _build_visualization_tab(self) -> None:
        frame = ttk.Frame(self.nb)
        self.nb.add(frame, text="Visualization")

        preview_frame = ttk.LabelFrame(frame, text="Color-Coded Sequence Preview")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.sequence_preview = tk.Text(preview_frame, height=8, state=tk.DISABLED, font=("Courier", 10))
        self.sequence_preview.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        for tag, color in (("helix", "#f44336"), ("sheet", "#2196f3"), ("coil", "#4caf50")):
            self.sequence_preview.tag_configure(tag, foreground=color, font=("Courier", 10, "bold"))

        dist_frame = ttk.LabelFrame(frame, text="Distribution Overview")
        dist_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.distribution_table = ttk.Treeview(dist_frame, columns=("State", "Percent"), show="headings", height=5)
        self.distribution_table.heading("State", text="State")
        self.distribution_table.heading("Percent", text="Percent")
        self.distribution_table.column("State", anchor=tk.CENTER, width=120)
        self.distribution_table.column("Percent", anchor=tk.CENTER, width=120)
        self.distribution_table.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        ttk.Button(frame, text="Save Visualization Snapshot...", command=self._not_implemented).pack(pady=5)

    def _build_about_tab(self) -> None:
        frame = ttk.Frame(self.nb)
        self.nb.add(frame, text="About")
        text = tk.Text(frame, wrap=tk.WORD, height=20)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert(
            tk.END,
            (
                "Protein Secondary Structure Predictor\n\n"
                "Frontend Status:\n"
                "- Rich five-tab layout with diagnostics, advanced prediction controls,\n"
                "  model comparison, feature inspection, and visualization previews ready.\n"
                "- All export actions and workflows have dedicated hooks.\n\n"
                "Next Backend Tasks:\n"
                "1. Integrate UniProt REST API via ProteinDataRetriever.\n"
                "2. Implement FeatureExtractor for hydrophobicity, polarity, and related descriptors.\n"
                "3. Wire RuleBasedPredictor, DecisionTreePredictor, and NaiveBayesPredictor to trained models.\n"
                "4. Generate matplotlib plots via Visualizer and embed with FigureCanvasTkAgg.\n"
                "5. Implement ResultsExporter for CSV/JSON/report/PDB outputs.\n"
            ),
        )
        text.configure(state=tk.DISABLED)

    # --------------------------- Event handlers ---------------------------
    def _handle_uniprot_fetch(self) -> None:
        uniprot_id = self.uniprot_entry.get().strip()
        try:
            sequence = self.backend.fetch_sequence(uniprot_id)
        except ValueError as exc:
            messagebox.showerror("Input Error", str(exc))
            return
        except Exception as exc:  # pragma: no cover - placeholder branch
            messagebox.showerror("Fetch Error", f"Failed to fetch sequence: {exc}")
            return
        self._apply_sequence(sequence, f"UniProt {uniprot_id or '(mock)'}")

    def _handle_fasta_upload(self) -> None:
        path = filedialog.askopenfilename(
            title="Select FASTA File",
            filetypes=[("FASTA files", "*.fasta *.fa *.faa"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as handle:
                content = handle.read()
            sequence = self.backend.parse_fasta(content)
        except (OSError, ValueError) as exc:
            messagebox.showerror("File Error", str(exc))
            return
        self.sequence_text.delete("1.0", tk.END)
        self.sequence_text.insert(tk.END, sequence)
        self._apply_sequence(sequence, f"FASTA {path}")

    def _apply_manual_sequence(self, source: str) -> None:
        sequence = self.sequence_text.get("1.0", tk.END).strip().replace("\n", "")
        if not sequence:
            messagebox.showwarning("Sequence Missing", "Please enter a sequence.")
            return
        self._apply_sequence(sequence, source)

    def _insert_example_sequence(self) -> None:
        selection = self.example_list.curselection()
        if not selection:
            messagebox.showinfo("Select Example", "Please select an example sequence.")
            return
        name = self.example_list.get(selection[0])
        sequence = self.backend.load_example(name)
        self.sequence_text.delete("1.0", tk.END)
        self.sequence_text.insert(tk.END, sequence)
        self._apply_sequence(sequence, f"Example: {name}")

    def _handle_run_predictions(self) -> None:
        sequence = self.sequence_var.get()
        if not sequence:
            messagebox.showwarning("Sequence Missing", "Load or enter a sequence first.")
            return
        selected_models = [name for name, var in self.model_vars.items() if var.get()]
        if not selected_models:
            messagebox.showwarning("No Models", "Select at least one prediction model.")
            return

        self._log("Starting prediction pipeline...")
        self.progress_var.set(10)
        config = {
            "window_size": self.window_size.get(),
            "scale": self.scale_choice.get(),
            "smoothing": self.smoothing.get(),
            "confidence_threshold": self.conf_threshold.get(),
            "ensemble": self.ensemble_enabled.get(),
            "noise_aug": self.noise_aug.get(),
        }
        self.after(
            200,
            lambda: self._execute_predictions(sequence=sequence, models=selected_models, config=config),
        )

    def _execute_predictions(self, sequence: str, models: Sequence[str], config: Dict[str, object]) -> None:
        try:
            result = self.backend.run_predictions(sequence, models, config)
        except ValueError as exc:
            messagebox.showerror("Prediction Error", str(exc))
            self._log(f"Error: {exc}")
            return

        self.prediction_result = result
        self.progress_var.set(70)
        self._refresh_results_views(result)
        self.progress_var.set(100)
        self._log("Prediction pipeline completed.")
        self.nb.select(2)
        self.status_var.set("Predictions complete (placeholder data).")

    def _refresh_results_views(self, result: PredictionResult) -> None:
        self.results_table.delete(*self.results_table.get_children())
        for record in result.residues:
            self.results_table.insert(
                "",
                tk.END,
                values=(record.position, record.residue, record.model, record.state, record.confidence),
            )

        self.model_summary_table.delete(*self.model_summary_table.get_children())
        for summary in result.model_summaries:
            self.model_summary_table.insert(
                "",
                tk.END,
                values=(summary.name, summary.accuracy, summary.precision, summary.recall, summary.notes),
            )

        self.feature_profile_table.delete(*self.feature_profile_table.get_children())
        for idx, values in enumerate(
            itertools.zip_longest(
                result.feature_profile.hydrophobicity,
                result.feature_profile.polarity,
                result.feature_profile.molecular_weight,
                fillvalue="",
            ),
            start=1,
        ):
            hydro, pol, weight = values
            if idx > 25:
                self.feature_profile_table.insert("", tk.END, values=("...", "...", "...", "..."))
                break
            self.feature_profile_table.insert("", tk.END, values=(idx, hydro, pol, weight))

        summary_text = ", ".join(f"{state}: {pct}%" for state, pct in result.distribution.items())
        self.summary_var.set(summary_text)

        payload = self.visualizer.build_visual_payload(result)
        self._render_sequence_preview(result.residues)
        self._render_distribution(payload["distribution"])

    def _render_sequence_preview(self, residues: Sequence) -> None:  # type: ignore[arg-type]
        self.sequence_preview.configure(state=tk.NORMAL)
        self.sequence_preview.delete("1.0", tk.END)
        tag_map = {"α-Helix": "helix", "β-Sheet": "sheet", "Coil": "coil"}
        for record in residues[:400]:
            tag = tag_map.get(record.state, "")
            self.sequence_preview.insert(tk.END, record.residue, tag)
        if len(residues) > 400:
            self.sequence_preview.insert(tk.END, "...", "")
        self.sequence_preview.configure(state=tk.DISABLED)

    def _render_distribution(self, distribution: Dict[str, float]) -> None:
        self.distribution_table.delete(*self.distribution_table.get_children())
        for state, pct in distribution.items():
            self.distribution_table.insert("", tk.END, values=(state, pct))

    def _handle_export_results(self) -> None:
        if not self.prediction_result:
            messagebox.showinfo("No Data", "Run a prediction before exporting.")
            return
        payloads = self.backend.export_payloads(self.prediction_result)
        info = (
            "CSV Preview:\n"
            f"{payloads['csv'][:200]}...\n\n"
            "JSON Preview:\n"
            f"{payloads['json'][:200]}...\n\n"
            "Report Preview:\n"
            f"{payloads['report'][:200]}..."
        )
        messagebox.showinfo("Export Preview", info)

    def _reset_predictions(self) -> None:
        self.sequence_var.set("")
        self.sequence_text.delete("1.0", tk.END)
        self.prediction_result = None
        self.results_table.delete(*self.results_table.get_children())
        self.model_summary_table.delete(*self.model_summary_table.get_children())
        self.feature_profile_table.delete(*self.feature_profile_table.get_children())
        self.sequence_preview.configure(state=tk.NORMAL)
        self.sequence_preview.delete("1.0", tk.END)
        self.sequence_preview.configure(state=tk.DISABLED)
        self.distribution_table.delete(*self.distribution_table.get_children())
        self.summary_var.set("No predictions yet.")
        self.progress_var.set(0)
        self._log("State reset.")
        self.status_var.set("Reset complete.")

    def _apply_sequence(self, sequence: str, source_label: str) -> None:
        self.sequence_var.set(sequence)
        self.sequence_source_var.set(source_label)
        info = self.backend.describe_sequence(sequence)
        self.sequence_length_var.set(str(info["length"]))
        self.sequence_valid_var.set("Yes" if info["is_valid"] else "Check letters")
        self._refresh_composition_table(info["composition"])
        self.status_var.set(f"Sequence loaded from {source_label}.")

    def _refresh_composition_table(self, composition: Dict[str, float]) -> None:
        self.composition_table.delete(*self.composition_table.get_children())
        for residue, pct in sorted(composition.items()):
            self.composition_table.insert("", tk.END, values=(residue, pct))

    def _log(self, message: str) -> None:
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _open_about_popup(self) -> None:
        messagebox.showinfo(
            "About",
            "Protein Secondary Structure Predictor (Frontend Prototype)\n"
            "Backend integrations will be added in upcoming iterations.",
        )

    def _not_implemented(self) -> None:
        messagebox.showinfo("Coming Soon", "This feature will be implemented with the backend.")


def build_app() -> ProteinStructureApp:
    """Factory so other modules can create the Tk application."""
    return ProteinStructureApp()

