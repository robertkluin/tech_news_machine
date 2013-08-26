"""Code snippets for use in talks.  It may not be pretty, but it should run."""

import boot
boot.setup()

import datetime, feedparser, hashlib, logging, readability, webapp2

from google.appengine.api import blobstore
from google.appengine.api import taskqueue
from google.appengine.api import urlfetch
from google.appengine.ext import ndb


class HackerNewsHandler(webapp2.RequestHandler):
    def get(self):
        load_feed()


class ArticleMeta(ndb.Model):
    first_seen = ndb.DateTimeProperty(auto_now_add=True)
    last_fetch = ndb.DateTimeProperty()

    hn_title = ndb.StringProperty(indexed=False)
    url = ndb.StringProperty(indexed=False)
    content = ndb.BlobKeyProperty(indexed=False)


def load_feed():
    stream = feedparser.parse("http://news.ycombinator.com/rss")

    keys = [ndb.Key(ArticleMeta, hashlib.sha1(entry.link).hexdigest())
            for entry in stream.entries]

    articles = ndb.get_multi(keys)

    new_articles = []
    fetch_tasks = []

    for key, article, entry in zip(keys, articles, stream.entries):
        if article: continue

        logging.info("Found new article at %s", entry.link)

        new_articles.append(ArticleMeta(
            key=key,
            url=entry.link,
            hn_title=entry.title))

        fetch_tasks.append(taskqueue.Task(
            url='/_fetch_article',
            name=key.id(),
            params={'url': entry.link}))

    if new_articles:
        ndb.put_multi(new_articles)
        taskqueue.Queue('default').add(fetch_tasks)


class FetchArticleHandler(webapp2.RequestHandler):
    def post(self):
        url = self.request.get('url')
        if not url:
            return

        fetch_article(url)


def fetch_article(url):
    try:
        result = urlfetch.fetch(url)
    except:
        return

    raw_html = result.content.decode('utf-8')

    article = readability.Readability(raw_html, url)

    url_hash = hashlib.sha1(url).hexdigest()

    content_key = write_to_blobstore(article.content)

    article = ArticleMeta.get_by_id(url_hash)
    article.content = content_key
    article.last_fetch = datetime.datetime.utcnow()
    article.put()


def write_to_gcs(content, url_hash):
    import cloudstorage as gcs

    gcs_filename = "BUCKET/" + url_hash

    with gcs.open(gcs_filename, 'w') as gcs_file:
        gcs_file.write(content)

    return blobstore.create_gs_key("/gs" + gcs_filename)


def write_to_blobstore(content):
    from google.appengine.api import files

    file_name = files.blobstore.create(mime_type='application/octet-stream')

    with files.open(file_name, 'a') as blob:
        blob.write(content)

    files.finalize(file_name)

    return files.blobstore.get_blob_key(file_name)


app = webapp2.WSGIApplication([
    ('/_check', HackerNewsHandler),
    ('/_fetch_article', FetchArticleHandler)
], config={})

