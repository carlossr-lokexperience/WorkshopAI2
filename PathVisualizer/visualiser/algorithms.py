from queue import PriorityQueue, Queue, LifoQueue

import pygame


def h(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    return abs(x1 - x2) + abs(y1 - y2)


def reconstruct_path(came_from, current, draw, start):
    while current in came_from:
        current = came_from[current]
        if current != start:
            current.make_path()
        draw()


def a_star(draw, grid, start, end):
    count = 0
    open_set = PriorityQueue()
    open_set.put((0, count, start))

    came_from = {}

    g_score = {node: float("inf") for row in grid for node in row}
    g_score[start] = 0

    f_score = {node: float("inf") for row in grid for node in row}
    f_score[start] = h(start.get_pos(), end.get_pos())

    open_set_hash = {start}

    while not open_set.empty():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()

        current = open_set.get()[2]
        open_set_hash.remove(current)

        if current == end:
            reconstruct_path(came_from, end, draw, start)
            end.make_end()
            start.make_start()
            return True

        for neighbor in current.neighbors:
            temp_g = g_score[current] + 1

            if temp_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = temp_g
                f_score[neighbor] = temp_g + h(neighbor.get_pos(), end.get_pos())

                if neighbor not in open_set_hash:
                    count += 1
                    open_set.put((f_score[neighbor], count, neighbor))
                    open_set_hash.add(neighbor)

                    if neighbor != end:
                        neighbor.make_open()

        draw()

        if current != start:
            current.make_closed()

    return False


def dijkstra(draw, grid, start, end):
    count = 0
    open_set = PriorityQueue()
    open_set.put((0, count, start))

    came_from = {}
    dist = {node: float("inf") for row in grid for node in row}
    dist[start] = 0

    open_set_hash = {start}

    while not open_set.empty():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()

        current = open_set.get()[2]
        open_set_hash.remove(current)

        if current == end:
            reconstruct_path(came_from, end, draw, start)
            end.make_end()
            start.make_start()
            return True

        for neighbor in current.neighbors:
            new_dist = dist[current] + 1

            if new_dist < dist[neighbor]:
                came_from[neighbor] = current
                dist[neighbor] = new_dist

                if neighbor not in open_set_hash:
                    count += 1
                    open_set.put((dist[neighbor], count, neighbor))
                    open_set_hash.add(neighbor)

                    if neighbor != end:
                        neighbor.make_open()

        draw()

        if current != start:
            current.make_closed()

    return False


def bfs(draw, grid, start, end):
    queue = Queue()
    queue.put(start)

    came_from = {}
    visited = {start}

    while not queue.empty():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()

        current = queue.get()

        if current == end:
            reconstruct_path(came_from, end, draw, start)
            end.make_end()
            start.make_start()
            return True

        for neighbor in current.neighbors:
            if neighbor not in visited:
                visited.add(neighbor)
                came_from[neighbor] = current
                queue.put(neighbor)

                if neighbor != end:
                    neighbor.make_open()

        draw()

        if current != start:
            current.make_closed()

    return False


def dfs(draw, grid, start, end):
    stack = LifoQueue()
    stack.put(start)

    came_from = {}
    visited = {start}

    while not stack.empty():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()

        current = stack.get()

        if current == end:
            reconstruct_path(came_from, end, draw, start)
            end.make_end()
            start.make_start()
            return True

        for neighbor in current.neighbors:
            if neighbor not in visited:
                visited.add(neighbor)
                came_from[neighbor] = current
                stack.put(neighbor)

                if neighbor != end:
                    neighbor.make_open()

        draw()

        if current != start:
            current.make_closed()

    return False


def greedy_best_first(draw, grid, start, end):
    count = 0
    open_set = PriorityQueue()
    open_set.put((h(start.get_pos(), end.get_pos()), count, start))

    came_from = {}
    visited = {start}

    while not open_set.empty():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()

        current = open_set.get()[2]

        if current == end:
            reconstruct_path(came_from, end, draw, start)
            end.make_end()
            start.make_start()
            return True

        for neighbor in current.neighbors:
            if neighbor not in visited:
                visited.add(neighbor)
                came_from[neighbor] = current
                count += 1
                priority = h(neighbor.get_pos(), end.get_pos())
                open_set.put((priority, count, neighbor))

                if neighbor != end:
                    neighbor.make_open()

        draw()

        if current != start:
            current.make_closed()

    return False