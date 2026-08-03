import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src" / "parser"))
from fjsp_parser import parse_fjsp_file
from decoder import decode, random_feasible_chromosome


def validate_schedule(instance, schedule):
    """Raises AssertionError if precedence or machine-capacity is violated."""
    # 1. Precedence: within a job, op_index k must start no earlier than op k-1 ends
    by_job = {}
    for entry in schedule:
        by_job.setdefault(entry["job"], []).append(entry)
    for job_id, entries in by_job.items():
        entries.sort(key=lambda e: e["op_index"])
        for i in range(1, len(entries)):
            assert entries[i]["start"] >= entries[i - 1]["end"], (
                f"Precedence violated in job {job_id}: "
                f"op {entries[i]['op_index']} starts before op {entries[i-1]['op_index']} ends"
            )
        # every operation of the job must appear exactly once
        assert len(entries) == len(instance.jobs[job_id]), "missing/duplicate operation"

    # 2. Machine capacity: no two operations overlap on the same machine
    by_machine = {}
    for entry in schedule:
        by_machine.setdefault(entry["machine"], []).append(entry)
    for machine, entries in by_machine.items():
        entries.sort(key=lambda e: e["start"])
        for i in range(1, len(entries)):
            assert entries[i]["start"] >= entries[i - 1]["end"], (
                f"Machine {machine} double-booked"
            )

    # 3. Machine eligibility: each operation actually runs on an eligible machine
    for entry in schedule:
        op = instance.jobs[entry["job"]][entry["op_index"]]
        assert entry["machine"] in op.eligible, "assigned to ineligible machine"
        assert entry["end"] - entry["start"] == op.eligible[entry["machine"]], "wrong duration"

    return True


def hill_climb(instance, seq, asg, rng, iterations=500):
    """Simple local search: repeatedly try a random single-operation
    reassignment or a random swap in the sequence; keep it if it improves
    makespan. Just for sanity-checking the decoder, not the real GA."""
    best_makespan, _ = decode(instance, seq, asg)
    seq, asg = list(seq), dict(asg)
    for _ in range(iterations):
        new_seq, new_asg = list(seq), dict(asg)
        if rng.random() < 0.5:
            i, j = rng.sample(range(len(new_seq)), 2)
            new_seq[i], new_seq[j] = new_seq[j], new_seq[i]
        else:
            job_id = rng.randrange(instance.num_jobs)
            op_index = rng.randrange(len(instance.jobs[job_id]))
            op = instance.jobs[job_id][op_index]
            new_asg[(job_id, op_index)] = rng.choice(list(op.eligible.keys()))
        try:
            new_makespan, _ = decode(instance, new_seq, new_asg)
        except ValueError:
            continue
        if new_makespan <= best_makespan:
            seq, asg, best_makespan = new_seq, new_asg, new_makespan
    return best_makespan, seq, asg


if __name__ == "__main__":
    inst = parse_fjsp_file(REPO_ROOT / "data-sample" / "kacem" / "k1.txt")
    KNOWN_OPTIMUM = 11

    rng = random.Random(0)
    best = float("inf")
    n_trials = 20000

    for _ in range(n_trials):
        seq, asg = random_feasible_chromosome(inst, rng)
        makespan, schedule = decode(inst, seq, asg)
        validate_schedule(inst, schedule)  # will raise if decoder is wrong
        if makespan < best:
            best = makespan

    print(f"[random search] best = {best}")
    print("Now hill-climbing from 50 random restarts...")
    hc_best = float("inf")
    for _ in range(50):
        seq, asg = random_feasible_chromosome(inst, rng)
        hc_makespan, hc_seq, hc_asg = hill_climb(inst, seq, asg, rng, iterations=1000)
        if hc_makespan < hc_best:
            hc_best = hc_makespan
    best = min(best, hc_best)
    print(f"[hill-climb] best = {hc_best}")

    print(f"Validated {n_trials} random chromosomes: no constraint violations.")
    print(f"Best makespan found by random search: {best}")
    print(f"Known optimum (from instances.json): {KNOWN_OPTIMUM}")
    if best == KNOWN_OPTIMUM:
        print("MATCH — decoder confirmed correct.")
    elif best <= KNOWN_OPTIMUM * 1.15:
        print("Close to optimum via pure random search — decoder looks correct "
              "(a real GA with crossover/mutation should close the remaining gap).")
    else:
        print("Gap is large — investigate decoder logic before proceeding.")
