from stats.games.base_game_evaluator import GameEvaluator
from stats.games.mario.mario_tiles import TILES
import stats.games.mario.mario_simulation_data as mario_simulation_data
import stats.games.mario.mario_characteristics as mario_characteristics
import stats.games.mario.mario_visual_integrity as mario_visual_integrity

class MarioEvaluator(GameEvaluator):
    def get_valid_characters(self):
        # Define valid characters for Super Mario Bros
        return TILES

    def evaluate_characteristics(self, level):
        return mario_characteristics.evaluate_characteristics(level)

    def simulation_data(self, level_file, level):
        return mario_simulation_data.simulation_data(level_file)

    def validate_visual_integrity(self, level):
        # Check if the level has visual integrity
        return mario_visual_integrity.validate_visual_integrity(level)