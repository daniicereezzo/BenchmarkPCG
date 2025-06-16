from stats.games.mario.mario_tiles import *

def validate_visual_integrity(level):
    """
    Validate the visual integrity of a Mario level.
    
    Args:
        level (str): The level string to validate.
        
    Returns:
        bool: True if the level has visual integrity, False otherwise.
    """
    top_left_pipe_positions = []
    top_right_pipe_positions = []
    left_pipe_positions = []
    right_pipe_positions = []
    top_cannon_positions = []
    body_cannon_positions = []

    level = level.splitlines()
    height = len(level)
    width = len(level[0])

    for i in range(height):
        for j in range(width):
            match level[i][j]:
                case '<':
                    top_left_pipe_positions.append((j, i))
                case '>':
                    top_right_pipe_positions.append((j, i))
                case '[':
                    left_pipe_positions.append((j, i))
                case ']':
                    right_pipe_positions.append((j, i))
                case 'B':
                    top_cannon_positions.append((j, i))
                case 'b':
                    body_cannon_positions.append((j, i))
                case _:
                    pass

    # Ensures that every left part of the pipe has a right part and viceversa

    predicted_top_right_pipe_positions = [(x + 1, y) for x, y in top_left_pipe_positions]

    set_top_right_pipe_positions = set(top_right_pipe_positions)
    set_predicted_top_right_pipe_positions = set(predicted_top_right_pipe_positions)

    if set_top_right_pipe_positions != set_predicted_top_right_pipe_positions:
        return False
    
    predicted_right_pipe_positions = [(x + 1, y) for x, y in left_pipe_positions]

    set_right_pipe_positions = set(right_pipe_positions)
    set_predicted_right_pipe_positions = set(predicted_right_pipe_positions)

    if set_right_pipe_positions != set_predicted_right_pipe_positions:
        return False
    
    
    # Ensures that every body part of a pipe is connected to another body part or a top part

    for left_pipe_position in left_pipe_positions:
        x, y = left_pipe_position

        if y == 0:
            if level[y+1][x] != LEFT_PIPE and level[y+1][x] != TOP_LEFT_PIPE:
                return False
        elif y == height - 1:
            if level[y-1][x] != TOP_LEFT_PIPE and level[y-1][x] != LEFT_PIPE:
                return False
        elif level[y-1][x] != TOP_LEFT_PIPE and level[y-1][x] != LEFT_PIPE and level[y+1][x] != TOP_LEFT_PIPE and level[y+1][x] != LEFT_PIPE:
            return False
        
    # Ensures that every body part of a cannon is connected to another body part or a top part

    for body_cannon_position in body_cannon_positions:
        x, y = body_cannon_position

        '''if y == 0:
            return False
        
        if level[y-1][x] != BODY_CANNON and level[y-1][x] != TOP_CANNON:
            return False'''

        if y == 0:
            if level[y+1][x] != BODY_CANNON and level[y+1][x] != TOP_CANNON:
                return False 
        elif y == height - 1:
            if level[y-1][x] != TOP_CANNON and level[y-1][x] != BODY_CANNON:
                return False
        elif level[y-1][x] != TOP_CANNON and level[y-1][x] != BODY_CANNON and level[y+1][x] != TOP_CANNON and level[y+1][x] != BODY_CANNON:
                return False
    

    # Ensures that there are no consecutive top parts in the same column
        
    '''for top_left_pipe_position in top_left_pipe_positions:
        x, y = top_left_pipe_position
        if (x, y-1) in top_left_pipe_positions:
            return False'''
        
    # Ensures that there are no groups of consecutive body parts without a top part or two consecutive top parts in the same column
    
    for j in range(width):
        top_found = False
        pipe_found = False

        for i in range(height):
            if level[i][j] == TOP_LEFT_PIPE:
                if not top_found and pipe_found:    # Upside down pipe
                    pipe_found = False
                    top_found = False
                elif top_found and not pipe_found:  # Two consecutive top parts
                    return False
                else:                               # New normal pipe
                    pipe_found = False
                    top_found = True
            elif level[i][j] == LEFT_PIPE:
                if not pipe_found:
                    pipe_found = True
            else:
                if pipe_found and not top_found:    # Pipe without top part
                    return False
                
                pipe_found = False                  # Reset variables
                top_found = False
        
        if pipe_found and not top_found:            # Pipe without top part
            return False
        
        pipe_found = False                          # Reset variables
        top_found = False
    
    # Same with cannons

    for j in range(width):
        top_found = False
        cannon_found = False

        for i in range(height):
            if level[i][j] == TOP_CANNON:
                if not top_found and cannon_found:    # Upside down cannon
                    cannon_found = False
                    top_found = False
                elif top_found and not cannon_found:  # Two consecutive top parts
                    return False
                else:                               # New normal cannon
                    cannon_found = False
                    top_found = True
            elif level[i][j] == BODY_CANNON:
                if not cannon_found:
                    cannon_found = True
            else:
                if cannon_found and not top_found:    # Cannon without top part
                    return False
                
                cannon_found = False                  # Reset variables
                top_found = False
        
        if cannon_found and not top_found:            # Cannon without top part
            return False
        
        cannon_found = False                          # Reset variables
        top_found = False

    return True