"""Simple in-memory article-to-user "matcher"."""

import json
import urllib2

#import gevent
from gevent.pywsgi import WSGIServer

from BeautifulSoup import BeautifulSoup


# INDEX contains two mappings. One maps tokens to users, the other maps users
# to tokens.
INDEX = {
    'users': {},
    'tokens': {}
}


def load_index(env):
    """Seed INDEX from the json encoded request body."""
    index = json.loads(env['wsgi.input'].read())
    INDEX.update(index)
    return INDEX


def dump_index(env):
    """Return the INDEX."""
    return INDEX


def update_subscriptions(env):
    """Update the user and token mappings."""
    raw_update = env['wsgi.input'].read()

    try:
        update = json.loads(raw_update)
        user_id = update['user_id']
    except:
        return "ERROR: Invalid input."

    if not user_id:
        return False

    current_subscriptions = set(INDEX['users'].get(user_id, ()))
    subscriptions = set(update.get('tokens', ()))

    INDEX['users'][user_id] = list(subscriptions)

    # Remove tokens they don't care about now.
    for token in current_subscriptions - subscriptions:
        token_list = INDEX['tokens'].get(token)
        if not token_list:
            continue

        try:
            token_list.remove(token)
        except ValueError:
            pass

    # Add tokens they now care about.
    for token in subscriptions - current_subscriptions:
        token_list = INDEX['tokens'].setdefault(token, [])
        if user_id not in token_list:
            token_list.append(user_id)

    return True


def tokenize_article(env):
    """Returns the list of users interested in an article."""
    article_url = env['wsgi.input'].read()

    if not article_url:
        return "no url"

    raw_article = urllib2.urlopen(article_url).read().decode('utf-8')

    if not raw_article:
        return "no article"

    html = BeautifulSoup(raw_article)

    if not html:
        return "no html"

    #text = html.get_text(strip=True)  # This needs a newer BeautifulSoup.
    text = html.getText(" ")

    if not text:
        return "no text"

    tokens = set(text.split())

    if not tokens:
        return "no tokens"

    users = set()
    for token in tokens:
        users.update(INDEX['tokens'].get(token, ()))

    return list(users)


HANDLERS = {
    '/_a/load': load_index,
    '/_a/dump': dump_index,
    '/subscription/update': update_subscriptions,
    '/process/article': tokenize_article
}


def wsgi_handler(environ, start_response):
    handler = HANDLERS.get(environ['PATH_INFO'])
    if not handler:
        status = '404 Not Found'
        headers = [
            ('Content-Type', 'application/json')
        ]

        start_response(status, headers)

        return '{"status": 404}\n'

    status = '200 OK'
    headers = [
        ('Content-Type', 'application/json')
    ]

    start_response(status, headers)

    return json.dumps(handler(environ)) + "\n"


WSGIServer(('', 8001), wsgi_handler).serve_forever()

