
from src.logic.action import Action

def convert_position(action: Action, height: int, width: int) -> Action:
    """
    Convert chess board representation to numerical representation
    For example, under height 7, width 11: D2 -> (1, 3), C5 -> (4, 4), F7 -> (6, 1)
    """
    try:
        action.tile_pos = (int(action.pos[1:]) - 1, height - 1 - (ord(action.pos[0]) - ord('A')))
    except Exception as e:
        action.tile_pos = None
    return action

if __name__ == "__main__":
    # Usage and testing
    action = Action(pos="D2")
    print(convert_position(action, 7, 11)) # Action(pos='D2', tile_pos=(5, 3))
    action = Action(pos="C5")
    print(convert_position(action, 7, 11)) # Action(pos='C5', tile_pos=(2, 4))
    action = Action(pos="F7")
    print(convert_position(action, 7, 11)) # Action(pos='F7', tile_pos=(0, 5))