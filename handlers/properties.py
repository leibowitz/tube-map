from tornado import gen
import tornado.web
import json
import zoopla
import urllib.parse
import math
import requests

api = zoopla.api(version=1, api_key='API_KEY')
proxies={'http': 'http://127.0.0.1:8989'}

def list_properties_trovit(latitude, longitude, radius, min_bedrooms, min_bathrooms, min_price, max_price):
    headers = {'x-client-id': 'CLIENT_ID'}
    #print(latitude, longitude, radius)
    (lat_min, lon_min, lat_max, lon_max) = boundingBox(latitude, longitude, (radius/1.6))
    payload = {
            'longitude_max': lon_max,
            'longitude_min': lon_min,
            'latitude_max': lat_max,
            'latitude_min': lat_min,
            'rooms_min': min_bedrooms,
            'from': 'map',
            'type': 1,
            'bathrooms_min': min_bathrooms,
            'country': 'uk',
            'order': 'relevance',
            #'per_page': 50,
            'price_min': min_price,
            #'new_homes': True,
            'price_max': max_price
    }
    r = requests.get('https://api.trovit.com:443/v2/homes/ads', headers=headers, params=payload)
    for listing in r.json()["ads"]:
        new_home = True if 'is_new' in listing and listing['is_new'] and listing['is_new'] == 1 else False
        photo = listing['photos']["medium"]["url"] if 'photos' in listing else None
        yield {"latitude": listing['latitude'], "longitude": listing['longitude'], "price": int(listing['price']), "id": listing['id'], "url": listing['url'], "description": listing['description'], "address": listing['title'], "image": photo, "floor_plans": listing['floor_plan'] if 'floor_plan' in listing and listing['floor_plan'] else [], "new_home": new_home}

def list_properties_zoopla(latitude, longitude, radius, min_bedrooms, min_bathrooms, min_price, max_price):

    for listing in api.property_listings(
            #postcode=args.postcode,
            latitude=latitude,
            longitude=longitude,
            radius=radius,
            property_type='flats',
            new_homes="yes",
            minimum_price=min_price,
            maximum_price=max_price,
            minimum_beds=min_bedrooms,
            listing_status='sale',
            proxies=proxies,
            max_results=10):

        bathrooms = int(listing.num_bathrooms)
        if bathrooms < min_bathrooms:
            continue
        new_home = True if listing.new_home and listing.new_home == "true" else False
        #print("bathrooms: {}, street: {}, new home: {}, price: {}, details_url: {}".format(
        #    listing.num_bathrooms,
        #    listing.street_name,
        #    listing.new_home if listing.new_home else False,
        #    listing.price,
        #    listing.details_url,
        #    #listing.short_description,
        #    #listing.floor_plan,
        #))
        u = urllib.parse.urlparse(listing.details_url)
        #u.query = None
        details_url = u._replace(query=None).geturl()
        yield {"latitude": listing.latitude, "longitude": listing.longitude, "price": int(listing.price), "id": listing.listing_id, "url": details_url, "description": listing.short_description, "address": listing.displayable_address, "image": listing.thumbnail_url, "floor_plans": listing.floor_plan if listing.floor_plan else [], "new_home": new_home}


class PropertiesHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @gen.engine
    def get(self):
        if 'X-Requested-With' not in self.request.headers or self.request.headers['X-Requested-With'] != "XMLHttpRequest":
            return
        latitude = float(self.get_argument('latitude', 0))
        longitude = float(self.get_argument('longitude', 0))
        radius = float(self.get_argument('radius', 0))
        min_price = int(self.get_argument('min_price', 500000))
        max_price = int(self.get_argument('max_price', 600000))
        min_bed = int(self.get_argument('min_bed', 2))
        min_bath = int(self.get_argument('min_bath', 2))

        source = self.get_argument('source', 'trovit')
        if source == 'zoopla':
            func = list_properties_zoopla
        else:
            func = list_properties_trovit

        results = list(func(latitude, longitude, radius, min_bed, min_bath, min_price, max_price))

        self.write(json.dumps(results))
        self.finish()


# degrees to radians
def deg2rad(degrees):
    return math.pi*degrees/180.0
# radians to degrees
def rad2deg(radians):
    return 180.0*radians/math.pi

# Semi-axes of WGS-84 geoidal reference
WGS84_a = 6378137.0  # Major semiaxis [m]
WGS84_b = 6356752.3  # Minor semiaxis [m]

# Earth radius at a given latitude, according to the WGS-84 ellipsoid [m]
def WGS84EarthRadius(lat):
    # http://en.wikipedia.org/wiki/Earth_radius
    An = WGS84_a*WGS84_a * math.cos(lat)
    Bn = WGS84_b*WGS84_b * math.sin(lat)
    Ad = WGS84_a * math.cos(lat)
    Bd = WGS84_b * math.sin(lat)
    return math.sqrt( (An*An + Bn*Bn)/(Ad*Ad + Bd*Bd) )

# Bounding box surrounding the point at given coordinates,
# assuming local approximation of Earth surface as a sphere
# of radius given by WGS84
def boundingBox(latitudeInDegrees, longitudeInDegrees, halfSideInKm):
    lat = deg2rad(latitudeInDegrees)
    lon = deg2rad(longitudeInDegrees)
    halfSide = 1000*halfSideInKm

    # Radius of Earth at given latitude
    radius = WGS84EarthRadius(lat)
    # Radius of the parallel at given latitude
    pradius = radius*math.cos(lat)

    latMin = lat - halfSide/radius
    latMax = lat + halfSide/radius
    lonMin = lon - halfSide/pradius
    lonMax = lon + halfSide/pradius

    return (rad2deg(latMin), rad2deg(lonMin), rad2deg(latMax), rad2deg(lonMax))
