import numpy as np
import gurobipy as guro
from gurobipy import GRB
import json
import folium
from itertools import combinations, product
import webbrowser


# Get Data *************************************************************************************************************
capitals_json = json.load(open('/Users/xXxMrMayhemxXx/Documents/GitHub/RideSharing-Autonomous-Mobility-Optimizer-/project/us_state_capitals.json'))
capitals = []                                           # [lansing, denver, ....]
coordinates = {}                                        # capital |--> (lat, long)
for state in capitals_json:
    if state not in ['AK', 'HI']:
        capital = capitals_json[state]['capital']
        capitals.append(capital)
        coordinates[capital] = (float(capitals_json[state]['lat']), float(capitals_json[state]['long']))


# --------------------------------------------distance------------------------------------------------------------------
def distance(capital_1, capital_2):
    Δ = tuple(map(lambda i, j: i-j, coordinates[capital_2], coordinates[capital_1]))
    return np.linalg.norm(Δ, ord=2)
# --------------------------------------------distance------------------------------------------------------------------


distance_dict = {(c_1, c_2): distance(c_1, c_2)         # (capital_1, capital_2) |--> REAL NUMBERS
                 for (c_1, c_2) in product(capitals, capitals)
                 if c_1 != c_2}                         # (c_1, c_2) in Capitals^2

all_tours = []
# --------------------------------------------subTour_eliminator--------------------------------------------------------
def subTour_eliminator(model, where):
    if where == GRB.Callback.MIPSOL:                                                # possible solution
        values = model.cbGetSolution(model._vars)
        selected_nodes = guro.tuplelist((i_1, i_2)
                                  for (i_1, i_2) in model._vars.keys()
                                  if values[i_1, i_2] > 0.5)

        sol_tour = get_cycle(selected_nodes)
        all_tours.append(sol_tour)

        if len(sol_tour) < len(capitals):
            model.cbLazy(guro.quicksum(model._vars[i_1, i_2]
                                       for (i_1, i_2) in combinations(sol_tour, 2)) <= len(sol_tour)-1)
# --------------------------------------------subTour_eliminator--------------------------------------------------------


# --------------------------------------------get_cycle-----------------------------------------------------------------
def get_cycle(edge_list):
    unvisited = capitals[:]
    ciclo = capitals[:]
    while unvisited:
        this_cycle = []
        neighbors = unvisited
        while neighbors:
            current = neighbors[0]
            this_cycle.append(current)
            unvisited.remove(current)
            neighbors = [j
                         for (i, j) in edge_list.select(current, '*')
                         if j in unvisited]
        if len(this_cycle) <= len(ciclo):
            ciclo = this_cycle
    return ciclo
# --------------------------------------------get_cycle-----------------------------------------------------------------


# Model ****************************************************************************************************************

model = guro.Model()

des_vars = model.addVars(distance_dict.keys(), obj=distance_dict, vtype=GRB.BINARY, name='x')

for (i, j) in des_vars.keys():
    model.addConstr(des_vars[j, i] == des_vars[i, j])

model.addConstrs(des_vars.sum(c, '*') == 2 for c in capitals)

model._vars = des_vars
model.Params.lazyConstraints = 1
model.optimize(subTour_eliminator)


# Analysis *************************************************************************************************************

vals = model.getAttr('x', des_vars)
selected = guro.tuplelist((i, j) for i, j in vals.keys() if vals[i, j] > 0.5)

tour = get_cycle(selected)
assert len(tour) == len(capitals)

map = folium.Map(location=[40, -95], zoom_start=4)

# Every Possible Path
combo = [(i, j) for (i, j) in product(capitals, capitals) if i != j]
for (i, j) in combo:
    folium.PolyLine([coordinates[i], coordinates[j]], color='black', weight=1.0, opacity=0.075).add_to(map)

points = []
for city in tour:
    points.append(coordinates[city])

folium.PolyLine(points, color="blue", weight=2.5, opacity=0.35).add_to(map)
folium.PolyLine([points[0], points[len(points)-1]], color="blue", weight=2.5, opacity=0.35).add_to(map)




count = 0
for each in points:
    popup_text = "{}<br> Latitude: {:,}<br> Longitude: {:,}"
    popup_text = popup_text.format(
        tour[count],
        each[0],
        each[1]
    )
    map.add_child(folium.CircleMarker(location=each,
                                      fill='true',
                                      radius = 7.5,
                                      popup=popup_text,
                                      fill_color='red',
                                      color = 'clear',
                                      fill_opacity=0.3))
    count = count + 1


# --------------------------------------------auto_open-----------------------------------------------------------------
def auto_open(path, f_map):
    html_page = f'{path}'
    f_map.save(html_page)
    new = 2
    webbrowser.open(html_page, new=new)
# --------------------------------------------auto_open-----------------------------------------------------------------


auto_open('/Users/xXxMrMayhemxXx/Desktop/map.html', map)






