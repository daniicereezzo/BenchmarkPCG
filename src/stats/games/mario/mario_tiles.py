import sys

GROUND = "X"
BREAKABLE = "S"
EMPTY = "-"
FULL_QUESTION_BLOCK = "?"
EMPTY_QUESTION_BLOCK = "Q"
ENEMY = "E"
TOP_LEFT_PIPE = "<"
TOP_RIGHT_PIPE = ">"
LEFT_PIPE = "["
RIGHT_PIPE = "]"
COIN = "o"
TOP_CANNON = "B"
BODY_CANNON = "b"

TILES = [GROUND, BREAKABLE, EMPTY, FULL_QUESTION_BLOCK, EMPTY_QUESTION_BLOCK, ENEMY, TOP_LEFT_PIPE, TOP_RIGHT_PIPE, LEFT_PIPE, RIGHT_PIPE, COIN, TOP_CANNON, BODY_CANNON]

def from_int_to_vglc(num):
    try:
        char = TILES[num]
        return char
    except IndexError:
        print("ERROR: Invalid number. Exiting...")
        sys.exit(1)
        
def from_vglc_to_int(char):
    try:
        num = TILES.index(char)
        return num
    except ValueError:
        print("ERROR: Invalid character. Exiting...")
        sys.exit(1)

''' "X" : ["solid","ground"],
    "S" : ["solid","breakable"],
    "-" : ["passable","empty"],
    "?" : ["solid","question block", "full question block"],
    "Q" : ["solid","question block", "empty question block"],
    "E" : ["enemy","damaging","hazard","moving"],
    "<" : ["solid","top-left pipe","pipe"],
    ">" : ["solid","top-right pipe","pipe"],
    "[" : ["solid","left pipe","pipe"],
    "]" : ["solid","right pipe","pipe"],
    "o" : ["coin","collectable","passable"],
    "B" : ["Cannon top","cannon","solid","hazard"],
    "b" : ["Cannon bottom","cannon","solid"]'''
