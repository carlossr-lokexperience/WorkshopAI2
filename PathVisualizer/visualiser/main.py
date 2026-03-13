import pygame

from algorithms import a_star, dijkstra, bfs, dfs, greedy_best_first
from grid import make_grid, draw, get_clicked_pos

pygame.font.init()
FONT = pygame.font.SysFont("consolas", 20)
BIGFONT = pygame.font.SysFont("consolas", 28)

ROWS = 50

ALGORITHM_NAMES = {
    "astar": "A*",
    "dijkstra": "Dijkstra",
    "bfs": "BFS",
    "dfs": "DFS",
    "greedy": "Greedy Best-First"
}


def draw_text_overlay(win, current_algorithm, screen_width):
    overlay_height = 34
    overlay_surface = pygame.Surface((screen_width, overlay_height))
    overlay_surface.set_alpha(230)
    overlay_surface.fill((245, 245, 245))
    win.blit(overlay_surface, (0, 0))

    text = FONT.render(
        f"Algorithm: {ALGORITHM_NAMES[current_algorithm]} | "
        f"[1] A*  [2] Dijkstra  [3] BFS  [4] DFS  [5] Greedy  | "
        f"[SPACE] Run  [C] Clear",
        True,
        (30, 30, 30)
    )
    win.blit(text, ((screen_width - text.get_width()) // 2, 8))


def draw_start_popup(win, width, height):
    win.fill((240, 240, 240))
    title = BIGFONT.render("Pathfinding Visualizer", True, (0, 0, 0))
    win.blit(title, ((width - title.get_width()) // 2, 50))

    lines = [
        "Welcome, pathfinding wizard!",
        "",
        "[LEFT CLICK]  : Place start, end, and walls",
        "[RIGHT CLICK] : Remove nodes",
        "",
        "[1] : Select A*",
        "[2] : Select Dijkstra",
        "[3] : Select BFS",
        "[4] : Select DFS",
        "[5] : Select Greedy Best-First",
        "",
        "[SPACE] : Run selected algorithm",
        "[C]     : Clear the grid",
        "",
        "Start  = ORANGE",
        "End    = TURQUOISE",
        "Wall   = BLACK",
        "Open   = GREEN",
        "Closed = RED",
        "Path   = PURPLE",
        "",
        "Press any key to begin..."
    ]

    start_y = 120
    line_gap = 28

    for i, line in enumerate(lines):
        text = FONT.render(line, True, (30, 30, 30))
        win.blit(text, ((width - text.get_width()) // 2, start_y + i * line_gap))

    pygame.display.update()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                waiting = False


def run_selected_algorithm(current_algorithm, win, grid, start, end, screen_width, screen_height):
    for row in grid:
        for node in row:
            node.update_neighbors(grid)

    draw_callback = lambda: draw(
        win,
        grid,
        ROWS,
        screen_width,
        screen_height,
        lambda: draw_text_overlay(win, current_algorithm, screen_width)
    )

    if current_algorithm == "astar":
        return a_star(draw_callback, grid, start, end)
    elif current_algorithm == "dijkstra":
        return dijkstra(draw_callback, grid, start, end)
    elif current_algorithm == "bfs":
        return bfs(draw_callback, grid, start, end)
    elif current_algorithm == "dfs":
        return dfs(draw_callback, grid, start, end)
    elif current_algorithm == "greedy":
        return greedy_best_first(draw_callback, grid, start, end)

    return False


def main():
    pygame.init()
    info = pygame.display.Info()
    screen_width = min(900, info.current_w - 100)
    screen_height = min(900, info.current_h - 100)

    win = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
    pygame.display.set_caption("Pathfinding Visualizer - A*")

    draw_start_popup(win, screen_width, screen_height)

    grid_size = min(screen_width, screen_height)
    grid = make_grid(ROWS, grid_size)
    start = None
    end = None
    current_algorithm = "astar"
    run = True

    while run:
        grid_size = min(screen_width, screen_height)

        draw(
            win,
            grid,
            ROWS,
            screen_width,
            screen_height,
            lambda: draw_text_overlay(win, current_algorithm, screen_width)
        )

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            elif event.type == pygame.VIDEORESIZE:
                screen_width = event.w
                screen_height = event.h
                win = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)

                grid_size = min(screen_width, screen_height)
                grid = make_grid(ROWS, grid_size)
                start = None
                end = None

            elif pygame.mouse.get_pressed()[0]:
                pos = pygame.mouse.get_pos()
                row, col = get_clicked_pos(pos, ROWS, screen_width, screen_height)
                if row is None or col is None:
                    continue

                node = grid[row][col]

                if not start and node != end:
                    start = node
                    start.make_start()
                elif not end and node != start:
                    end = node
                    end.make_end()
                elif node != end and node != start:
                    node.make_barrier()

            elif pygame.mouse.get_pressed()[2]:
                pos = pygame.mouse.get_pos()
                row, col = get_clicked_pos(pos, ROWS, screen_width, screen_height)
                if row is None or col is None:
                    continue

                node = grid[row][col]

                if node == start:
                    start = None
                elif node == end:
                    end = None

                node.reset()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    current_algorithm = "astar"
                    pygame.display.set_caption(f"Pathfinding Visualizer - {ALGORITHM_NAMES[current_algorithm]}")

                elif event.key == pygame.K_2:
                    current_algorithm = "dijkstra"
                    pygame.display.set_caption(f"Pathfinding Visualizer - {ALGORITHM_NAMES[current_algorithm]}")

                elif event.key == pygame.K_3:
                    current_algorithm = "bfs"
                    pygame.display.set_caption(f"Pathfinding Visualizer - {ALGORITHM_NAMES[current_algorithm]}")

                elif event.key == pygame.K_4:
                    current_algorithm = "dfs"
                    pygame.display.set_caption(f"Pathfinding Visualizer - {ALGORITHM_NAMES[current_algorithm]}")

                elif event.key == pygame.K_5:
                    current_algorithm = "greedy"
                    pygame.display.set_caption(f"Pathfinding Visualizer - {ALGORITHM_NAMES[current_algorithm]}")

                elif event.key == pygame.K_SPACE and start and end:
                    run_selected_algorithm(
                        current_algorithm,
                        win,
                        grid,
                        start,
                        end,
                        screen_width,
                        screen_height
                    )

                elif event.key == pygame.K_c:
                    start = None
                    end = None
                    grid = make_grid(ROWS, grid_size)

    pygame.quit()


if __name__ == "__main__":
    main()