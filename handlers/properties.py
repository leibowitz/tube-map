from tornado import gen
import tornado.web
import json
import zoopla
import urllib.parse
import math
import polyline
import requests

trovit_client_id = 'CLIENT_ID'
zoopla_key = 'API_KEY'
proxies={}
use_proxy = False
if use_proxy:
    proxies['http'] = 'http://127.0.0.1:8989'

api = zoopla.api(version=1, api_key=zoopla_key)

def list_properties_nestoria(latitude, longitude, radius, min_bedrooms, min_bathrooms, min_price=0, max_price=0):
    (lat_min, lon_min, lat_max, lon_max) = boundingBox(latitude, longitude, radius)
    payload = {
            'action': 'search_listings',
            'encoding': 'json',
            'south_west': '%f,%f' % (lat_min, lon_min),
            'north_east': '%f,%f' % (lat_max, lon_max),
            'bedroom_min': min_bedrooms,
            'bathroom_min': min_bathrooms,
            'listing_type': 'buy'
    }

    if min_price:
            payload['price_min'] = min_price
    if max_price:
            payload['price_max'] = max_price

    r = requests.get('http://api.nestoria.co.uk/api', params=payload, proxies=proxies)
    for listing in r.json()["response"]["listings"]:
        yield {"id": str(id(listing)), "latitude": listing['latitude'], "longitude": listing['longitude'], "price": int(listing['price']), "url": listing['lister_url'], "description": listing['summary'], "address": listing['title'], "image": listing['thumb_url'], "floor_plans": [], "new_home": False}

def list_properties_smartnewhomes(latitude, longitude, radius, min_bedrooms, min_bathrooms, min_price=0, max_price=0):
    (lat_min, lon_min, lat_max, lon_max) = boundingBox(latitude, longitude, radius)
    box = [(lat_min, lon_min), (lat_min, lon_max), (lat_max, lon_max), (lat_max, lon_min), (lat_min, lon_min)]
    new_home = True
    payload = {
            'beds_min': min_bedrooms,
            'category': 'residential',
            'include_retirement_homes': 'false',
            'include_shared_ownership': 'true',
            'new_homes': 'include',
            'q': '',
            'polyenc': [polyline.encode(box)]
    }

    if min_price:
            payload['price_min'] = min_price
    if max_price:
            payload['price_max'] = max_price

    if new_home:
        payload['section'] = "new-homes"

    headers = {'X-Requested-With': 'XMLHttpRequest'}
    r = requests.post('http://www.smartnewhomes.com/ajax/maps/listings', headers=headers, data=payload, proxies=proxies)
    properties = {}
    params = [
            ('api_key', zoopla_key)
    ]
    for listing in r.json()["listings"]:
        properties[ listing["listing_id"] ] = {"latitude": listing["lat"], "longitude": listing["lon"]}
        url = "http://www.smartnewhomes.com/new-homes/details/" + listing["listing_id"]
        url = "http://www.zoopla.co.uk/for-sale/details/" + listing["listing_id"]
        params.append(('listing_id', listing["listing_id"]))

    if len(params) != 1:
        r = requests.get('http://api.zoopla.co.uk/api/v1/property_listings.json', params=params, proxies=proxies)
        for listing in r.json()["listing"]:
            bathrooms = int(listing["num_bathrooms"])
            if bathrooms < min_bathrooms:
                continue
            new_home = True if "new_home" in listing and listing["new_home"] == "true" else False
            u = urllib.parse.urlparse(listing["details_url"])
            details_url = u._replace(query=None).geturl()
            yield {"latitude": listing['latitude'], "longitude": listing['longitude'], "price": int(listing["price"]), "id": str(listing["listing_id"]), "url": details_url, "description": listing["short_description"], "address": listing["displayable_address"], "image": listing["thumbnail_url"], "floor_plans": listing["floor_plan"] if 'floor_plan' in listing else [], "new_home": new_home}

def list_properties_trovit(latitude, longitude, radius, min_bedrooms, min_bathrooms, min_price=0, max_price=0):
    headers = {'x-client-id': trovit_client_id}
    (lat_min, lon_min, lat_max, lon_max) = boundingBox(latitude, longitude, (radius/1.6))
    new_home = True
    payload = {
            'longitude_max': lon_max,
            'longitude_min': lon_min,
            'latitude_max': lat_max,
            'latitude_min': lat_min,
            'rooms_min': min_bedrooms,
            'from': 'map',
            'type': 1, # 1 => home for sale, 2 => home for rent
            'bathrooms_min': min_bathrooms,
            'country': 'uk',
            'order': 'relevance'
            #'per_page': 50,
    }

    if min_price:
            payload['price_min'] = min_price
    if max_price:
            payload['price_max'] = max_price

    if new_home:
        payload['new_homes'] = "true"

    r = requests.get('http://api.trovit.com/v2/homes/ads', headers=headers, params=payload, proxies=proxies)
    for listing in r.json()["ads"]:
        new_home = True if 'is_new' in listing and listing['is_new'] and listing['is_new'] == 1 else False
        photo = listing['photos']["medium"]["url"] if 'photos' in listing else None
        yield {"latitude": listing['latitude'], "longitude": listing['longitude'], "price": int(listing['price']), "id": str(listing['id']), "url": listing['url'], "description": listing['description'], "address": listing['title'], "image": photo, "floor_plans": listing['floor_plan'] if 'floor_plan' in listing and listing['floor_plan'] else [], "new_home": new_home}

def list_properties_zoopla(latitude, longitude, radius, min_bedrooms, min_bathrooms, min_price=0, max_price=0):

    new_home = True
    params = {
            #'postcode': args.postcode,
            'latitude': latitude,
            'longitude': longitude,
            'radius': radius,
            'property_type': 'flats',
            'minimum_beds': min_bedrooms,
            'listing_status': 'sale',
            'proxies': proxies,
            'max_results': 10
            }

    if min_price:
            params['minimum_price'] = min_price
    if max_price:
            params['maximum_price'] = max_price

    if new_home:
        params['new_homes'] = "yes"
    for listing in api.property_listings(**params):

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
        yield {"latitude": listing.latitude, "longitude": listing.longitude, "price": int(listing.price), "id": str(listing.listing_id), "url": details_url, "description": listing.short_description, "address": listing.displayable_address, "image": listing.thumbnail_url, "floor_plans": listing.floor_plan if listing.floor_plan else [], "new_home": new_home}

def list_properties_rightmove(latitude, longitude, radius, min_bedrooms, min_bathrooms, min_price=0, max_price=0):

    (lat_min, lon_min, lat_max, lon_max) = boundingBox(latitude, longitude, radius)
    box = [(lat_min, lon_min), (lat_min, lon_max), (lat_max, lon_max), (lat_max, lon_min), (lat_min, lon_min)]

    new_home = True
    payload = {
    'apiApplication': 'ANDROID',
    'locationIdentifier': 'USERDEFINEDAREA^' + json.dumps({"polylines": polyline.encode(box)}),
    'minBedrooms': min_bedrooms
    }

    if max_price:
        payload['maxPrice'] = max_price
    if min_price:
        payload['minPrice'] = min_price

    if new_home:
        payload['newHome'] = "true"

    r = requests.get('http://api.rightmove.co.uk/api/sale/find', params=payload, proxies=proxies)
    for listing in r.json()["properties"]:
        yield {"id": str(listing["identifier"]), "latitude": listing['latitude'], "longitude": listing['longitude'], "price": int(listing['price']), "url": "http://www.rightmove.co.uk/property-for-sale/property-%d.html" % (listing['identifier']), "description": listing['summary'], "address": listing['address'], "image": listing['photoThumbnailUrl'], "floor_plans": [], "new_home": new_home}

class PropertiesHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @gen.engine
    def get(self):
        if 'X-Requested-With' not in self.request.headers or self.request.headers['X-Requested-With'] != "XMLHttpRequest":
            return
        latitude = float(self.get_argument('latitude', 0))
        longitude = float(self.get_argument('longitude', 0))
        radius = float(self.get_argument('radius', 0))
        min_price = self.get_argument('min_price', 0)
        max_price = self.get_argument('max_price', 0)
        min_price = int(min_price) if min_price and min_price.isdigit() else 0
        max_price = int(max_price) if max_price and max_price.isdigit() else 0
        min_bed = int(self.get_argument('min_bed', 2))
        min_bath = int(self.get_argument('min_bath', 2))

        source = self.get_argument('source', 'trovit')
        if source == 'zoopla':
            func = list_properties_zoopla
        elif source == 'nestoria':
            func = list_properties_nestoria
        elif source == 'rightmove':
            func = list_properties_rightmove
        elif source == 'smartnewhomes':
            func = list_properties_smartnewhomes
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
