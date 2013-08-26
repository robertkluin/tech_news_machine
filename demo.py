"""Code snippets for use in talks.  It may not be pretty, but it should run."""

import boot
boot.setup()

import datetime, hashlib, logging, webapp2
import feedparser, readability

from google.appengine.api import blobstore
from google.appengine.api import taskqueue
from google.appengine.api import urlfetch
from google.appengine.ext import ndb

from furious.context import Context


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

  with Context() as context:
    for key, article, entry in zip(keys, articles, stream.entries):
      if article: continue

      logging.info("Found new article at %s", entry.link)

      new_articles.append(ArticleMeta(
          key=key,
          url=entry.link,
          hn_title=entry.title))

      context.add(fetch_article, args=[entry.link],
                  task_args={'name': key.id()})

  if new_articles:
    ndb.put_multi(new_articles)


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

  content_key = write_to_blobstore(article.content.encode('utf-8'))

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

