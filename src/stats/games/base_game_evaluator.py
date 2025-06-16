from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from stats.level_stats import LevelStats

class GameEvaluator(ABC, BaseModel):
    """
    Abstract base class for game level evaluators.
    This class defines the interface for evaluating game levels, including methods for
    validating characters, size, and visual integrity, as well as simulating playthroughs
    and evaluating characteristics.
    """
    num_rows: int = Field(..., description="Number of rows in the level", gt=0)
    num_cols: int = Field(..., description="Number of columns in the level", gt=0)

    def model_post_init(self, __context):
        """
        Post-initialization method to validate the model's attributes.
        This method checks that the valid characters are a list of single-character strings.
        """
        valid_chars = self.get_valid_characters()
        if not isinstance(valid_chars, list):
            raise TypeError("get_valid_characters() must return a list")
        if not valid_chars:
            raise ValueError("get_valid_characters() must return a non-empty list")
        if not all(isinstance(c, str) and len(c) == 1 for c in valid_chars):
            raise ValueError("All valid characters must be single-character strings")
        
    @property
    def valid_characters(self) -> list:
        """
        Returns the list of valid characters for the game.
        """
        return self.get_valid_characters()

    def validate_characters(self, level: str) -> bool:
        """
        Validates that all characters in the level are within the valid character set.

        Note: This method ignores the newline characters.
        """
        return all(c in self.valid_characters for c in "".join(level.splitlines()))
    
    def validate_size(self, level: str) -> bool:
        """
        Validates that the level size is correct.
        """
        # Check if the level has the expected number of rows and columns
        rows = level.splitlines()
        if len(rows) != self.num_rows:
            return False

        for row in rows:
            if len(row) != self.num_cols:
                return False

        return True
    
    def validate_visual_integrity(self, level: str) -> bool:
        """
        Validates that the level has visual integrity.

        This method can be overridden by subclasses in order to define specific visual integrity rules.
        """
        return True

    def evaluate(self, level_path: str, level: str, parallelization : bool) -> LevelStats:
        """
        The main evaluation method that:
         1. Removes the last character if it's a newline.
         2. Checks that the level contains only valid characters.
         3. Checks that the level has the correct size.
         4. Checks that the level has visual integrity.
         5. Simulates a playthrough of the level and returns the results.
         6. Evaluates the level's characteristics.
        
        Returns the results as a tuple of (playability, actions, characteristics).
        """
        # Initialize necessary variables
        has_valid_characters = False
        has_valid_size = False
        has_visual_integrity = False
        is_playable = False
        actions = []
        characteristics = {}
        level_name = level_path.split("/")[-1]

        if level[-1] == "\n":
            level = level[:-1]

        has_valid_characters = self.validate_characters(level)

        if has_valid_characters:
            has_valid_size = self.validate_size(level)

            if has_valid_size:
                has_visual_integrity = self.validate_visual_integrity(level)

                if has_visual_integrity:
                    is_playable, actions = self.simulation_data(level_path, level)

                    if is_playable:
                        characteristics = self.evaluate_characteristics(level)

                        for key, value in characteristics.items():
                            if not isinstance(value, float):
                                try:
                                    value = float(value)
                                except RuntimeError:
                                    raise RuntimeError(f"ERROR: Characteristics from a level must be a dictionary with (string, float) pairs. The characteristic {key} is not float and it cannot be \
                                          converted to float either.\nThe method \'evaluate_characteristics\' returned a {type(value)} value. Please, modify the method so it returns a float. Exiting...")
                    '''elif not parallelization:
                        print(f"\nWARNING: Level {level_name} is not playable.")
                elif not parallelization:
                    print("WARNING: Level does not have visual integrity.")
            elif not parallelization:
                print("WARNING: Level size is incorrect.")
        elif not parallelization:
            print("WARNING: Level contains invalid characters.")
            invalid_chars = set("".join(level.splitlines())) - set(self.valid_characters)
            print(f"Invalid characters: {invalid_chars}")'''

        # Create a LevelStats object to store the results
        level_stats = LevelStats(
            level_name=level_name,
            level=level,
            has_valid_characters=has_valid_characters,
            has_valid_size=has_valid_size,
            has_visual_integrity=has_visual_integrity,
            is_playable=is_playable,
            actions=actions,
            characteristics=characteristics
        )

        '''print(f"Level {level_path} evaluation results:")
        print(f"  - Valid characters: {has_valid_characters}")
        print(f"  - Valid size: {has_valid_size}")
        print(f"  - Visual integrity: {has_visual_integrity}")
        print(f"  - Playable: {is_playable}")
        print(f"  - Actions: {actions}")
        print("Level:\n")
        print(level)'''

        return level_stats
    
    @abstractmethod
    def get_valid_characters(self) -> list:
        """
        Abstract method to return the set of valid characters for the specific game.
        """
        pass

    @abstractmethod
    def simulation_data(self, level_path: str, level: str) -> tuple[bool, list]:
        """
        Abstract method to simulate a playthrough of the level and return the results. It should return a tuple containing:
         1) A boolean indicating whether the level is playable.
         2) A list of actions taken during the simulation.
        Note: It includes the level file path as a parameter in case it is necessary.
        """
        pass

    @abstractmethod
    def evaluate_characteristics(self, level: str) -> dict[str, float]:
        """
        Abstract method for evaluating the level's characteristics.
        """
        pass