import numpy as np
import pandas as pd
import os
import sys
import json
import ast
import Levenshtein
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from itertools import combinations
from tqdm import tqdm

from stats.games.registry import EVALUATOR_REGISTRY
from stats.level_stats import LevelStats
from stats.diversity_archive import DiversityArchive

def levenshtein_distance(pair):
    '''rows = len(sequence1) + 1
    cols = len(sequence2) + 1
    distances = [[0 for x in range(cols)] for x in range(rows)]

    for i in range(1, rows):
        distances[i][0] = i

    for i in range(1, cols):
        distances[0][i] = i
        
    for col in range(1, cols):
        for row in range(1, rows):
            if sequence1[row-1] == sequence2[col-1]:
                cost = 0
            else:
                cost = 1
            distances[row][col] = min(distances[row-1][col] + 1,    # deletion
                                distances[row][col-1] + 1,          # insertion
                                distances[row-1][col-1] + cost)     # substitution
    
    return distances[row][col]'''
    a, b = pair
    return Levenshtein.distance(a, b)

def evaluate_level(level_path, level, evaluator, parallelization):
    return evaluator.evaluate(level_path, level, parallelization)

class GeneratorStats:
    def __init__(self, path, parallelization, max_workers):
        self.folder_path = None
        self.generator_name = None
        self.game_name = None
        self.ignore = None
        self.n_intervals_per_dimension = None
        self.content_diversity = None
        self.a_star_diversity = None
        self.coverage = None
        self.levels_stats = []
        self.diversity_archive = None
        self.generation_times = None
        self.parallelization = parallelization
        self.max_workers = max_workers

        # Check if the path is a directory or a .csv file
        if os.path.isdir(path):
            self.load_from_folder(path)
        elif path.endswith('.csv'):
            self.load_from_csv(path)
        else:
            raise ValueError("Path must be a directory or a .csv file.")

    def load_from_folder(self, folder_path):
        print("\nEvaluating generator from " + folder_path + "...")

        # Check if the path is a directory
        if not os.path.isdir(folder_path):
            raise ValueError("Path must be a directory.")

        self.folder_path = folder_path

        # Search for properties.json in the folder
        properties_file = os.path.join(folder_path, "properties.json")
        if not os.path.exists(properties_file):
            raise FileNotFoundError(f"properties.json not found in {folder_path}")

        # Read the content of properties.json
        with open(properties_file, 'r') as f:
            properties = json.load(f)

        # Extract the parameter indicating if this levels folder should not be taken into account
        self.ignore = properties.get("Ignore", False)

        if self.ignore:
            print("WARNING: Ignoring generator from folder " + folder_path + "...")
            return

        # Extract the game name and the generator name
        try:
            self.game_name = properties["Game Name"]
            self.generator_name = properties["Generator Name"]
        except KeyError as e:
            raise KeyError(f"Missing item in properties.json: {e}")

        # Extract the parameter indicating the number of intervals per dimension for the coverage archive
        self.n_intervals_per_dimension = properties.get("Number of intervals per dimension", 10)

        # Search for times.csv in the folder
        times_file = os.path.join(folder_path, "times.csv")
        if os.path.exists(times_file):
            # Read the content of times.csv
            self.generation_times = pd.read_csv(times_file)

            if "level_name" not in self.generation_times.columns:
                raise ValueError("times.csv must contain a 'level_name' column.")
            if "generation_time" not in self.generation_times.columns:
                raise ValueError("times.csv must contain a 'generation_time' column.")
        else:
            print(f"\nWARNING: {times_file} not found in {folder_path}. Generation times will not be available.")

        # Create the diversity archive. It must represent a multidimensional grid with each feature as a dimension, and 10 points per dimension
        self.diversity_archive = DiversityArchive(self.n_intervals_per_dimension)

        self.evaluate_levels()

    def evaluate_levels(self):
        # Load the levels
        levels_paths = [os.path.join(self.folder_path, f) for f in os.listdir(self.folder_path) if f.endswith(".txt")]
        game_evaluator = EVALUATOR_REGISTRY[self.game_name]

        levels = []
        for level_path in levels_paths:
            # Read the level
            with open(level_path, "r") as f:
                level = f.read()
            
            levels.append(level)

        if len(levels_paths) != len(levels):
            print(f"ERROR: Different number of levels and files from generator {self.generator_name}. Exiting...")
            sys.exit(1)

        n_levels = len(levels_paths)
        desc = "Evaluating levels"

        if self.parallelization:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(evaluate_level, levels_paths[i], levels[i], game_evaluator, parallelization = True): levels_paths[i] for i in range(n_levels)}

                try:
                    for future in tqdm(as_completed(futures), total=len(futures), desc=desc, ncols=80):
                        stats = future.result()
                        self.add_level_stats(stats)
                except Exception as e:
                    print(f"Error detected: {e}. Exiting...")
                    executor.shutdown(wait=False, cancel_futures=True)
                    sys.exit(1)
        else:
            self.levels_stats = [game_evaluator.evaluate(levels_paths[i], levels[i], parallelization = False) for i in tqdm(range(n_levels), total=n_levels, desc=desc, ncols=80)]
            '''for i in range(n_levels):            
                print(f"\nEvaluating level {i+1} (\'{level_files[i]}\') from generator {self.generator_name}...")
                
                # Evaluate the level
                level_stats = game_evaluator.evaluate(level_files[i], levels[i])

                # Update the generator stats
                self.add_level_stats(level_stats)'''
        
        # Compute diversity values
        self.compute_content_diversity()
        self.compute_a_star_diversity()

    def add_level_stats(self, level_stats):
        self.levels_stats.append(level_stats)

    # Save the data as a csv file
    def save(self, output_folder, suffix = None):
        if suffix is None:
            suffix = "_stats"

        output_file = os.path.join(output_folder, self.generator_name + suffix + ".csv")

        metadata = {'Folder Path': self.folder_path, 'Generator Name': self.generator_name, 'Game Name': self.game_name, 'Ignore': self.ignore, 'Content Diversity': self.content_diversity, 'A* Diversity': self.a_star_diversity, 'Coverage': self.coverage, 'Number of intervals per dimension': self.diversity_archive.num_intervals_per_dimension}
        
        data = [vars(level_stats) for level_stats in self.levels_stats]
        '''for level_stats in self.levels_stats:
            level_data = deepcopy(vars(level_stats))
            characteristics = level_data.pop('characteristics')
            level_data = level_data | characteristics
            data.append(level_data)'''
        
        df = pd.DataFrame(data)

        # Add the generation times to the dataframe
        if self.generation_times is not None:
            df = pd.merge(df, self.generation_times, left_on='level_name', right_on='level_name', how='left')
        
        with open(output_file, 'w') as f:
            # Write metadata as comments
            for key, value in metadata.items():
                f.write(f"# {key}: {value}\n")
            
            # Write the data as a CSV
            df.to_csv(f, index=False)

    def load_from_csv(self, filepath):
        # Check if the path is a .csv file
        if not filepath.endswith('.csv'):
            raise ValueError("Path must be a .csv file.")
        
        # Read the metadata from the CSV file
        with open(filepath, 'r') as f:
            for line in f:
                if line.startswith("#"):
                    key, value = line[1:].strip().split(":")
                    key = key.strip()
                    value = value.strip()

                    if key == "Folder Path":
                        self.folder_path = value
                    elif key == "Generator Name":
                        self.generator_name = value
                    elif key == "Game Name":
                        self.game_name = value
                    elif key == "Ignore":
                        self.ignore = ast.literal_eval(value)
                    elif key == "Content Diversity":
                        self.content_diversity = ast.literal_eval(value)
                    elif key == "A* Diversity":
                        self.a_star_diversity = ast.literal_eval(value)
                    elif key == "Coverage":
                        self.coverage = ast.literal_eval(value)
                    elif key == "Number of intervals per dimension":
                        self.n_intervals_per_dimension = ast.literal_eval(value)
                else:
                    break

        # Check that every metadata has been read
        if self.folder_path is None:
            raise RuntimeError(f"ERROR: \'Folder Path\' not specified in {filepath}.")
        if self.generator_name is None:
            raise RuntimeError(f"ERROR: \'Generator Name\' not specified in {filepath}")
        if self.game_name is None:
            raise RuntimeError(f"ERROR: \'Game Name\' not specified in {filepath}")
        if self.ignore is None:
            raise RuntimeError(f"ERROR: \'Ignore\' not specified in {filepath}")
        if self.content_diversity is None:
            raise RuntimeError(f"ERROR: \'Content Diversity\' not specified in {filepath}")
        if self.a_star_diversity is None:
            raise RuntimeError(f"ERROR: \'A* Diversity\' not specified in {filepath}")
        if self.n_intervals_per_dimension is None:
            raise RuntimeError(f"ERROR: \'Number of intervals per dimension\' not specified in {filepath}")
        
        if self.ignore:
            print(f"WARNING: Ignoring generator from file {filepath}...")
            return
        
        self.diversity_archive = DiversityArchive(self.n_intervals_per_dimension)
        
        # Read the data from the CSV file
        df = pd.read_csv(filepath, comment="#")

        if "generation_time" in df.columns:
            self.generation_times = df[["level_name", "generation_time"]]
        else:
            # Search for times.csv in the associated folder
            print(f"WARNING: Generation times not found in the CSV file from generator {self.generator_name}. Looking for times.csv in the folder...")

            times_file = os.path.join(self.folder_path, "times.csv")
            if os.path.exists(times_file):
                # Read the content of times.csv
                self.generation_times = pd.read_csv(times_file)

                if "level_name" not in self.generation_times.columns:
                    raise ValueError("times.csv must contain a 'level_name' column.")
                if "generation_time" not in self.generation_times.columns:
                    raise ValueError("times.csv must contain a 'generation_time' column.")
            else:
                print(f"\nWARNING: {times_file} not found for {self.generator_name}. Generation times will not be available.")
            
        for index, row in df.iterrows():
            level_stats = LevelStats(
                level_name = row['level_name'],
                level = row['level'],
                has_valid_characters = row['has_valid_characters'],
                has_valid_size = row['has_valid_size'],
                has_visual_integrity = row['has_visual_integrity'],
                is_playable = row['is_playable'],
                actions = ast.literal_eval(row['actions']),
                characteristics = ast.literal_eval(row['characteristics'])
            )
            self.add_level_stats(level_stats)
                
    def compute_a_star_diversity(self):
        '''actions = [level_stats.actions for level_stats in self.levels_stats if level_stats.is_valid]

        pairs = list(combinations(actions, 2))
        print("Number of pairs: ", len(pairs))

        diversities = []
        for a, b in tqdm(pairs, desc = f"Computing A* Diversity of generator {self.generator_name}", ncols=80):
            diversities.append(levenshtein_distance(a, b))
        
        self.a_star_diversity = sum(diversities) / len(diversities) if len(diversities) > 0 else 0
        print("A* diversity: ", self.a_star_diversity)'''

        actions = [level_stats.actions for level_stats in self.levels_stats if level_stats.is_valid]

        pairs = list(combinations(actions, 2))

        if not pairs:
            self.content_diversity = 0
            print("A* diversity: 0")
            return

        desc = f"Computing A* Diversity"

        if self.parallelization:
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                diversities = list(
                    tqdm(
                        executor.map(levenshtein_distance, pairs),
                        total=len(pairs),
                        desc=desc,
                        ncols=80
                    )
                )
        else:
            diversities = [levenshtein_distance(par) for par in tqdm(pairs, total=len(pairs), desc=desc, ncols=80)]

        self.a_star_diversity = sum(diversities) / len(diversities)
        #print("A* diversity: ", self.a_star_diversity)

    def compute_content_diversity(self):
        '''valid_levels = []
        for level_stats in self.levels_stats:
            if level_stats.is_valid:
                valid_levels.append("".join(level_stats.level.splitlines()))

        pairs = list(combinations(valid_levels, 2))
        print("Number of pairs: ", len(pairs))

        diversities = []
        for a, b in tqdm(pairs, desc = f"Computing Content Diversity of generator {self.generator_name}", ncols=80):
            diversities.append(levenshtein_distance(a, b))
        
        self.content_diversity = sum(diversities) / len(diversities) if len(diversities) > 0 else 0
        print("Content diversity: ", self.content_diversity)'''

        valid_levels = ["".join(level_stats.level.splitlines()) for level_stats in self.levels_stats if level_stats.is_valid]

        pairs = list(combinations(valid_levels, 2))

        if not pairs:
            self.content_diversity = 0
            print("Content diversity: 0")
            return

        desc = f"Computing Content Diversity"

        if self.parallelization:
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                diversities = list(
                    tqdm(
                        executor.map(levenshtein_distance, pairs),
                        total=len(pairs),
                        desc=desc,
                        ncols=80
                    )
                )
        else:
            diversities = [levenshtein_distance(par) for par in tqdm(pairs, total=len(pairs), desc=desc, ncols=80)]

        self.content_diversity = sum(diversities) / len(diversities)
        #print("Content diversity: ", self.content_diversity)
    
    def compute_coverage(self):
        self.diversity_archive.add_generator_stats(self)
        self.coverage = self.diversity_archive.get_coverage()

    def normalize_diversity(self, min_content_diversity, max_content_diversity, min_a_star_diversity, max_a_star_diversity, min_coverage, max_coverage):
        '''self.coverage = (self.coverage - min_coverage) / (max_coverage - min_coverage)
        self.a_star_diversity = (self.a_star_diversity - min_a_star_diversity) / (max_a_star_diversity - min_a_star_diversity)
        self.content_diversity = (self.content_diversity - min_content_diversity) / (max_content_diversity - min_content_diversity)'''

        self.coverage = self.coverage / max_coverage
        self.a_star_diversity = self.a_star_diversity / max_a_star_diversity
        self.content_diversity = self.content_diversity / max_content_diversity

    def normalize_characteristics(self, min_values : dict, max_values : dict):
        keys = min_values.keys()
        for key in keys:
            min_value = min_values[key]
            max_value = max_values[key]
            if min_value == max_value:
                for level_stats in self.levels_stats:
                    level_stats.characteristics[key] = 0
            else:
                for level_stats in self.levels_stats:
                    if len(level_stats.characteristics) > 0:
                        level_stats.characteristics[key] = (level_stats.characteristics[key] - min_value) / (max_value - min_value)
                
        '''min_content_diversity = min_values["content_diversity"]
        max_content_diversity = max_values["content_diversity"]
        self.content_diversity = (self.content_diversity - min_content_diversity) / (max_content_diversity - min_content_diversity)

        min_a_star_diversity = min_values["a_star_diversity"]
        max_a_star_diversity = max_values["a_star_diversity"]
        self.a_star_diversity = (self.a_star_diversity - min_a_star_diversity) / (max_a_star_diversity - min_a_star_diversity)

        min_coverage = min_values["coverage"]
        max_coverage = max_values["coverage"]
        if min_coverage == max_coverage:
            self.coverage = 0
        else:
            self.coverage = (self.coverage - min_coverage) / (max_coverage - min_coverage)'''
        
    def average_generation_time(self):
        if self.generation_times is None:
            return None
        
        times = self.generation_times["generation_time"].values

        return sum(times) / len(times) / 1e9  # Convert to seconds
    
    def no_visual_bugs_percentage(self):
        correct_levels = [1 if level_stats.has_valid_characters and level_stats.has_valid_size and level_stats.has_visual_integrity else 0 for level_stats in self.levels_stats]

        return sum(correct_levels) / len(correct_levels)

    def valid_percentage(self):
        valid_levels = [1 if level_stats.is_valid else 0 for level_stats in self.levels_stats]

        return sum(valid_levels) / len(valid_levels)