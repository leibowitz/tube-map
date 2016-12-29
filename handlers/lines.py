from tornado import gen
import tornado.web
import json
from collections import defaultdict
from py2neo import Graph

graph = Graph("http://neo4j:passwd@localhost:7474/db/data/")

class LinesHandler(tornado.web.RequestHandler):
    lines_colors = {'Central': '#FF0000', 'Bakerloo': '#b26300', 'Piccadilly': '#0019a8', 'Circle': '#ffd329', 'District': '#007d32', 'Overground': '#ef7b10', 'Hammersmith & City': '#f4a9be', 'Jubilee': '#a1a5a7', 'Metropolitan': '#9b0058', 'Northern': '#000000', 'Central': '#dc241f', 'Victoria': '#0098d8', 'Waterloo & City': '#93ceba', 'DLR': '#00AFAD', 'Emirates Air Line': '#dc241f'}
    @tornado.web.asynchronous
    @gen.engine
    def get(self):
        if 'X-Requested-With' not in self.request.headers or self.request.headers['X-Requested-With'] != "XMLHttpRequest":
            return
        lines = defaultdict(defaultdict)
        for record in graph.run("""
                // get all tube lines
                match p=(c:Station)-[r1:ROUTE]-(a:Stop)-[r2:ROUTE]->(b:Stop)-[r3:ROUTE]-(d:Station)
                return distinct a.line as line, a.direction as direction, c as from, d as to
                """):
            record = dict(record)
            if record['line'] not in lines:
                line_color = self.lines_colors[record['line']] if record['line'] in self.lines_colors else '#000000'
                lines[ record['line'] ] = {'directions': defaultdict(list), 'color': line_color}

            #if record['direction'] not in lines[ record['line'] ]['directions']:
            #    lines[ record['line'] ]['directions'][ record['direction'] ] = list()

            lines[ record['line'] ]['directions'][ record['direction'] ].append({
                "from": {"name": record['from']['name'], "lat": record['from']['latitude'], "lng": record['from']['longitude']},
                "to": {"name": record['to']['name'], "lat": record['to']['latitude'], "lng": record['to']['longitude']}
            })

        self.write(json.dumps(lines))
        self.finish()


