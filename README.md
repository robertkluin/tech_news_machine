Smart Tech News
===============


*NOTE*: The version of the code used for the talk lives in the [talk_code](https://github.com/robertkluin/tech_news_machine/tree/talk_code) branch.


Introduction
------------

Smart Tech News is an application that watches the Hacker News RSS feed, pulls
down new articles, parses them, looks for articles you might be interested in,
and sends you a notification with a link to a reduced form (readability) of the
article and a link to the original article.

It started as an example of building something fast using App Engine and
Compute Engine.  The matching engine runs on GCE, and the rest of the
application runs on App Engine.  It makes use of Cloud Storage for hosting the
reduced form content.

