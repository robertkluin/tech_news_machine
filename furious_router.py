import boot
boot.setup()

#from appstats_logger.middleware import stats_logger_wsgi_middleware

from furious.handlers import webapp


app = webapp.app
#app = stats_logger_wsgi_middleware(webapp.app)
