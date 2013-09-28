"""Code snippets for use in talks.  It may not be pretty, but it should run."""

import boot
boot.setup()

import datetime, hashlib, json, logging, os, webapp2
import feedparser, readability

from google.appengine.api import blobstore
from google.appengine.api import channel
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
from google.appengine.ext.webapp import blobstore_handlers

from furious.context import Context


class HackerNewsHandler(webapp2.RequestHandler):
  def get(self):
    load_feed()


class ArticleMeta(ndb.Model):
  first_seen = ndb.DateTimeProperty(auto_now_add=True)
  last_fetch = ndb.DateTimeProperty()

  hn_title = ndb.StringProperty(indexed=False)
  url = ndb.StringProperty(indexed=False)

  @property
  def content_key(self):
    """Return GCS Key for content."""
    gcs_filename = "/newsarticles/" + self.key.id()
    return blobstore.create_gs_key("/gs" + gcs_filename)


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
                  task_args={'name': key.id(),
                             'countdown': 30})

  if new_articles:
    ndb.put_multi(new_articles)


def fetch_article(url):
  try:
    result = urlfetch.fetch(url)
  except:
    return

  raw_html = result.content.decode('utf-8')

  article = readability.Readability(raw_html, url)

  url_hash = hashlib.sha1(url).hexdigest()

  write_to_cloud_storage(article.content.encode('utf-8'), url_hash)

  article = ArticleMeta.get_by_id(url_hash)
  article.last_fetch = datetime.datetime.utcnow()
  article.put()

  article_url = "http://%s/article?article_id=%s" % (
      os.environ['HTTP_HOST'], url_hash)

  users = urlfetch.fetch("http://localhost:8001/process/article",
                         payload=article_url, method="POST").content

  interested_users = json.loads(users)
  for user_id in interested_users:
    send_message_to_user(user_id, url, url_hash, article.hn_title)


def send_message_to_user(user_id, url, article_id, article_title):
  message = {"id": article_id,
             "url": url,
             "title": article_title}

  channel.send_message(str(user_id), json.dumps(message))


def write_to_cloud_storage(content, url_hash):
  import cloudstorage as gcs

  gcs_filename = "/newsarticles/" + url_hash

  with gcs.open(gcs_filename, 'w') as gcs_file:
    gcs_file.write(content)

  return blobstore.create_gs_key("/gs" + gcs_filename)


def write_to_blobstore(content):
  from google.appengine.api import files

  file_name = files.blobstore.create(mime_type='text/html')

  with files.open(file_name, 'a') as blob:
   blob.write(content)

  files.finalize(file_name)

  return files.blobstore.get_blob_key(file_name)


class BlobHandler(blobstore_handlers.BlobstoreDownloadHandler):

  def get(self):
    article_id = self.request.get('article_id')
    if not article_id:
      logging.error("No article id")
      return

    article_meta = ArticleMeta.get_by_id(article_id)
    if not article_meta:
      logging.error("No article meta found")
      return

    self.send_blob(article_meta.content_key, content_type='text/html')


app = webapp2.WSGIApplication([
    ('/_check', HackerNewsHandler),
    ('/article', BlobHandler),
], config={})

