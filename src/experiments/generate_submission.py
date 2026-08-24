"""
Generate competition submission files.

Creates CSV files in the format required by the FJSSP-W-Competition.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import csv
import json
import glob
from datetime import datetime
from typing import Dict, List
import statistics

from parser.fjssp_w_parser import parse_competition_instance
from ga.fjssp_w.genetic_algorithm_w import FJSSPW_GA


def generate_submission_for_instance(
    instance_path: str,
    instance_name: str,
    population_size: int = 100,
    generations: int = 200,
    n_runs: int = 10,
    random_seed: int = 42
) -> Dict:
    """
    Generate competition submission data for a single instance.
    
    Returns:
        dict: Submission data
    """
    print(f"Processing: {instance_name}")
    
    # Load instance
    instance_data = parse_competition_instance(instance_path)
    n_operations = instance_data['n_operations']
    
    all_runs = []
    best_makespans = []
    
    for run in range(n_runs):
        seed = random_seed + run
        
        # Create GA
        ga = FJSSPW_GA(
            instance_data,
            population_size=population_size,
            generations=generations,
            random_seed=seed
        )
        
        # Run GA
        result = ga.evolve()
        schedule = ga.get_best_schedule()
        
        # Convert numpy types to Python floats
        makespan = float(result['best_makespan'])
        best_makespans.append(makespan)
        
        all_runs.append({
            'run': run + 1,
            'makespan': makespan,
            'start_times': [float(x) for x in schedule['start_times']],
            'end_times': [float(x) for x in schedule['end_times']],
            'machine_assignment': [int(x) for x in schedule['machine_assignment']],
            'worker_assignment': [int(x) for x in schedule['worker_assignment']],
            'evaluations': generations * population_size
        })
    
    # Calculate statistics (now all are Python floats)
    avg_makespan = sum(best_makespans) / len(best_makespans)
    best_makespan = min(best_makespans)
    worst_makespan = max(best_makespans)
    
    # Calculate standard deviation manually
    if len(best_makespans) > 1:
        variance = sum((x - avg_makespan) ** 2 for x in best_makespans) / (len(best_makespans) - 1)
        std_makespan = variance ** 0.5
    else:
        std_makespan = 0.0
    
    # Find best run
    best_run = min(all_runs, key=lambda x: x['makespan'])
    
    return {
        'instance': instance_name,
        'best_makespan': best_makespan,
        'avg_makespan': avg_makespan,
        'worst_makespan': worst_makespan,
        'std_makespan': std_makespan,
        'n_runs': n_runs,
        'best_run': best_run,
        'all_runs': all_runs
    }


def generate_submission_csv(results: List[Dict], output_file: str):
    """
    Generate competition submission CSV file.
    
    Format required by competition:
    instance,run,best_makespan,start_times,machine_assignments,worker_assignments
    """
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'instance', 'run', 'makespan', 'evaluations',
            'start_times', 'machine_assignments', 'worker_assignments'
        ])
        
        for result in results:
            for run_data in result['all_runs']:
                writer.writerow([
                    result['instance'],
                    run_data['run'],
                    run_data['makespan'],
                    run_data['evaluations'],
                    ';'.join(str(x) for x in run_data['start_times']),
                    ';'.join(str(x) for x in run_data['machine_assignment']),
                    ';'.join(str(x) for x in run_data['worker_assignment'])
                ])
    
    print(f"Submission CSV saved to: {output_file}")


def generate_submission_json(results: List[Dict], output_file: str):
    """
    Generate competition submission JSON file.
    """
    output = []
    
    for result in results:
        best_run = result['best_run']
        output.append({
            'instance': result['instance'],
            'best_makespan': result['best_makespan'],
            'avg_makespan': result['avg_makespan'],
            'std_makespan': result['std_makespan'],
            'n_runs': result['n_runs'],
            'best_run': {
                'run': best_run['run'],
                'makespan': best_run['makespan'],
                'evaluations': best_run['evaluations'],
                'start_times': best_run['start_times'],
                'machine_assignments': best_run['machine_assignment'],
                'worker_assignments': best_run['worker_assignment']
            }
        })
    
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"Submission JSON saved to: {output_file}")


def main():
    """Generate submission files for competition."""
    print("=" * 60)
    print("FJSSP-W COMPETITION SUBMISSION GENERATOR")
    print("=" * 60)
    
    # Use first 3 instances for quick submission
    instance_dir = "../FJSSP-W-Competition/instances/fjssp-w"
    instance_files = glob.glob(os.path.join(instance_dir, "*.fjs"))[:3]
    
    if not instance_files:
        print(f"No .fjs files found in {instance_dir}")
        return
    
    print(f"Generating submission for {len(instance_files)} instances")
    print(f"  - {', '.join(os.path.basename(f) for f in instance_files)}")
    print()
    
    results = []
    
    for instance_path in instance_files:
        instance_name = os.path.basename(instance_path)
        
        result = generate_submission_for_instance(
            instance_path,
            instance_name,
            population_size=50,
            generations=30,
            n_runs=3,
            random_seed=42
        )
        results.append(result)
        
        print(f"  {instance_name}: Best={result['best_makespan']:.1f}, Avg={result['avg_makespan']:.1f}")
    
    # Generate submission files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    csv_file = f"results/wfu/submission_{timestamp}.csv"
    json_file = f"results/wfu/submission_{timestamp}.json"
    
    generate_submission_csv(results, csv_file)
    generate_submission_json(results, json_file)
    
    print("\n" + "=" * 60)
    print("SUBMISSION GENERATION COMPLETE")
    print("=" * 60)
    print(f"CSV: {csv_file}")
    print(f"JSON: {json_file}")
    print("\nFiles are ready for competition submission!")


if __name__ == "__main__":
    main()