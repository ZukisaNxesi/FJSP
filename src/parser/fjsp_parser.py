"""
Parser for the FJSPLib text format used by Brandimarte, Kacem and Hurink instances.

Format:
    Line 1: <num_jobs> <num_machines>
    One line per job:
        <num_ops>
        then, for each operation:
            <num_eligible_machines> (<machine_idx> <proc_time>) * num_eligible_machines
    Machine indices are 0-based in this file format.
"""
from dataclasses import dataclass, field


@dataclass
class Operation:
    job_id: int
    op_index: int          # position within the job (0-based)
    # eligible[machine_id] = processing_time
    eligible: dict = field(default_factory=dict)


@dataclass
class FJSPInstance:
    num_jobs: int
    num_machines: int
    jobs: list  # jobs[j] = list[Operation], in required processing order

    @property
    def num_operations(self) -> int:
        return sum(len(job) for job in self.jobs)


def parse_fjsp_file(path: str) -> FJSPInstance:
    with open(path, "r") as f:
        # Some files have trailing whitespace/blank lines; filter them out
        tokens = f.read().split()

    idx = 0

    def next_int():
        nonlocal idx
        val = int(tokens[idx])
        idx += 1
        return val

    num_jobs = next_int()
    num_machines = next_int()

    jobs = []
    for j in range(num_jobs):
        num_ops = next_int()
        operations = []
        for o in range(num_ops):
            num_eligible = next_int()
            eligible = {}
            for _ in range(num_eligible):
                m = next_int()
                t = next_int()
                eligible[m] = t
            operations.append(Operation(job_id=j, op_index=o, eligible=eligible))
        jobs.append(operations)

    return FJSPInstance(num_jobs=num_jobs, num_machines=num_machines, jobs=jobs)


if __name__ == "__main__":
    import sys
    inst = parse_fjsp_file(sys.argv[1] if len(sys.argv) > 1 else "../../data/fjsp-instances/kacem/k1.txt")
    print(f"Jobs: {inst.num_jobs}, Machines: {inst.num_machines}, Total ops: {inst.num_operations}")
    for j, ops in enumerate(inst.jobs):
        for op in ops:
            print(f"  Job {j} Op {op.op_index}: eligible = {op.eligible}")
