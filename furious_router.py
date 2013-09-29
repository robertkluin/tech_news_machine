"""Ensure the instance is fully configured (paths setup)."""

import boot
boot.setup()

from furious.handlers import webapp

import settings

app = webapp.app

if settings.ENABLE_RPC_PROFILE_LOGGING:
    global app

    from appstats_logger.middleware import stats_logger_wsgi_middleware

    app = stats_logger_wsgi_middleware(webapp.app)

