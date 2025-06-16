import numpy as np

class DiversityArchive:
    def __init__(self, num_intervals_per_dimension):
        self.num_intervals_per_dimension = num_intervals_per_dimension
        self.dimensions = None
        self.set_of_covered_cells = set()

    def add_generator_stats(self, generator_stats):
        for level_stats in generator_stats.levels_stats:
            if level_stats.is_valid:
                # Compute the position in the diversity space
                values = np.array(list(level_stats.characteristics.values()))

                if self.dimensions is None:
                    self.dimensions = len(values)
                elif self.dimensions != len(values):
                    raise ValueError("Inconsistent dimensions in characteristics of generator " + generator_stats.generator_name)
                
                position = np.floor(values * self.num_intervals_per_dimension)
                position = np.clip(position, 0, self.num_intervals_per_dimension - 1)

                # Mark the associated cell as covered
                self.set_of_covered_cells.add(tuple(position))

    def get_coverage(self):
        return len(self.set_of_covered_cells)