import folium
import webbrowser

from OSMPythonTools.overpass import Overpass








map = folium.Map(location=[40, -95], zoom_start=4)









# --------------------------------------------auto_open-----------------------------------------------------------------
def auto_open(path, f_map):
    html_page = f'{path}'
    f_map.save(html_page)
    new = 2
    webbrowser.open(html_page, new=new)
# --------------------------------------------auto_open-----------------------------------------------------------------


auto_open('/Users/xXxMrMayhemxXx/Desktop/map.html', map)