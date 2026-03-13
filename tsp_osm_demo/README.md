# TSP Urban Demo (OpenStreetMap + Streamlit)

A workshop-friendly visual demo of the Traveling Salesperson Problem (TSP) on a **real street network** using **OpenStreetMap**, **OSMnx**, **OR-Tools**, **Folium**, and **Streamlit**.

## What it does

- Loads a real drivable road network for a selected city/neighborhood.
- Lets users add stops by **address** or by **clicking on the map**.
- Snaps stops to the nearest street node.
- Computes shortest-path distances through the road network.
- Solves a **real TSP** (visit all stops and return to depot).
- Draws both:
  - the **manual / insertion order route**
  - the **optimized TSP route**
- Shows key metrics: total distance, route order, and improvement.

## Install

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

## Notes

- Internet is needed the first time a place graph is downloaded from OpenStreetMap/Overpass.
- Smaller places load faster and are better for live demos.
- Good workshop examples:
  - Sol, Madrid, Spain
  - Eixample, Barcelona, Spain
  - Salamanca, Madrid, Spain
  - Centro, Valencia, Spain

## Suggested flow for a live workshop

1. Load a neighborhood.
2. Add 6-12 stops.
3. Show the naive order route.
4. Solve the TSP.
5. Compare distances and discuss why street routing differs from straight-line routing.
