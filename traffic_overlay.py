import re
import urllib.request, json
from google_maps_polyline import decode as decode_polyline
#import pprint
from webscreenshot import WebScreenShot

def _write_traffic_html(latbnd, lngbnd, filename):
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
        f.write(re.sub(r"BOUNDSHERE", s, template))


def traffic_overlay(waypoints, time, wait=5):
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
    _write_traffic_html((min(lats), max(lats)), (min(lngs), max(lngs)), html_file)

    # take screenshot
    S = WebScreenShot()
    image = S.capture(html_file, wait=wait)

    # bounds are returned in a cookie (ohh la la)
    cookie = S.get_cookies()
    bounds = json.loads(cookie[0])['k']
    print(bounds)

    # save an image for fun
    img_file = "_img.jpg"
    image.save(img_file)


if __name__ =="__main__":
    waypoints = ["104 West St. New York, NY", "288 West St. New York, NY", "Lincoln Tunnel New York, NY"]
    traffic_overlay(waypoints, 0, wait=20)
