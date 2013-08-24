import urllib2

import feedparser

import readability

from furious import context


def strip_article(url):
    htmlcode = urllib2.urlopen(url).read().decode('utf-8')

    article = readability.Readability(htmlcode, url)

    #data = urllib2.urlopen(url).read()
    print article.content


def load_feed():
    stream = feedparser.parse("http://news.ycombinator.com/rss")

    if not stream:
        print "Missing stream?"
        return

    if not stream.feed:
        print "Missing feed?"
        print stream
        return

    print stream.feed.title

    with context.new() as ctx:
        for entry in stream.entries:
            ctx.add(target=strip_article, args=[entry.link])

