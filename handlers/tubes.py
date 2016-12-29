from tornado import gen
import tornado.web
import json
from py2neo import Graph

graph = Graph("http://neo4j:passwd@localhost:7474/db/data/")

class TubesHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @gen.engine
    def get(self):
        if 'X-Requested-With' not in self.request.headers or self.request.headers['X-Requested-With'] != "XMLHttpRequest":
            return
        results = []
        for record in graph.run("""
                // get all tube stations
                MATCH (n:Station)
                RETURN n
                """):
                results.append({"name": record['n']['name'], "latitude": record['n']['latitude'], "longitude": record['n']['longitude']})

        self.write(json.dumps(results))
        self.finish()


