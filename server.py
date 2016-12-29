import os
from tornado.ioloop import IOLoop
from tornado.options import OptionParser
import tornado.web

import handlers

if __name__ == "__main__":
    h = [
        (r"/", handlers.HomeHandler),
        (r"/request", handlers.RequestHandler),
        (r"/properties", handlers.PropertiesHandler),
        (r"/tubes", handlers.TubesHandler),
        (r"/lines", handlers.LinesHandler),
        (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': os.path.join(os.path.dirname(__file__), 'static')}),
        (r'/css/(.*)', tornado.web.StaticFileHandler, {'path': os.path.join(os.path.dirname(__file__), 'css')}),
        (r'/fonts/(.*)', tornado.web.StaticFileHandler, {'path': os.path.join(os.path.dirname(__file__), 'fonts')}),
    ]

    options = OptionParser()
    options.define("port", default=8009, help="run on the given port", type=int)

    options.parse_command_line()

    settings = dict(
        handlers=h,
        static_path=os.path.join(os.path.dirname(__file__), 'static'),
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        debug=True,
    )

    application = tornado.web.Application(
        **settings)

    application.listen(options.port)
    
    IOLoop.instance().start()


