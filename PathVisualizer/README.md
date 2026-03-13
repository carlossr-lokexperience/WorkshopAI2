# A* Pathfinding Visualizer

A clean, interactive, and responsive A* pathfinding visualizer built with **Python** and **Pygame**, featuring real-time
rendering, dynamic grid resizing, and a polished UI. Click to place walls, set start/end nodes, and watch A* do its
thing.

---

## ✨ Features

- Interactive grid with live A* visualization
- Fully resizable, square-centered UI
- Supports wall placement and path reset
- Color-coded pathfinding states
- Instruction overlay and popup
- Clean modular code (great for extending)

## 📦 Setup (via Poetry)

> Requires Python 3.8+

```bash
git clone https://github.com/Harithmh/pathfinder-visualizer.git
cd pathfinder-visualizer



# Run the app
python main.py
```

---

## 🎮 Controls

| Action            | Key / Mouse |
|-------------------|-------------|
| Place Start / End | Left Click  |
| Place Wall        | Left Click  |
| Remove Node       | Right Click |
| Start Pathfinding | `SPACE`     |
| Clear Grid        | `C`         |

---

## 🎨 Color Legend

| State      | Color     |
|------------|-----------|
| Start      | Orange    |
| End        | Turquoise |
| Wall       | Black     |
| Open       | Green     |
| Closed     | Red       |
| Final Path | Purple    |

---

## 🧩 Future Ideas

- Dijkstra + BFS/DFS toggle
- Weighted grids & terrain
- Maze generation
- Dark mode toggle
- Export path as steps
