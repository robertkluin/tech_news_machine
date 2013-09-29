"""Code snippets for use in talks.  It may not be pretty, but it should run."""

import boot
boot.setup()

import logging, webapp2

from google.appengine.ext.webapp import blobstore_handlers



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
    ('/article', BlobHandler),
], config={})

