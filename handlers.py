import webapp2

#from furious.async import Async
from furious import async

from parser import load_feed


class HackerNewsHandler(webapp2.RequestHandler):

    def get(self):
        task = async.Async(target=load_feed)
        task.start()

        self.response.out.write("Inserted parsing task")

