# Source reports

The raw source reports used in this study are public or published third-party documents. They are not redistributed in this repository.

Use `../source_manifest.csv` to download each report from its publisher and place it at the listed `local_path`. The manifest records the expected byte size and SHA-256 checksum for provenance verification. After the files are present, run `python src/validate_data.py` from the repository root before rebuilding the datasets.

The processed analytical datasets needed to inspect and reproduce the reported statistical analyses are included under `data/processed/`.
