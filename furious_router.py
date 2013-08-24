import os
import sys

path = os.path.join(os.getcwd(), 'lib')
if path not in sys.path:
    sys.path.insert(0, path)


from appstats_logger.middleware import stats_logger_wsgi_middleware

from furious.handlers import webapp


app = stats_logger_wsgi_middleware(webapp.app)
