from stats.games.base_game_evaluator import GameEvaluator
from stats.games.mario.mario import MarioEvaluator

EVALUATOR_REGISTRY = {}

def register_game(name : str, evaluator_cls : GameEvaluator, num_rows : int, num_cols: int):
    """
    Register a game evaluator class in the registry.
    Args:
        name (str): The name of the game.
        evaluator_cls (type): The evaluator class to register.
        num_rows (int): The number of rows in the level.
        num_cols (int): The number of columns in the level.
    """
    if not isinstance(name, str):
        raise ValueError("Game name must be a string.")
    if not name:
        raise ValueError("Game name cannot be empty.")
    
    if not issubclass(evaluator_cls, GameEvaluator):
        raise ValueError(f"{evaluator_cls} is not a subclass of GameEvaluator.")
    
    if name in EVALUATOR_REGISTRY:
        raise ValueError(f"Game evaluator for {name} is already registered.")
    
    EVALUATOR_REGISTRY[name] = evaluator_cls(num_rows = num_rows, num_cols = num_cols)

    print(f"Registered game evaluator for {name} with dimensions {num_rows}x{num_cols}.")
    
# Register the evaluator for Super Mario Bros levels of size 14x140
register_game("Super Mario Bros", MarioEvaluator, 14, 140)