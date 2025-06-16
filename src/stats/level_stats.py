from pydantic import BaseModel, Field

class LevelStats(BaseModel):
    """
    Class to store the statistics of a level.
    
    Attributes:
        level_name (str): The name of the level.
        level (str): The level data as a string.
        generation_time (float): The time taken to generate the level.
        has_valid_characters (bool): Whether the level has valid characters.
        has_valid_size (bool): Whether the level size is valid.
        has_visual_integrity (bool): Whether the level has visual integrity.
        is_playable (bool): Whether the level is playable.
        actions (list): List of actions taken by the agent during the simulation.
        characteristics (BaseCharacteristics): The characteristics to measure in the level.
    """
    
    level_name: str = Field(..., description="The name of the level.")
    level: str = Field(..., description="The level data as a string.")
    has_valid_characters: bool = Field(..., description="Whether the level has valid characters.")
    has_valid_size: bool = Field(..., description="Whether the level size is valid.")
    has_visual_integrity: bool = Field(..., description="Whether the level has visual integrity.")
    is_playable: bool = Field(..., description="Whether the level is playable.")
    actions: list = Field(..., description="List of actions taken by the agent during the simulation.")
    characteristics: dict = Field(..., description="The characteristics to measure in the level.")

    @property
    def is_valid(self) -> bool:
        return (
            self.has_valid_characters and
            self.has_valid_size and
            self.has_visual_integrity and
            self.is_playable
        )