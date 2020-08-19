import folium
from flask import Flask, render_template, request
from jinja2 import Template


app = Flask(__name__)


class CustomPopup(folium.LatLngPopup):
    _template = Template(u"""
                {% macro script(this, kwargs) %}
                    var {{this.get_name()}} = L.popup();
                    function latLngPop(e) {
                        url = "/map/?lat=" + e.latlng.lat.toFixed(4) + "&long=" + e.latlng.lng.toFixed(4);
                        {{this.get_name()}}
                            .setLatLng(e.latlng)
                            .setContent('<a href="' + url + '" target="_blank">add</a>')
                            .openOn({{this._parent.get_name()}});
                        }
                    {{this._parent.get_name()}}.on('click', latLngPop);
                {% endmacro %}
                """)


@app.route('/')
def index():
    detroit = [42.3316, -83.0467]
    folium_map = folium.Map(location=detroit, tiles="OpenStreetMap", zoom_start=8)
    folium_map.add_child(CustomPopup())
    map = folium_map._repr_html_()
    return render_template('map.html', map=map)


@app.route('/map/')
def map():
    lat = request.args.get('lat', '')
    long = request.args.get('long', '')
    print(lat, long)
    message = {"lat": lat, "long": long}
    return render_template('coor.html', message=message)


if __name__ == '__main__':
    app.run(debug=True)



