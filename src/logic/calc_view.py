import numpy as np
import math
from typing import List, Tuple, Dict, Any

from src.logger import logger
from src.config import ViewCalculationConfig as viewconfig

def transform_map_to_view(level: Dict[str, Any]) -> List[List[Tuple[float, float]]]:
    """
    Transforms a map to a view based on the given parameters.

    Parameters:
    level (dict): The map data.

    Returns:
    list: A 2D list of tuples representing the transformed map points in ratio form.
    """
    DEGREE = math.pi / 180
    try:
        height, width = level["height"], level["width"]
        x, y, z = level["view"][1]
    except KeyError as e:
        logger.error(f"Error loading map data: {e}")
        raise KeyError(f"Error loading map data: {e}")

    # Matrix for transforming map coordinates to view coordinates
    transform_matrix = np.array([
        [1, 0, 0, -x],
        [0, 1, 0, -y],
        [0, 0, 1, -z],
        [0, 0, 0, 1]
    ])

    # Transformation matrices
    perspective_matrix = np.array([
        [viewconfig.FROM_RATIO / math.tan(20 * DEGREE), 0, 0, 0],
        [0, 1 / math.tan(20 * DEGREE), 0, 0],
        [0, 0, -(viewconfig.FAR + viewconfig.NEAR) / (viewconfig.FAR - viewconfig.NEAR), -(viewconfig.FAR * viewconfig.NEAR * 2) / (viewconfig.FAR - viewconfig.NEAR)],
        [0, 0, -1, 0]
    ])
    rotate_x_matrix = np.array([
        [1, 0, 0, 0],
        [0, math.cos(30 * DEGREE), -math.sin(30 * DEGREE), 0],
        [0, -math.sin(30 * DEGREE), -math.cos(30 * DEGREE), 0],
        [0, 0, 0, 1]
    ])
    rotate_y_matrix = np.array([
        [math.cos(10 * DEGREE), 0, math.sin(10 * DEGREE), 0],
        [0, 1, 0, 0],
        [-math.sin(10 * DEGREE), 0, math.cos(10 * DEGREE), 0],
        [0, 0, 0, 1]
    ])

    # Final transformation matrix
    final_matrix = perspective_matrix @ rotate_x_matrix @ rotate_y_matrix @ transform_matrix.copy()

    # Transform each map point to view point
    out_pos = []
    for i in range(height):
        tmp_pos = []
        for j in range(width):
            tile = level["tiles"][i][j]
            map_point = np.array([
                j - (width - 1) / 2.0, 
                (height - 1) / 2.0 - i, 
                tile["heightType"] * -0.4, 
                1])
            view_point = final_matrix @ map_point
            view_point = view_point / view_point[3]
            view_point = (view_point + 1) / 2
            tmp_pos.append((view_point[0], 1 - view_point[1]))
        out_pos.append(tmp_pos)

    logger.info(f"Transformed map to view, size: {height}x{width}")
    return out_pos

if __name__ == "__main__":
    # Usage and Testing
    from src.cache import get_map
    map = get_map('1-7')
    res = transform_map_to_view(map)
    # Note: result seems to have reversed x and y, compared to showen on map.ark-nights.com
    # the left most deployable position
    logger.info(f"Left most deployable position: {res[3][1]}")