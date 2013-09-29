import datetime
import hashlib
import json
import logging
import os

from google.appengine.api import blobstore
from google.appengine.api import channel
from google.appengine.api import urlfetch
from google.appengine.ext import ndb

from furious.async import Async
from furious.context import Context

import readability

import settings


class ArticleMeta(ndb.Model):
    """Tracks some basic metadata about articles, and serves as an index of
    known articles.
    """
    first_seen = ndb.DateTimeProperty(auto_now_add=True)
    last_fetch = ndb.DateTimeProperty()

    hn_title = ndb.StringProperty(indexed=False)
    url = ndb.StringProperty(indexed=False)

    @property
    def content_key(self):
        """Return GCS Key for content."""
        gcs_filename = "/newsarticles/" + self.key.id()
        return blobstore.create_gs_key("/gs" + gcs_filename)


def process_new_articles(entries):
    """Compile a list of keys from entries, then check for existing entries
    that have not already been fetched.
    """
    # Build a list of keys from the article URL.
    keys = [ndb.Key(ArticleMeta, hashlib.sha1(entry.link).hexdigest())
            for entry in entries]

    # Fetch existing article meta entities.
    articles = ndb.get_multi(keys)

    new_articles = []

    with Context() as context:
        for key, article, entry in zip(keys, articles, entries):
            # Do not insert processors for any article that has already been
            # fetched.
            if article and article.last_fetch:
                logging.debug("Skipping fetched article at %s", entry.link)
                continue

            logging.info("Found new article at %s", entry.link)

            new_articles.append(ArticleMeta(
                key=key,
                url=entry.link,
                hn_title=entry.title))

            # Create a processor task for the new article.
            context.add(process_article, args=[entry.link],
                        task_args={'name': "process-article-" + key.id()})

        # Before exiting the context, write the new article meta entities.
        if new_articles:
            ndb.put_multi(new_articles)


def process_article(url):
    try:
        result = urlfetch.fetch(url)
    except:
        logging.error("Failed to fetch URL %s.", url)
        # TODO: Should probably return an error here so that task will retry.
        return

    # Do a simple test to avoid dealing with non-html.
    # TODO: This could probably be made more robust.
    if 'html' not in result.headers.get('content-type', ''):
        logging.info("Not processing %s at URL %s.",
                     result.headers.get('content-type', ''),
                     url)
        return

    article = _get_article_content(result.content, url)
    url_hash = hashlib.sha1(url).hexdigest()

    # Save the distilled content to Cloud Storage for later processing and
    # serving.
    _write_to_cloud_storage(article.content.encode('utf-8'), url_hash)

    # TODO: There's got a be a cleaner way to lay this code out.
    hn_title = _update_last_fetch_time(url_hash)

    # Run the matcher and notifier in different tasks.
    Async(_match_and_notify_users, args=[url, url_hash, hn_title]).start()


def _match_and_notify_users(url, url_hash, hn_title):
    """Run the article through the matching engine and notify insterested users
    of the new article.
    """
    # Build up the Cloud Storage URL for the distilled content.
    distilled_url = "http://%s/article?article_id=%s" % (
        os.environ['HTTP_HOST'], url_hash)

    # TODO: Probably need to adjust this to work in some other way.... For
    # example, perhaps the matcher side should handle chunking up the list of
    # users.

    # Ping the matcher to run against the distilled version of the article.
    users = urlfetch.fetch(settings.MATCHER_BASE_URL + "/process/article",
                           payload=distilled_url, method="POST").content

    # TODO: Probably need to implement some form of batching here.
    # Get the list of interested users the matcher returned.
    interested_users = json.loads(users)

    # Create a task for each notification, using the user id + URL hash as the
    # name.
    with Context() as context:
        for user_id in interested_users:
            context.add(
                _send_message_to_user, args=[url, url_hash, hn_title],
                task_args={'name': "notify-user-%s-%s" % (url_hash, user_id)})


def _get_article_content(content, url):
    # Get the raw HTML, as a utf8 string.
    raw_html = content.decode('utf-8')

    # Use Readability to tease out the core article.
    # TODO: Fix the stupid unicode artifacts that get left all over the place.
    return readability.Readability(raw_html, url)


def _update_last_fetch_time(url_hash):
    # Update the last_fetch time for the article, this way it will not be
    # processed again.
    article = ArticleMeta.get_by_id(url_hash)
    article.last_fetch = datetime.datetime.utcnow()
    article.put()

    return article.hn_title


def _write_to_cloud_storage(content, url_hash):
    """Write the given content to the CS bucket."""
    import cloudstorage as gcs

    gcs_filename = settings.CS_BUCKET + url_hash

    # TODO: Probably need to handle failures in some way.  Especially cases
    # where the article content might have already been written.
    with gcs.open(gcs_filename, 'w') as gcs_file:
        gcs_file.write(content)


def _send_message_to_user(
        user_id, distilled_url, url, article_id, article_title):
    """Send a notification message to the user interested in the article."""
    message = {"id": article_id,
               "distilled_url": distilled_url,
               "url": url,
               "title": article_title}

    channel.send_message(str(user_id), json.dumps(message))
