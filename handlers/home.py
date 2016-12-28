from tornado import gen
import tornado.web

class HomeHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @gen.engine
    def get(self):
        self.render("home.html")
