# FJSP Genetic Algorithm Baseline

This repository contains a small Python implementation for parsing Flexible Job
Shop Scheduling Problem (FJSP) instances and running a baseline genetic
algorithm on the Brandimarte benchmark set.

## Repository Layout

- `src/parser/` - parser for FJSPLib-style instance files.
- `src/ga/` - decoder, schedule validation helpers, and the genetic algorithm.
- `src/experiments/` - runnable experiment scripts.
- `data-sample/` - bundled benchmark data and metadata.
- `results/` - generated experiment outputs.

## Requirements

- Python 3.10 or newer

The current code only uses the Python standard library, so there are no package
dependencies to install.

## Run The Baseline Experiment

From the repository root:

```bash
python3 src/experiments/run_baseline.py
```

The script runs the genetic algorithm on the Brandimarte `mk01` to `mk15`
instances and writes:

```text
results/phase2_brandimarte_baseline.csv
```

## Run Individual Checks

Run the GA on `mk01`:

```bash
python3 src/ga/genetic_algorithm.py
```

Run the decoder sanity check on the Kacem `k1` instance:

```bash
python3 src/ga/sanity_check.py
```

Parse a specific instance file:

```bash
python3 src/parser/fjsp_parser.py data-sample/brandimarte/mk01.txt
```

## Notes

Generated files such as virtual environments, Python cache files, and experiment
outputs are ignored by Git. Keep source code and benchmark input data under
version control.
