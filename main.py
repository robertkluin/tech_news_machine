import boot
boot.setup()

import webapp2

from handlers import FileServeHandler
from handlers import HackerNewsHandler
from handlers import KeywordsHandler
from handlers import SendMessageHandler
from handlers import ShowFeedHandler

config = {}

app = webapp2.WSGIApplication([
    ('/_load', HackerNewsHandler),
    ('/', ShowFeedHandler),
    ('/send', SendMessageHandler),
    ('/content/([^/]+)?', FileServeHandler),
    ('/keywords', KeywordsHandler),
], config=config)

