def clear_grid(grid):
    for row in grid:
        for node in row:
            node.reset()
