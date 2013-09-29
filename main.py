import boot
boot.setup()

import webapp2

from handlers import KeywordsHandler
from handlers import SendMessageHandler
from handlers import ShowFeedHandler

from feed import ProcessHackerNewsHandler
from article import DistilledArticleServer


config = {}

app = webapp2.WSGIApplication([
    ('/article/([^/]+)?', DistilledArticleServer),
    ('/_check', ProcessHackerNewsHandler),
    ('/', ShowFeedHandler),
    ('/send', SendMessageHandler),
    ('/keywords', KeywordsHandler),
], config=config)

