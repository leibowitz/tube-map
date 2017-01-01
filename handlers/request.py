from tornado import gen
import tornado.web
import json
from py2neo import Graph

graph = Graph("http://neo4j:passwd@localhost:7474/db/data/")

class RequestHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @gen.engine
    def get(self):
        if 'X-Requested-With' not in self.request.headers or self.request.headers['X-Requested-With'] != "XMLHttpRequest":
            return
        latitude = self.get_argument('latitude', 0)
        longitude = self.get_argument('longitude', 0)
        max_time = int(self.get_argument('max_time', 2700))
        #max_time = 60 * 60

        results = []
        radius = 1.5
        max_total_time = max_time - 300
        zones = [2, 3, 4, 5, 6]
        where_zones = ' in x or '.join(str(x) for x in zones) + ' in x'
        for record in graph.run("""
                // find tube stations within {radius}km of {latitude},{longitude}
                with %s as lat, %s as lng
                CALL spatial.withinDistance('tube-stations',{longitude:lng,latitude:lat},%f) yield node as start
                WITH start, 2 * 6371 * asin(sqrt(haversin(radians(lat - start.latitude)) + cos(radians(lat)) * cos(radians(start.latitude)) * haversin(radians(lng - start.longitude)))) as distance // distance is between station and original lat/lng in km
                MATCH (end:Station)
                CALL apoc.algo.dijkstra(start, end, 'ROUTE>', 'time') YIELD path, weight
                WHERE length(path) > 0
                WITH path, start, end, distance, distance*600 + weight as totaltime, length(path) as stops, reduce(a=[], x IN [x in nodes(path) | x.line] | CASE WHEN x is not null and NOT x IN a THEN a + x ELSE a END) as lines // distance*600 because on average it takes about 10 min to walk 1km
                WHERE length(lines) < 3 // 1 line change maximum
                AND totaltime < %d // maximum {max_total_time} min
                AND filter(x IN end.zones WHERE %s) // in zone [{zones}]
                // To get only end stations and average total time, use this
                RETURN distinct end, avg(totaltime) as time, id(end) as nodeid
                ORDER BY time
                """ % (latitude, longitude, radius, max_total_time, where_zones)):
                max_walk_time = max_time - record['time']
                distance_walk_km = max_walk_time / 600 # in km
                distance_walk_miles = distance_walk_km / 1.6
                results.append({"name": record['end']['name'], "distance": distance_walk_miles, "latitude": record['end']['latitude'], "longitude": record['end']['longitude'], "time": record['time'], "id": record['nodeid']})

        self.write(json.dumps(results))
        self.finish()


