"""
Runs the standard GA on every Brandimarte instance and saves a results
table (instance, jobs, machines, known optimum/bound, GA best, gap %)
to a CSV file. This becomes your first real baseline results table.
"""
import sys
import json
import csv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src" / "parser"))
sys.path.insert(0, str(REPO_ROOT / "src" / "ga"))
from fjsp_parser import parse_fjsp_file
from genetic_algorithm import run_ga


def load_bounds(instances_json_path):
    """Returns {instance_name: optimum_or_upper_bound} from instances.json."""
    with open(instances_json_path) as f:
        data = json.load(f)
    bounds = {}
    for entry in data:
        name = entry.get("name")
        if entry.get("optimum") is not None:
            bounds[name] = entry["optimum"]
        elif entry.get("bounds"):
            bounds[name] = entry["bounds"]["upper"]  # best known upper bound
    return bounds


def main():
    bounds = load_bounds(REPO_ROOT / "data-sample" / "instances.json")

    instance_names = [f"mk{str(i).zfill(2)}" for i in range(1, 16)]
    results = []

    for name in instance_names:
        path = REPO_ROOT / "data-sample" / "brandimarte" / f"{name}.txt"
        try:
            inst = parse_fjsp_file(path)
        except FileNotFoundError:
            print(f"Skipping {name}: file not found")
            continue

        print(f"Running GA on {name} ({inst.num_jobs} jobs, {inst.num_machines} machines)...")
        best_fitness, _, _ = run_ga(
            inst, pop_size=80, generations=150, seed=0, verbose=False
        )

        known = bounds.get(name)
        gap_pct = None
        if known:
            gap_pct = round(100 * (best_fitness - known) / known, 1)

        results.append({
            "instance": name,
            "jobs": inst.num_jobs,
            "machines": inst.num_machines,
            "known_best": known,
            "ga_best": best_fitness,
            "gap_percent": gap_pct,
        })
        print(f"  -> GA best = {best_fitness}, known best = {known}, gap = {gap_pct}%")

    out_path = REPO_ROOT / "results" / "phase2_brandimarte_baseline.csv"
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["instance", "jobs", "machines", "known_best", "ga_best", "gap_percent"])
        writer.writeheader()
        writer.writerows(results)

    print(f"\nSaved results to {out_path}")


if __name__ == "__main__":
    main()
