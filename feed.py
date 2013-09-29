import logging

import feedparser

import settings

from article import process_new_articles


def process_feed(feed_url=settings.HN_RSS_FEED):
    """Fetch an RSS feed, then insert article processors for new articles."""
    entries = _get_feed_entries(feed_url)

    if not entries:
        return

    process_new_articles(entries)


def _get_feed_entries(feed_url):
    """Fetch the RSS feed at feed_url and return the entries from it."""
    stream = feedparser.parse(feed_url)

    if not stream:
        logging.error('Error fetching stream: No Stream.')
        return

    if stream.feed:
        logging.info('Fetched feed: %s', stream.feed.title)

    if not stream.entries:
        logging.warning('No entries in stream: %s.', stream)
        return

    return stream.entries

