import sys
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

from stats.games.mario.mario_tiles import *

def evaluate_characteristics(level):
    mario_characteristics = MarioCharacteristics(level)
    return mario_characteristics.characteristics

class MarioCharacteristics:
    def __init__(self, level):
        # Initialize variables
        self.level = level.splitlines()
        self.height = len(self.level)
        self.width = len(self.level[0]) if self.height > 0 else 0

        self.tile_absolute_frequency = {}
        self.tile_relative_frequency = {}
        self.tile_positions = {}
        self.tile_position_stats = {}
        self.tile_indicator = {}
        self.gap_widths = []
        self.n_platforms_per_col = []
        self.n_gaps = 0

        self.characteristics = {
            "linearity": 0,
            "leniency": 0,
            "density": 0,
            "simmetry": 0,
            "balance": 0,
            "decoration_frequency": 0,
            "enemy_sparsity": 0,
        }

        # Evaluate the level
        self.evaluate_level()
        
    def evaluate_level(self):
        try:
            self.compute_raw_data()
        except RuntimeError as e: # It has a tile that is not in the TILES list
            print(f"ERROR: {e}")
            print("ERROR: Level has invalid tiles. Exiting...")
            invalid_tiles = set(self.level) - set(TILES)
            print(f"Invalid tiles: {invalid_tiles}")
            sys.exit(1)

        # The order of the following executions is important (some functions depend on the results of others)
        self.compute_linearity()
        self.compute_leniency()
        self.compute_density()
        self.compute_simmetry()
        self.compute_balance()
        self.compute_decoration_frequency()
        self.compute_enemy_sparsity()

    # Compute:
    #  - the number of gaps: n_gaps,
    #  - the number of ground blocks in each column: n_platforms_per_col
    #  - For each tile: absolute frequency, relative frequency, positions, position stats and indicator
    def compute_raw_data(self):
        # Compute absolute frequency, tile positions and ground blocks per column
        for tile in TILES:
            self.tile_absolute_frequency[tile] = 0
            self.tile_positions[tile] = []

        self.n_platforms_per_col = [0] * self.width

        for y, row in enumerate(self.level):
            for x, tile in enumerate(row):
                self.tile_absolute_frequency[tile] += 1
                self.tile_positions[tile].append((x, y))
                if tile in [GROUND, BREAKABLE, FULL_QUESTION_BLOCK, EMPTY_QUESTION_BLOCK] and \
                (y == 0 or self.level[y - 1][x] in [EMPTY, COIN, ENEMY]):
                    self.n_platforms_per_col[x] += 1

        # Compute relative frequency
        total_tiles = self.width * self.height
        for tile in TILES:
            self.tile_relative_frequency[tile] = self.tile_absolute_frequency[tile] / total_tiles

        # Compute tile indicator
        for tile in TILES:
            self.tile_indicator[tile] = 0 if self.tile_absolute_frequency[tile] == 0 else 1

        # Compute position stats
        for tile in TILES:
            if self.tile_absolute_frequency[tile] > 0:
                x = np.array([pos[0] for pos in self.tile_positions[tile]])
                y = np.array([pos[1] for pos in self.tile_positions[tile]])
                self.tile_position_stats[tile] = {"mean_x": float(np.mean(x)), "mean_y": float(np.mean(y)), "std_x": float(np.std(x)), "std_y": float(np.std(y))}
            else:
                self.tile_position_stats[tile] = {"mean_x": None, "mean_y": None, "std_x": None, "std_y": None}
        
        # Compute the width of the gaps presented in the level and the number of gaps (a gap is a set of consecutive columns with no ground blocks)
        gap_found = False
        gap_width = 0
        for x in range(len(self.level[0])):
            if all([self.level[y][x] != GROUND for y in range(len(self.level))]):
                if not gap_found:
                    gap_found = True
                    gap_width = 1
                else:
                    gap_width += 1
                
                if x == len(self.level[0]) - 1:
                    self.gap_widths.append(gap_width)
            elif gap_found:
                self.gap_widths.append(gap_width)
                gap_found = False
                gap_width = 0
        self.n_gaps = len(self.gap_widths)
            
    def compute_linearity(self):  # This function computes the linearity of the ground blocks in the level
        # Get ground blocks of the level
        x = []
        y = []

        for i, row in enumerate(self.level):
            for j, tile in enumerate(row):
                if tile in [GROUND, BREAKABLE, FULL_QUESTION_BLOCK, EMPTY_QUESTION_BLOCK] and \
                (i == 0 or self.level[i - 1][j] in [EMPTY, COIN, ENEMY]):
                    x.append(j)
                    y.append(i)

        #x = [tile[0] for tile in self.tile_positions[GROUND]]
        #y = [tile[1] for tile in self.tile_positions[GROUND]]

        x = np.array(x)
        y = np.array(y)

        # Compute the regression line
        slope, intercept, r, p, std_err = stats.linregress(x, y)

        def model(x):
            return slope * x + intercept

        # Plot the regression line
        #regression_line = list(map(model, x))
        #plt.scatter(x, y)
        #plt.plot(x, regression_line, color='red')
        #plt.show()

        # Compute the linearity of the level
        self.characteristics["linearity"] = -float(sum([abs(y_p - model(p)) for (p, y_p) in zip(x, y)]) / len(x))
        #self.characteristics["linearity"] = float(r) ** 2
        #self.characteristics["linearity"] = r ** 2
    
    def compute_leniency(self):
        # Weights: power-up blocks (1), cannons, flower tubes and gaps (-0.5), enemies, average gap width (-1)
        average_gap_width = sum(self.gap_widths) / len(self.gap_widths) if len(self.gap_widths) > 0 else 0

        total_sum = self.tile_absolute_frequency[FULL_QUESTION_BLOCK] * (1) + \
              self.tile_absolute_frequency[TOP_CANNON] * (-0.5) + \
              self.tile_absolute_frequency[TOP_LEFT_PIPE] * (-0.5) + \
              self.n_gaps * (-0.5) + \
              self.tile_absolute_frequency[ENEMY] * (-1) + \
              average_gap_width * (-1)
        
        self.characteristics["leniency"] = total_sum / self.width
    
    def compute_density(self):
        self.characteristics["density"] = sum(self.n_platforms_per_col) / self.width
    
    def compute_simmetry(self):
        # 12 columnas. mitad izquierda = [0, 5], mitad derecha = [6,11], columnas / 2 = 6
        # 11 columnas. mitad izquierda = [0, 4], mitad derecha = [6,10], columnas / 2 = 5.5
        limit_down = self.height // 2
        if self.height % 2 == 1:
            limit_down += 1
        
        limit_right = self.width // 2
        if self.width % 2 == 1:
            limit_right += 1
            
        mid_height = (self.height - 1) / 2
        mid_width = (self.width - 1) / 2

        data_submatrix_up_left = [0.0, 0.0, 0.0]
        data_submatrix_up_right = [0.0, 0.0, 0.0]
        data_submatrix_down_left = [0.0, 0.0, 0.0]
        data_submatrix_down_right = [0.0, 0.0, 0.0]

        for i, row in enumerate(self.level):
            for j, tile in enumerate(row):
                if tile != EMPTY:
                    if i < self.height // 2 and j < self.width // 2:
                        data_submatrix_up_left[0] += abs(j - mid_width)
                        data_submatrix_up_left[1] += abs(i - mid_height)
                        data_submatrix_up_left[2] += 1
                    if i < self.height // 2 and j >= limit_right:
                        data_submatrix_up_right[0] += abs(j - mid_width)
                        data_submatrix_up_right[1] += abs(i - mid_height)
                        data_submatrix_up_right[2] += 1
                    if i >= limit_down and j < self.width // 2:
                        data_submatrix_down_left[0] += abs(j - mid_width)
                        data_submatrix_down_left[1] += abs(i - mid_height)
                        data_submatrix_down_left[2] += 1
                    if i >= limit_down and j >= limit_right:
                        data_submatrix_down_right[0] += abs(j - mid_width)
                        data_submatrix_down_right[1] += abs(i - mid_height)
                        data_submatrix_down_right[2] += 1


        #print("Limit right: ", limit_right)
        #print("Limit down: ", limit_down)

        '''submatrix_up_left = [row[:self.width // 2] for row in self.level[:self.height // 2]]
        submatrix_up_right = [row[limit_right:] for row in self.level[:self.height // 2]]
        submatrix_down_left = [row[:self.width // 2] for row in self.level[limit_down:]]
        submatrix_down_right = [row[limit_right:] for row in self.level[limit_down:]]

        

        def simmetry_data(submatrix):
            submatrix_height = len(submatrix)
            submatrix_width = len(submatrix[0]) if submatrix_height > 0 else 0

            return (
                sum([abs(j - mid_width) for row in submatrix for j in range(submatrix_width) if row[j] != EMPTY]),
                sum([abs(i - mid_height) for i in range(submatrix_height) for j in range(submatrix_width) if submatrix[i][j] != EMPTY]),
                submatrix_height * submatrix_width - "".join(submatrix).count(EMPTY)
            )

        data_submatrix_up_left = simmetry_data(submatrix_up_left)
        data_submatrix_up_right = simmetry_data(submatrix_up_right)
        data_submatrix_down_left = simmetry_data(submatrix_down_left)
        data_submatrix_down_right = simmetry_data(submatrix_down_right)'''

        X = abs(data_submatrix_up_left[0] - data_submatrix_up_right[0]) + \
            abs(data_submatrix_down_left[0] - data_submatrix_down_right[0]) + \
            abs(data_submatrix_up_left[0] - data_submatrix_down_left[0]) + \
            abs(data_submatrix_up_right[0] - data_submatrix_down_right[0]) + \
            abs(data_submatrix_up_left[0] - data_submatrix_down_right[0]) + \
            abs(data_submatrix_up_right[0] - data_submatrix_down_left[0])

        Y = abs(data_submatrix_up_left[1] - data_submatrix_up_right[1]) + \
            abs(data_submatrix_down_left[1] - data_submatrix_down_right[1]) + \
            abs(data_submatrix_up_left[1] - data_submatrix_down_left[1]) + \
            abs(data_submatrix_up_right[1] - data_submatrix_down_right[1]) + \
            abs(data_submatrix_up_left[1] - data_submatrix_down_right[1]) + \
            abs(data_submatrix_up_right[1] - data_submatrix_down_left[1])

        A = abs(data_submatrix_up_left[2] - data_submatrix_up_right[2]) + \
            abs(data_submatrix_down_left[2] - data_submatrix_down_right[2]) + \
            abs(data_submatrix_up_left[2] - data_submatrix_down_left[2]) + \
            abs(data_submatrix_up_right[2] - data_submatrix_down_right[2]) + \
            abs(data_submatrix_up_left[2] - data_submatrix_down_right[2]) + \
            abs(data_submatrix_up_right[2] - data_submatrix_down_left[2])
        
        self.characteristics["simmetry"] = -(X + Y + A)

        '''mid_width = self.width // 2
        mid_height = self.height // 2

        vertical_simmetry = 0
        upper_sublevel = self.level[:mid_height]
        lower_sublevel = self.level[mid_height:] if self.height % 2 == 0 else self.level[mid_height + 1:]
        flipped_lower_sublevel = lower_sublevel[::-1]

        for x in range(self.width):
            for y in range(mid_height):
                if upper_sublevel[y][x] == EMPTY and flipped_lower_sublevel[y][x] == EMPTY:
                    vertical_simmetry += 1

        horizontal_simmetry = 0
        left_sublevel = [row[:mid_width] for row in self.level]
        right_sublevel = [row[mid_width:] for row in self.level] if self.width % 2 == 0 else [row[mid_width + 1:] for row in self.level]
        flipped_right_sublevel = [row[::-1] for row in right_sublevel]

        for x in range(mid_width):
            for y in range(self.height):
                if left_sublevel[y][x] == EMPTY and flipped_right_sublevel[y][x] == EMPTY:
                    horizontal_simmetry += 1

        self.characteristics["simmetry"] = (vertical_simmetry + horizontal_simmetry) / (self.width * self.height)'''

    def compute_balance(self):
        mid_height = self.height // 2

        upper_sublevel = self.level[:mid_height]
        lower_sublevel = self.level[mid_height:] if self.height % 2 == 0 else self.level[mid_height + 1:]
        flipped_lower_sublevel = lower_sublevel[::-1]

        top_W = 0
        bottom_W = 0

        for x in range(self.width):
            for y in range(mid_height):
                if upper_sublevel[y][x] != EMPTY:
                    top_W += abs(y - mid_height)
                if flipped_lower_sublevel[y][x] != EMPTY:
                    bottom_W += abs(y - mid_height)

        self.characteristics["balance"] = abs(top_W - bottom_W)

    def compute_decoration_frequency(self):
        self.characteristics["decoration_frequency"] = sum([self.tile_absolute_frequency[tile] for tile in TILES if tile != GROUND and tile != EMPTY]) / (self.width * self.height)

    def compute_enemy_sparsity(self):
        if self.tile_absolute_frequency[ENEMY] == 0:
            self.characteristics["enemy_sparsity"] = 0
            return
        
        self.characteristics["enemy_sparsity"] = sum([abs(self.tile_positions[ENEMY][i][0] - self.tile_position_stats[ENEMY]["mean_x"]) for i in range(self.tile_absolute_frequency[ENEMY])]) / self.tile_absolute_frequency[ENEMY]

    '''def compute_path_length_percentage(self):
        self.characteristics["path_length_percentage"] = len(set(self.locations)) / (self.width * self.height)

    def compute_necessary_jumps(self):
        self.characteristics["necessary_jumps"] = self.result.getNumJumps()

    def compute_a_star_difficulty(self):
        self.characteristics["a_star_difficulty"] = self.result.getAStarDifficulty() / (self.width * self.height)'''