import os
import sys
import argparse
import math
import psutil

from stats.generator_stats import GeneratorStats
from create_figures import create_figures

def compute_max_workers_dynamic(ram_per_worker_mb=512, max_ram_usage=0.75, cpu_factor=0.75, max_workers=None):
    """
    Computes the number of parallel processes based on real-time available RAM and CPU cores.

    Parameters:
    - ram_per_worker_mb: Estimated RAM per process in MB (default is 512 MB).
    - max_ram_usage: Maximum proportion of RAM to use (0.75 = 75% of total RAM).
    - cpu_factor: Proportion of CPUs to use (0.75 = 75% of the CPU cores).

    Returns:
    - Integer number of safe workers to use in parallelization.
    """
    # If the user specifies a number, use it
    if not max_workers is None:
        return max_workers

    # Get real-time memory info
    memory = psutil.virtual_memory()
    available_ram = memory.available  # Only the available RAM (free memory)

    # Limit the RAM to use (no more than 75% of available RAM)
    available_ram_for_workers = available_ram * max_ram_usage

    # Estimate how much RAM each worker process will need (in bytes)
    ram_per_worker = ram_per_worker_mb * 1024 ** 2

    # Calculate the maximum number of processes that can be run without exceeding the available RAM
    max_by_ram = int(available_ram_for_workers // ram_per_worker)

    # Get the number of available CPUs and compute the limit based on CPUs
    available_cpus = os.cpu_count()
    max_by_cpu = int(available_cpus * cpu_factor)

    # The final number of workers will be the minimum between the RAM limit and the CPU limit
    final_max_workers = max(1, min(max_by_ram, max_by_cpu))

    return final_max_workers

def make_dir(dir_name):
    try:
        os.makedirs(dir_name)
        print(f"\nDirectory '{dir_name}' created successfully.")
    except FileExistsError:
        print(f"\nWARNING: Directory '{dir_name}' already exists.")
    except PermissionError:
        print(f"\nERROR: Permission denied: Unable to create '{dir_name}'.")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate the levels contained in the folder \"levels\".")
    parser.add_argument("--continue_evaluation", action='store_true', help="Continue a previous evaluation using the stats files from each set of levels.")
    parser.add_argument("--do_not_use_parallelization", action='store_true', help="Deactivate the parallelization.")
    parser.add_argument("--max_workers", type=int, default=None, help="Set the maximum number of workers to use in the parallelization.")
    parser.add_argument("--create_figures", action='store_true', help="Create the figures for the evaluation.")
    args = parser.parse_args()

    use_parallelization = False if args.do_not_use_parallelization else True
    if use_parallelization:
        if not args.max_workers is None:
            print(f"Number of max workers in parallelization asked by user: {args.max_workers}")

        max_workers = compute_max_workers_dynamic(max_workers = args.max_workers)
        print(f"Number of max workers used for safety in parallelization: {max_workers}")
    else:
        max_workers = None

    # Create the output folder for initial stats (raw characteristics, content diversity and A* diversity)
    output_folder_initial_stats = "initial_stats"
    make_dir(output_folder_initial_stats)

    # Create the output folder for intermediate stats (normalized characteristics but raw general metrics)
    output_folder_intermediate_stats = "intermediate_stats"
    make_dir(output_folder_intermediate_stats)

    # Create the output folder for the normalized stats (every information is normalized now)
    output_folder_final_stats = "final_stats"
    make_dir(output_folder_final_stats)

    input_folder = "levels" # Folder where the different folders of levels are stored
    levels_folders = [folder for folder in os.listdir(input_folder) if os.path.isdir(os.path.join(input_folder, folder))]

    all_stats = []

    if args.continue_evaluation:
        stats_files = [f for f in os.listdir(output_folder_initial_stats) if f.endswith(".csv")]
        for stats_file in stats_files:
            print("\nLoading stats from " + stats_file + "...")

            generator_stats = GeneratorStats(os.path.join(output_folder_initial_stats, stats_file), use_parallelization, max_workers)

            if generator_stats.ignore:
                continue

            all_stats.append(generator_stats)

            print("Stats loaded successfully for generator " + generator_stats.generator_name + ".")

    folders_already_evaluated = [generator_stats.folder_path for generator_stats in all_stats]

    for levels_folder in levels_folders:
        if args.continue_evaluation and os.path.join(input_folder, levels_folder) in folders_already_evaluated:
            continue

        generator_stats = GeneratorStats(os.path.join(input_folder, levels_folder), use_parallelization, max_workers)

        if generator_stats.ignore:
            continue

        # Add the generator stats to the list
        all_stats.append(generator_stats)

        generator_stats.save(output_folder_initial_stats, "_initial_stats")

    # Take the min and max values from characteristics of all generators stats, so that they can be normalized
    min_values = {}
    max_values = {}

    for generator_stats in all_stats:
        for level_stats in generator_stats.levels_stats:
            for stat, value in level_stats.characteristics.items():
                if math.isnan(value):
                    continue

                if stat not in min_values or value < min_values[stat]:
                    min_values[stat] = value
                if stat not in max_values or value > max_values[stat]:
                    max_values[stat] = value

    #print(f"\nMin values: {min_values}")
    #print(f"\nMax values: {max_values}")

    # Normalize the generators stats except the diversity values and compute the coverage
    for generator_stats in all_stats:
        generator_stats.normalize_characteristics(min_values, max_values)
        generator_stats.compute_coverage()
        generator_stats.save(output_folder_intermediate_stats, "_intermediate_stats")

    # Take the min and max values from all diversity values, so that they can be normalized
    min_content_diversity = min([generator_stats.content_diversity for generator_stats in all_stats])
    max_content_diversity = max([generator_stats.content_diversity for generator_stats in all_stats])
    min_a_star_diversity = min([generator_stats.a_star_diversity for generator_stats in all_stats])
    max_a_star_diversity = max([generator_stats.a_star_diversity for generator_stats in all_stats])
    min_coverage = min([generator_stats.coverage for generator_stats in all_stats])
    max_coverage = max([generator_stats.coverage for generator_stats in all_stats])

    '''print("\nMin content diversity: " + str(min_content_diversity))
    print("Max content diversity: " + str(max_content_diversity))
    print("Min A* diversity: " + str(min_a_star_diversity))
    print("Max A* diversity: " + str(max_a_star_diversity))
    print("Min coverage: " + str(min_coverage))
    print("Max coverage: " + str(max_coverage))'''

    # Normalize the diversity values and save the normalized stats
    for i, generator_stats in enumerate(all_stats):
        generator_stats.normalize_diversity(min_content_diversity, max_content_diversity, min_a_star_diversity, max_a_star_diversity, min_coverage, max_coverage)

        # Save the generator stats
        generator_stats.save(output_folder_final_stats, "_final_stats")

    print("\nEvaluation finished successfully.")

    if args.create_figures:
        create_figures(all_stats)
    else:
        print("\nWARNING: Figures not created. Use --create_figures to create them.")

    print("\nProgram finished successfully.")