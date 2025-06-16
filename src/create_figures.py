import os
import sys
import json

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from great_tables import GT

from stats.generator_stats import GeneratorStats

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

def make_evaluation(stats, evaluation_info, output_folder):
    evaluation_name = evaluation_info["name"]
    generators_names = evaluation_info["generators"]

    # Create the output folder
    make_dir(os.path.join(output_folder, evaluation_name))

    evaluation_stats = []
    for name in generators_names:
        for stat in stats:
            if stat.generator_name == name:
                evaluation_stats.append(stat)
                break

    average_times = [stat.average_generation_time() for stat in evaluation_stats]
    no_visual_bugs_percentages = [stat.no_visual_bugs_percentage() for stat in evaluation_stats]
    valid_percentages = [stat.valid_percentage() for stat in evaluation_stats]
    content_diversities = [stat.content_diversity for stat in evaluation_stats]
    a_star_diversities = [stat.a_star_diversity for stat in evaluation_stats]
    coverages = [stat.coverage for stat in evaluation_stats]
    
    # Create a table with the results per rows
    # First, create the pandas DataFrame
    show_times = True
    if any([time is None for time in average_times]):
        show_times = False
    
    if show_times:
        data = {"Generator" : generators_names, \
                "Average generation time (s)" : average_times, \
                "No visual bugs percentage" : no_visual_bugs_percentages, \
                "Valid percentage" : valid_percentages, \
                "Content diversity" : content_diversities, \
                "A* diversity" : a_star_diversities, \
                "Coverage" : coverages}
    else:
        data = {"Generator" : generators_names, \
                "No visual bugs percentage" : no_visual_bugs_percentages, \
                "Valid percentage" : valid_percentages, \
                "Content diversity" : content_diversities, \
                "A* diversity" : a_star_diversities, \
                "Coverage" : coverages}
    df = pd.DataFrame(data)

    # Create the table
    if show_times:
        content_columns = ["Average generation time (s)", "No visual bugs percentage", "Valid percentage", "Content diversity", "A* diversity", "Coverage"]
    else:
        content_columns = ["No visual bugs percentage", "Valid percentage", "Content diversity", "A* diversity", "Coverage"]
    gt = GT(df)
    gt = gt.tab_header(evaluation_name)
    gt = gt.fmt_number(decimals=4, columns=content_columns)
    gt = gt.cols_align(align = "center", columns = content_columns)

    # Store the table in a file
    table = gt.as_latex()
    with open(os.path.join(output_folder, evaluation_name, "table.txt"), 'w') as file:
        file.write(table)

    # Compute the normalized generation speed if generation time is present
    if show_times:
        min_time = min(average_times)
        relative_speed = [min_time / time for time in average_times]

    # Create the data for the grouped plot (with normalized generation speed)
    if show_times:
        data = {"Generator" : generators_names, \
                "Velocidad de\ngeneración" : relative_speed, \
                "Proporción de\nniveles sin bugs" : no_visual_bugs_percentages, \
                "Fiabilidad" : valid_percentages, \
                "Diversidad de\ncontenido" : content_diversities, \
                "Diversidad A*" : a_star_diversities, \
                "Coverage" : coverages}
    else:
        data = {"Generador" : generators_names, \
                "Proporción de\nniveles sin bugs" : no_visual_bugs_percentages, \
                "Fiabilidad" : valid_percentages, \
                "Diversidad de\ncontenido" : content_diversities, \
                "Diversidad A*" : a_star_diversities, \
                "Coverage" : coverages}
    df = pd.DataFrame(data)
    df = df.set_index("Generator")
    df = df.transpose()

    # Set the number of generators and the number of stats
    n_generators = len(generators_names)
    n_stats = 6 if show_times else 5

    # Define the bar positions
    x = np.arange(n_stats) * 1.2
    width = 0.15

    # Plot the grouped bars
    fig, ax = plt.subplots(figsize=(n_stats * 3, n_stats * 1.2))

    # Define hatch patterns for each generator
    hatch_patterns = ['/', '\\', '|', '-', '+', 'x', 'o', 'O', '.', '*']

    # Iterate over each generator
    for i in range(n_generators):
        ax.bar(x + i * width, df.iloc[:, i], width=width, label=generators_names[i], hatch=hatch_patterns[i % len(hatch_patterns)])

    # Set x-axis labels
    ax.set_xticks(x + (width * (n_generators - 1)) / 2)
    ax.set_xticklabels(df.index)

    # Labels, title and legend
    #ax.set_ylabel("Value", fontsize=14)
    #ax.set_title(f"{evaluation_name} visual comparison", fontsize=20, pad=20)  # Add padding to the title
    ax.legend(title="Generador", fontsize=20, title_fontsize=22, loc="upper center", bbox_to_anchor=(0.485, -0.28), ncol=2)
    #ax.legend(title="Generador", fontsize=18, title_fontsize=20, loc='lower center', bbox_to_anchor=(0.5, -0.15), ncol=3)
    plt.subplots_adjust(bottom=0.46, left=0.05, right=0.97, top=0.95)
    
    # Increase font size of x-axis labels
    ax.tick_params(axis='x', labelsize=20, pad=8)
    ax.tick_params(axis='y', labelsize=14)
    
    #plt.tight_layout()

    # Save the plot
    plt.savefig(os.path.join(output_folder, evaluation_name, "grouped_plot.eps"), format='eps')

def create_figures(all_stats):
    print("\nCreating figures...")

    # Create the output folder
    output_folder = "figures"
    make_dir(output_folder)

    input_folder = "evaluations" # Folder where the desired evaluations are established

    # Load necessary stats for each evaluation
    evaluation_files = [file for file in os.listdir(input_folder) if file.endswith(".json")]
    for file in evaluation_files:
        with open(os.path.join(input_folder, file), 'r') as f:
            evaluation_info = json.load(f)
        
        make_evaluation(all_stats, evaluation_info, output_folder)

    print("\nFigures created successfully.")
