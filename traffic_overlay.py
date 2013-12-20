import re
import urllib.request, json
import math
from google_maps_polyline import decode as decode_polyline
#import pprint
from webscreenshot import WebScreenShot
from PyQt4.QtCore import QPoint
from PyQt4.QtGui import QColor


def _write_traffic_html(latbnd, lngbnd, filename, width=1024, height=1024):
    coord = []
    for la in latbnd:
        for ln in lngbnd:
            coord.append((la, ln))

    # build coord javascript array
    coord_str = ["new google.maps.LatLng({},{})".format(c[1], c[0]) for c in coord];

    s = ", ".join(coord_str)

    # open template
    template = open("traffic_image_request_template.html", mode="r").read()
    #template = open("index.html", mode="r").read()

    # write output html file
    with open(filename, mode="w") as f:
        out = re.sub(r"BOUNDSHERE", s, template)
        out = re.sub(r"WIDTHPX", str(width), out)
        out = re.sub(r"HEIGHTPX", str(height), out)
        f.write(out)

def color_to_value(color):
    green = (55, 168, 28)
    yellow = (249, 217, 18)
    red = (125, 0, 0)
    black = (37, 20, 30)
    colors = (green, yellow, red, black)
    values = (1, 2, 3, 4)

    def nearest_color_rgb(c, colors):
        diff = [0] * len(colors)
        for i, color in enumerate(colors):
            for j in range(3):
                diff[i] += math.fabs(c[j]-color[j])
        return diff.index(max(diff))

    return values[nearest_color_rgb(color, colors)]

def traffic_overlay(waypoints, time, wait=5, debug=False):
    # sanity check
    if len(waypoints) < 2: raise ValueError

    # parse waypoints into origin, destination, and mid-waypoints
    origin = waypoints[0]
    destin = waypoints[-1]
    waypts = waypoints[1:-1]

    # build url
    url = "http://maps.googleapis.com/maps/api/directions/json?"
    f = {"origin" : origin, "destination" : destin, "waypoints" : "|".join(waypts), "sensor" : "false"}
    url += urllib.parse.urlencode(f)

    g = urllib.request.urlopen(url).read().decode()
    j = json.loads(g)
    #pprint.pprint(j)

    # error if not one route
    nroute = len(j['routes'])
    if nroute != 1: raise ValueError

    nleg = len(j['routes'][0]['legs'])
    # sanity check
    if nleg != len(waypoints)-1: raise ValueError

    coord = []
    for leg in j['routes'][0]['legs']:
        for s in leg['steps']:
            c = decode_polyline(s['polyline']['points'])
            # make sure we don't add the same point twice!
            if len(coord) > 0:
                if all([(coord[-1][i] - c[0][i]) < 1e-10 for i in range(2)]):
                    coord.extend(c[1:])
                else:
                    coord.extend(c)
            else:
                coord.extend(c)

    # temporary html file
    html_file = "_map.html"

    # find min/max lat/lng
    lats = [x[0] for x in coord]
    lngs = [x[1] for x in coord]
    img_size = (2048, 2048)
    _write_traffic_html((min(lats), max(lats)), (min(lngs), max(lngs)),
        html_file, width=2048, height=2048)

    # take screenshot
    S = WebScreenShot()
    image = S.capture(html_file, wait=wait)

    # bounds are returned in a cookie (ohh la la)
    cookie = S.get_cookies()
    bounds = json.loads(cookie[0])['k']

    # loop through polyline points and compute overlay value at each point
    image_size = [image.height(), image.width()]
    pplat = image_size[0]/(bounds['upper_right_lat']-bounds['lower_left_lat'])
    pplng = image_size[1]/(bounds['upper_right_lng']-bounds['lower_left_lng'])

    val = [0] * len(coord)
    for i, c in enumerate(coord):
        x = int((c[0] - bounds['lower_left_lng'])*pplng)
        y = int((bounds['upper_right_lat'] - c[1])*pplat)

        v = QColor(image.pixel(QPoint(x, y)))
        v_rgb = (v.red(), v.green(), v.blue())
        val[i] = color_to_value(v_rgb)

        # if debugging, change pixel color to black for each point sampled
        # and then save the image as _img.jpg
        if debug:
            image.setPixel(QPoint(x, y), 0)

    if debug:
        image.save("_img.jpg")

    print(val)


if __name__ =="__main__":
    waypoints = ["332 West St. New York, NY", "Lincoln Hwy New York, NY"]
    traffic_overlay(waypoints, 0, wait=20, debug=True)
