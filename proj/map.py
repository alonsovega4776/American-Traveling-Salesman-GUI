from flask import Flask, render_template, request
from jinja2 import Template
import folium
from folium.plugins import Draw
from folium import plugins
import webbrowser
import numpy as np
from itertools import combinations, product
import gurobipy as guro
from gurobipy import GRB

app = Flask(__name__)


class PopUp(folium.LatLngPopup):
    _template = Template("""
                {% macro script(this, kwargs) %}
                    var {{this.get_name()}} = L.popup({keepInView:false, 
                                                       closeButton:true, 
                                                       autoClose:false, 
                                                       closeOnClick:true});
                    
                    function latLngPop(e) {
                        url = "/map/?lat=" + e.latlng.lat.toFixed(10) + "&long=" + e.latlng.lng.toFixed(10);
                        {{this.get_name()}}
                            .setLatLng(e.latlng)
                            .setContent('<a href="' + url + '" target="_blank">Add Location</a>')
                            .openOn({{this._parent.get_name()}});
                        }
                    {{this._parent.get_name()}}.on('click', latLngPop);
                    
                {% endmacro %}
                """)


locations = []
coordinates = {}

detroit = [42.3316, -83.0467]

folium_map = folium.Map(location=detroit, zoom_start=8)

draw = Draw()
draw.add_to(folium_map)

fmtr = "function(num) {return L.Util.formatNum(num, 3) + ' deg ';};"
mouse = plugins.MousePosition(position='topright',
                              separator=' ',
                              num_digits=10,
                              prefix="Current Location:",
                              lat_formatter=fmtr, lng_formatter=fmtr)
mouse.add_to(folium_map)


@app.route('/')
def index():
    folium_map.add_child(PopUp())

    map = folium_map._repr_html_()
    return render_template('map.html', map=map)


@app.route('/map/')
def get_coord():
    lat = request.args.get('lat', '')
    long = request.args.get('long', '')

    coordinates[len(coordinates.keys())] = (float(lat), float(long))
    locations.append(len(coordinates)-1)

    if len(locations) > 5:
        debug = False


    folium_map.add_child(folium.CircleMarker(location=coordinates[locations[len(locations)-1]],
                                             color='blue',
                                             radius=5,
                                             fill='true',
                                             fill_color='black',
                                             tooltip=locations[len(locations)-1]))

    message = {"lat": lat, "long": long}
    return render_template('coor.html', message=message)



if __name__ == '__main__':
    app.run(debug=True)


# Data *****************************************************************************************************************
# --------------------------------------------distance------------------------------------------------------------------
def distance(i_1, i_2):
    Δ = tuple(map(lambda i, j: i-j, coordinates[i_1], coordinates[i_2]))
    return np.linalg.norm(Δ, ord=2)
# --------------------------------------------distance------------------------------------------------------------------


distance_dict = {(i_1, i_2): distance(i_1, i_2)
                                             for (i_1, i_2) in product(locations, locations)
                                             if i_1 != i_2}

# No Sub-tours *********************************************************************************************************
# --------------------------------------------get_cycle-----------------------------------------------------------------
def get_cycle(edge_list):
    unvisited = locations[:]
    ciclo = locations[:]
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

        if len(sol_tour) < len(locations):
            model.cbLazy(guro.quicksum(model._vars[i_1, i_2]
                                       for (i_1, i_2) in combinations(sol_tour, 2)) <= len(sol_tour)-1)
# --------------------------------------------subTour_eliminator--------------------------------------------------------


# Model ****************************************************************************************************************

model = guro.Model()

des_vars = model.addVars(distance_dict.keys(), obj=distance_dict, vtype=GRB.BINARY, name='x')

for (i, j) in des_vars.keys():
    model.addConstr(des_vars[j, i] == des_vars[i, j])

model.addConstrs(des_vars.sum(k, '*') == 2 for k in locations)

model._vars = des_vars
model.Params.lazyConstraints = 1
model.optimize(subTour_eliminator)

# Analysis *************************************************************************************************************

vals = model.getAttr('x', des_vars)
selected = guro.tuplelist((i, j) for (i, j) in vals.keys() if vals[i, j] > 0.5)

tour = get_cycle(selected)
assert len(tour) == len(locations)

points = []
for city in tour:
    points.append(coordinates[city])
points.append(points[0])

ant_path = plugins.AntPath(points, tooltip='hello',
                                   color='white',
                                   pulse_color='crimson',
                                   dash_array=[11, 15],
                                   delay=800,
                                   weight=4)

ant_path.add_to(folium_map)

# Every Possible Path
combo = [(i, j) for (i, j) in product(locations, locations) if i != j]
for (i, j) in combo:
    folium.PolyLine([coordinates[i], coordinates[j]], color='black', weight=3.0, opacity=0.175).add_to(folium_map)


# --------------------------------------------auto_open-----------------------------------------------------------------
def auto_open(path, f_map):
    html_page = f'{path}'
    f_map.save(html_page)
    new = 2
    webbrowser.open(html_page, new=new)
# --------------------------------------------auto_open-----------------------------------------------------------------


auto_open('/Users/xXxMrMayhemxXx/Desktop/map.html', folium_map)

print('ENDDDDDD')


