"""
Standard Genetic Algorithm for the deterministic FJSP (no workers, no
uncertainty yet -- this is the Phase 2 baseline your proposal calls
"standard GA" in Table 4.5, used later to isolate the effect of FPC).

Chromosome = (sequence, assignment), same representation as decoder.py.
"""
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src" / "parser"))
from fjsp_parser import parse_fjsp_file
from decoder import decode, random_feasible_chromosome


def init_population(instance, pop_size, rng):
    return [random_feasible_chromosome(instance, rng) for _ in range(pop_size)]


def fitness(instance, chromosome):
    """Lower makespan = better. We return makespan directly and always
    take the minimum when comparing (rather than inverting to 1/makespan),
    it's equivalent and avoids division-by-zero edge cases."""
    seq, asg = chromosome
    makespan, _ = decode(instance, seq, asg)
    return makespan


def tournament_selection(population, fitnesses, k, rng):
    contestants = rng.sample(range(len(population)), k)
    best_idx = min(contestants, key=lambda i: fitnesses[i])
    return population[best_idx]


def order_crossover(seq1, seq2, rng):
    """OX crossover adapted for operation-based encoding: seq contains
    repeated job-ids (once per operation of that job), not a plain
    permutation of unique values, so we crossover by relative order of
    job-id occurrences rather than by raw values."""
    n = len(seq1)
    a, b = sorted(rng.sample(range(n), 2))

    child = [None] * n
    child[a:b] = seq1[a:b]

    # Walk seq2 in order, taking each job-id occurrence that's still needed
    # (i.e. not already placed in the child[a:b] slice), to fill the rest.
    from collections import Counter
    fill_values = []
    remaining = Counter(seq1)
    remaining.subtract(Counter(child[a:b]))
    for job in seq2:
        if remaining[job] > 0:
            fill_values.append(job)
            remaining[job] -= 1

    pos = 0
    for i in list(range(0, a)) + list(range(b, n)):
        child[i] = fill_values[pos]
        pos += 1

    return child


def assignment_crossover(asg1, asg2, rng):
    """Uniform crossover on the assignment vector: for each operation,
    inherit the machine choice from parent 1 or parent 2 at random.
    This is always feasible (machine-eligibility-wise) because each
    parent's choice for that operation is, by construction, eligible."""
    child = {}
    for key in asg1:
        child[key] = asg1[key] if rng.random() < 0.5 else asg2[key]
    return child


def swap_mutation(seq, rng, prob):
    seq = list(seq)
    if rng.random() < prob:
        i, j = rng.sample(range(len(seq)), 2)
        seq[i], seq[j] = seq[j], seq[i]
    return seq


def assignment_mutation(instance, asg, rng, prob):
    asg = dict(asg)
    for (job_id, op_index), machine in list(asg.items()):
        if rng.random() < prob:
            op = instance.jobs[job_id][op_index]
            asg[(job_id, op_index)] = rng.choice(list(op.eligible.keys()))
    return asg


def run_ga(instance, pop_size=50, generations=200, tournament_k=3,
           crossover_prob=0.8, mutation_prob=0.1, seed=0, verbose=True):
    rng = random.Random(seed)
    population = init_population(instance, pop_size, rng)
    fitnesses = [fitness(instance, ind) for ind in population]

    best_idx = min(range(pop_size), key=lambda i: fitnesses[i])
    best_chromosome = population[best_idx]
    best_fitness = fitnesses[best_idx]
    history = [best_fitness]

    for gen in range(generations):
        new_population = []
        # elitism: carry the single best individual over unchanged
        new_population.append(best_chromosome)

        while len(new_population) < pop_size:
            parent1 = tournament_selection(population, fitnesses, tournament_k, rng)
            parent2 = tournament_selection(population, fitnesses, tournament_k, rng)

            if rng.random() < crossover_prob:
                child_seq = order_crossover(parent1[0], parent2[0], rng)
                child_asg = assignment_crossover(parent1[1], parent2[1], rng)
            else:
                child_seq, child_asg = list(parent1[0]), dict(parent1[1])

            child_seq = swap_mutation(child_seq, rng, mutation_prob)
            child_asg = assignment_mutation(instance, child_asg, rng, mutation_prob)

            new_population.append((child_seq, child_asg))

        population = new_population
        fitnesses = [fitness(instance, ind) for ind in population]

        gen_best_idx = min(range(pop_size), key=lambda i: fitnesses[i])
        if fitnesses[gen_best_idx] < best_fitness:
            best_fitness = fitnesses[gen_best_idx]
            best_chromosome = population[gen_best_idx]

        history.append(best_fitness)
        if verbose and gen % 20 == 0:
            print(f"  gen {gen:4d}: best so far = {best_fitness}")

    return best_fitness, best_chromosome, history


if __name__ == "__main__":
    inst = parse_fjsp_file(REPO_ROOT / "data-sample" / "brandimarte" / "mk01.txt")
    print("Running standard GA on Brandimarte mk01 (known optimum = 40)...")
    best_fitness, best_chromosome, history = run_ga(
        inst, pop_size=80, generations=150, seed=0
    )
    print(f"Final best makespan: {best_fitness}")
