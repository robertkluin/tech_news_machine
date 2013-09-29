import boot
boot.setup()

import webapp2

from handlers import HackerNewsHandler
from handlers import KeywordsHandler
from handlers import SendMessageHandler
from handlers import ShowFeedHandler
from article import DistilledArticleServer

config = {}

app = webapp2.WSGIApplication([
    ('/article/([^/]+)?', DistilledArticleServer),
    ('/_load', HackerNewsHandler),
    ('/', ShowFeedHandler),
    ('/send', SendMessageHandler),
    ('/keywords', KeywordsHandler),
], config=config)

