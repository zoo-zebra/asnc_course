import asyncio
import curses
import time
import random
from obstacles import show_obstacles, has_collision
from itertools import cycle
from explosion import explode

from curses_tools import draw_frame, read_controls, get_frame_size
from space_garbage import fly_garbage, obstacles, obstacles_in_last_collisions
from physics import update_speed
from game_scenario import get_garbage_delay_tics


TICK_TIMEOUT = 0.1
GARBAGE = ("duck", "hubble", "lamp", "trash_large", "trash_small", "trash_xl")
coroutines = []
year = 1957
frame_width = 1
centering = 2


async def sleep(tics=1):
    for _ in range(tics):
        await asyncio.sleep(0)


async def show_year(canvas):
    global year

    while True:
        canvas.addstr(2, 2, str(year))
        canvas.refresh()
        await sleep(2)
        year += 1


async def show_gameover(canvas):
    row, column = canvas.getmaxyx()
    canvas.addstr(
        round(row / 2),
        round(column / 2),
        """ 
   _____                         ____                 
  / ____|                       / __ \                 
 | |  __  __ _ _ __ ___   ___  | |  | |_   _____ _ __ 
 | | |_ |/ _` | '_ ` _ \ / _ \ | |  | \ \ / / _ \ '__|
 | |__| | (_| | | | | | |  __/ | |__| |\ V /  __/ |   
  \_____|\__,_|_| |_| |_|\___|  \____/  \_/ \___|_|                                                         
                                                      """,
    )
    canvas.refresh()


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), "*")
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), "O")
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), " ")

    row += rows_speed
    column += columns_speed

    symbol = "-" if columns_speed else "|"

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - frame_width, columns - frame_width

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        for ob in obstacles:
            if ob.has_collision(row, column):
                global obstacles_in_last_collisions
                obstacles_in_last_collisions.append(ob)
                await explode(canvas, row, column)
                return
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), " ")
        row += rows_speed
        column += columns_speed


async def blink(canvas, row, column, offset_tics, symbol="*"):
    while True:
        await sleep(offset_tics)

        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(20)

        canvas.addstr(row, column, symbol)
        await sleep(3)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(5)

        canvas.addstr(row, column, symbol)
        await sleep(3)


async def animate_spaceship(canvas, row, column, frame1, frame2):
    # с учетом рамки левый верх 1,1
    # левый низ row_max-1-row_f, 1
    # правый верх 1, column_max-1-column_f
    # правый низ  row_max-1-row_f, column_max-1-column_f

    row_max, column_max = canvas.getmaxyx()
    row_f1, column_f1 = get_frame_size(frame1)
    row_f2, column_f2 = get_frame_size(frame2)
    row_f = max(row_f1, row_f2)
    column_f = max(column_f1, column_f2)
    row_speed = column_speed = 0

    for frame in cycle(
        (
            frame1,
            frame1,
            frame2,
            frame2,
        )
    ):
        for ob in obstacles:
            if ob.has_collision(row, column):
                await show_gameover(canvas)
                return
        row_new, column_new, flag = read_controls(canvas)

        if flag and year > 2020:
            coroutines.append(fire(canvas, row, column))

        # плавное управление скоростью корабля
        if row_new == -1:
            row_speed, column_speed = update_speed(row_speed, column_speed, -1, 0)

        if row_new == 1:
            row_speed, column_speed = update_speed(row_speed, column_speed, 1, 0)

        if column_new == -1:
            row_speed, column_speed = update_speed(row_speed, column_speed, 0, -1)

        if column_new == 1:
            row_speed, column_speed = update_speed(row_speed, column_speed, 0, 1)

        row = min(max(1, row + row_speed), row_max - frame_width - row_f)
        column = min(max(1, column + column_speed), column_max - frame_width - column_f)

        draw_frame(canvas, row, column, frame)

        await asyncio.sleep(0)

        draw_frame(
            canvas,
            row,
            column,
            frame,
            negative=True,
        )


async def fill_orbit_with_garbage(canvas, garbage_frames):
    global coroutines
    global year
    row_max, column_max = canvas.getmaxyx()
    while True:
        column_random = random.randint(1, column_max - frame_width)
        garbage_frame = random.choice(garbage_frames)
        coroutines.append(
            fly_garbage(
                canvas,
                column=column_random,
                garbage_frame=garbage_frame,
            )
        )
        await sleep(get_garbage_delay_tics(year))


def draw(canvas):
    with open("./file/rocket_frame_1.txt", "r") as f:
        rocket_frame_1 = f.read()

    with open("./file/rocket_frame_2.txt", "r") as f:
        rocket_frame_2 = f.read()

    garbage_frames = []
    for item in GARBAGE:
        with open(f"./file/{item}.txt", "r") as g:
            garbage_frames.append(g.read())

    row, column = canvas.getmaxyx()
    # сделать ввод неблокирующим
    canvas.nodelay(True)
    canvas.border()
    star = "+*.:"

    global coroutines
    coroutines = [
        fill_orbit_with_garbage(canvas, garbage_frames),
        fire(canvas, round(row / 2), round(column / 2)),
        animate_spaceship(
            canvas,
            round(row / 2),
            round(column / 2) - centering,
            rocket_frame_1,
            rocket_frame_2,
        ),
        show_year(canvas),
    ]
    for _ in range(50):
        coroutines.append(
            blink(
                canvas,
                random.randint(1, row - centering),
                random.randint(1, column - centering),
                random.randint(1, 20),
                random.choice(star),
            )
        )

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.refresh()
        time.sleep(TICK_TIMEOUT)

        if len(coroutines) == 0:
            break


if __name__ == "__main__":
    screen = curses.initscr()
    curses.update_lines_cols()
    curses.curs_set(False)
    curses.wrapper(draw)
