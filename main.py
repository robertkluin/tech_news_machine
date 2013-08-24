import boot
boot.setup()

import webapp2

from handlers import HackerNewsHandler

config = {}

app = webapp2.WSGIApplication([
    ('/', HackerNewsHandler)
], config=config)
