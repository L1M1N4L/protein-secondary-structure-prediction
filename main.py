"""Entry point for the Protein Secondary Structure Predictor frontend."""

from frontend import ProteinStructureApp


def main() -> None:
    app = ProteinStructureApp()
    app.mainloop()


if __name__ == "__main__":
    main()

