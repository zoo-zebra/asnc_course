import asyncio
import curses
import time
import random
from curses_tools import draw_frame, read_controls, get_frame_size
from itertools import cycle


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
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), " ")
        row += rows_speed
        column += columns_speed


async def blink(canvas, row, column, symbol="*"):
    while True:
        for _ in range(random.randint(1, 20)):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_DIM)
        for _ in range(20):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for _ in range(5):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)


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

    for item in cycle("1"):
        row_new, column_new, flag = read_controls(canvas)

        row += row_new
        column += column_new

        if not (1 < row < row_max - 1 - row_f) or not (
            1 < column < column_max - 1 - column_f
        ):
            row -= row_new
            column -= column_new

        draw_frame(canvas, row, column, frame1)
        canvas.refresh()
        await asyncio.sleep(0)

        # стираем предыдущий кадр, прежде чем рисовать новый
        draw_frame(
            canvas,
            row,
            column,
            frame1,
            negative=True,
        )
        draw_frame(canvas, row, column, frame2)
        canvas.refresh()
        await asyncio.sleep(0)

        draw_frame(
            canvas,
            row,
            column,
            frame2,
            negative=True,
        )


def draw(canvas):
    with open("z:/PYTHON CODE/asnc_course/file/rocket_frame_1.txt", "r") as f:
        rocket_frame_1 = f.read()

    with open("z:/PYTHON CODE/asnc_course/file/rocket_frame_2.txt", "r") as f:
        rocket_frame_2 = f.read()

    row, column = canvas.getmaxyx()
    TICK_TIMEOUT = 0.1
    # сделать ввод неблокирующим
    canvas.nodelay(True)
    canvas.border()
    canvas.refresh()
    star = "+*.:"

    coroutines = [
        fire(canvas, round(row / 2), round(column / 2)),
        animate_spaceship(
            canvas,
            round(row / 2),
            round(column / 2) - 2,
            rocket_frame_1,
            rocket_frame_2,
        ),
    ]
    for _ in range(50):
        coroutines.append(
            blink(
                canvas,
                random.randint(1, row - 2),
                random.randint(1, column - 2),
                random.choice(star),
            )
        )

    while True:
        try:
            for coroutine in coroutines.copy():
                coroutine.send(None)
                canvas.refresh()
            time.sleep(TICK_TIMEOUT)
        except StopIteration:
            coroutines.remove(coroutine)

        if len(coroutines) == 0:
            break


if __name__ == "__main__":
    screen = curses.initscr()
    curses.update_lines_cols()
    curses.curs_set(False)
    curses.wrapper(draw)
