from curses_tools import draw_frame, get_frame_size
import asyncio
from obstacles import Obstacle


obstacles = []
obstacles_in_last_collisions = []


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 0

    while row < rows_number:
        draw_frame(canvas, row, column, garbage_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        obstacle_row, obstacle_column = get_frame_size(garbage_frame)
        global obstacles
        obstacles.append(Obstacle(row, column, obstacle_row, obstacle_column))
        for item in obstacles_in_last_collisions:
            while item in obstacles:
                obstacles.remove(item)
        row += speed
