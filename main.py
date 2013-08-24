import os
import sys

import webapp2

path = os.path.join(os.getcwd(), 'lib')
if path not in sys.path:
    sys.path.insert(0, path)


class TestHandler(webapp2.RequestHandler):

    def get(self):
        import feedparser

        d = feedparser.parse("https://news.ycombinator.com/rss")
        print d.feed.title
        print d.feed.link
        print d.feed.description

        print "Title " + d.entries[0].title
        print "Link " + d.entries[0].link
        print "Description " + d.entries[0].description
        print "Comments " + d.entries[0].comments
        self.response.out.write("test")


config = {}

app = webapp2.WSGIApplication([
    ('/', TestHandler)
], config=config)
