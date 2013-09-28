Smart Tech News
===============

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


Installation
------------

You will need to add the following to the `static` directory:

   * [Bootstrap](http://getbootstrap.com/)
   * [Underscore](http://underscorejs.org/) (minified version)
   * [Backbone](http://backbonejs.org/) (minified version)

The JavaScript files (Underscore and Backbone) go into the `js` directory that
was created when you copied the Bootstrap contents into `static`.

Usage
-----

To develop the application, you will need two terminal windows.  One to run the
App Engine portion, and one to run the Compute Engine portion.

To fire up the main App Engine application, enter the application root and run:

    dev_appserver.py .

To start up the matching engine, switch to the second terminal and run:

    python matcher.py

You should now be able to goto the [Article List](http://localhost:8080) and
create your subscription keywords.  (You should see stuff happen in both
terminals.)

You can then goto the [cron](http://localhost:8000/cron) page and tell the cron
job to run.  You should see output in the App Engine logs indicating that
the feed was fetched and articles were examined.  After a few seconds, if there
are any articles matching your keywords, the list should begin updating.  To
start, I suggest using some common words such as "the" and "a".

