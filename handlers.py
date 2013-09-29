import json
import urllib

import webapp2

from webapp2_extras import jinja2

from google.appengine.api import channel
from google.appengine.api import urlfetch
from google.appengine.api import users

import settings


class BaseHandler(webapp2.RequestHandler):

    @webapp2.cached_property
    def jinja2(self):
        # Returns a Jinja2 renderer cached in the app registry.
        return jinja2.get_jinja2(app=self.app)

    def render_response(self, _template, **context):
        # Renders a template and writes the result to the response.
        rv = self.jinja2.render_template(_template, **context)
        self.response.write(rv)


class AuthBaseHandler(BaseHandler):

    def get(self):
        self.user = users.get_current_user()
        if not self.user:
            self.redirect(users.create_login_url(self.request.uri))
            return


class ShowFeedHandler(AuthBaseHandler):

    def get(self):
        super(ShowFeedHandler, self).get()

        # Hacky but works for now.
        from demo import ArticleMeta

        articles = ArticleMeta.query().order(ArticleMeta.last_fetch).fetch(100)

        token = channel.create_channel(self.user.user_id())
        context = {
            'token': token,
            'user': self.user.user_id(),
            'articles': articles
        }

        self.render_response('articles.html', **context)


class SendMessageHandler(AuthBaseHandler):

    def get(self):
        super(SendMessageHandler, self).get()

        channel.send_message(self.user.user_id(), "test")


class KeywordsHandler(AuthBaseHandler):
    def post(self):
        """Update a users list of interested keywords."""
        super(KeywordsHandler, self).get()
        tokens = list(set(
            [token.strip() for token in self.request.body.lower().split(',')]))

        payload = {
            "user_id": self.user.user_id(),
            "tokens": tokens
        }
        urlfetch.fetch(settings.MATCHER_BASE_URL + "/subscription/update",
                       payload=json.dumps(payload), method="POST")

