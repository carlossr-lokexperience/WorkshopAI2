import pygame

from colors import WHITE, GREY
from node import Node


def make_grid(rows, grid_size):
    gap = grid_size // rows
    return [[Node(i, j, gap, rows) for j in range(rows)] for i in range(rows)]


def draw_grid(win, rows, effective_grid_size, x_offset, y_offset):
    gap = effective_grid_size // rows

    for i in range(rows + 1):
        pygame.draw.line(
            win,
            GREY,
            (x_offset, y_offset + i * gap),
            (x_offset + effective_grid_size, y_offset + i * gap)
        )
        pygame.draw.line(
            win,
            GREY,
            (x_offset + i * gap, y_offset),
            (x_offset + i * gap, y_offset + effective_grid_size)
        )


def draw(win, grid, rows, window_width, window_height, overlay_callback=None):
    win.fill(WHITE)

    grid_size = min(window_width, window_height)
    gap = grid_size // rows
    effective_grid_size = gap * rows

    x_offset = (window_width - effective_grid_size) // 2
    y_offset = (window_height - effective_grid_size) // 2

    for row in grid:
        for node in row:
            rect = pygame.Rect(
                node.col * gap + x_offset,
                node.row * gap + y_offset,
                gap,
                gap
            )
            pygame.draw.rect(win, node.color, rect)

    draw_grid(win, rows, effective_grid_size, x_offset, y_offset)

    if overlay_callback is not None:
        overlay_callback()

    pygame.display.update()


def get_clicked_pos(pos, rows, window_width, window_height):
    x, y = pos

    grid_size = min(window_width, window_height)
    gap = grid_size // rows
    effective_grid_size = gap * rows

    x_offset = (window_width - effective_grid_size) // 2
    y_offset = (window_height - effective_grid_size) // 2

    if (
        x < x_offset or x >= x_offset + effective_grid_size or
        y < y_offset or y >= y_offset + effective_grid_size
    ):
        return None, None

    row = (y - y_offset) // gap
    col = (x - x_offset) // gap

    if row < 0 or row >= rows or col < 0 or col >= rows:
        return None, None

    return row, col