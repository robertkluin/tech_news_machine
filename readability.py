#coding=utf-8

# author: kingwkb
# blog : http://yanghao.org/blog/
#
# this is code demo: http://yanghao.org/tools/readability

import urlparse
import re
import math
import posixpath

#import chardet
from BeautifulSoup import BeautifulSoup
#from bs4 import BeautifulSoup

REGEXPS = {
    'unlikelyCandidates': re.compile("combx|comment|community|disqus|extra|"
                                     "foot|header|menu|remark|rss|shoutbox|"
                                     "sidebar|sponsor|ad-break|agegate|"
                                     "pagination|pager|popup|tweet|twitter",
                                     re.I),
    'okMaybeItsACandidate': re.compile("and|article|body|column|main|shadow",
                                       re.I),
    'positive': re.compile("article|body|content|entry|hentry|main|page|"
                           "pagination|post|text|blog|story", re.I),
    'negative': re.compile("combx|comment|com|contact|foot|footer|footnote|"
                           "masthead|media|meta|outbrain|promo|related|scroll|"
                           "shoutbox|sidebar|sponsor|shopping|tags|tool|widget",
                           re.I),
    'extraneous': re.compile("print|archive|comment|discuss|e[\-]?mail|share|"
                             "reply|all|login|sign|single", re.I),
    'divToPElements': re.compile("<(a|blockquote|dl|div|img|ol|p|pre|table|ul)",
                                 re.I),
    'replaceBrs': re.compile("(<br[^>]*>[ \n\r\t]*){2,}", re.I),
    'replaceFonts': re.compile("<(/?)font[^>]*>", re.I),
    'trim': re.compile("^\s+|\s+$", re.I),
    'normalize': re.compile("\s{2,}", re.I),
    'killBreaks': re.compile("(<br\s*/?>(\s|&nbsp;?)*)+", re.I),
    'videos': re.compile("http://(www\.)?(youtube|vimeo)\.com", re.I),
    'skipFootnoteLink': re.compile("^\s*(\[?[a-z0-9]{1,2}\]?|^|edit|"
                                   "citation needed)\s*$", re.I),
    'nextLink': re.compile("(next|weiter|continue|>([^\|]|$)|»([^\|]|$))",
                           re.I),
    'prevLink': re.compile("(prev|earl|old|new|<|«)", re.I)
}


def _remove_script(html):
    for elem in html.findAll("script"):
        elem.extract()


def _remove_style(html):
    for elem in html.findAll("style"):
        elem.extract()


def _remove_link(html):
    for elem in html.findAll("link"):
        elem.extract()


def _extract_title(html):
    title = ''
    try:
        title = html.find('title').text
    except:
        pass

    return title


def _get_class_weight(node):
    weight = 0
    if 'class' in node:
        if REGEXPS['negative'].search(node['class']):
            weight -= 25
        if REGEXPS['positive'].search(node['class']):
            weight += 25

    if 'id' in node:
        if REGEXPS['negative'].search(node['id']):
            weight -= 25
        if REGEXPS['positive'].search(node['id']):
            weight += 25

    return weight


def get_link_density(self, node):
    links = node.findAll('a')
    text_length = len(node.text)

    if text_length == 0:
        return 0

    link_length = 0
    for link in links:
        link_length += len(link.text)

    return link_length / text_length


class Readability(object):

    def __init__(self, input, url):
        """
        url = "http://yanghao.org/blog/"
        htmlcode = urllib2.urlopen(url).read().decode('utf-8')

        readability = Readability(htmlcode, url)

        print readability.title
        print readability.content
        """
        self.candidates = {}

        self.url = url
        self.input = input
        self.input = REGEXPS['replaceBrs'].sub("</p><p>", self.input)
        self.input = REGEXPS['replaceFonts'].sub("<\g<1>span>",
                                                 self.input)

        self.html = BeautifulSoup(self.input)

#        print self.html.originalEncoding
#        print self.html
        _remove_script(self.html)
        _remove_style(self.html)
        _remove_link(self.html)

        self.title = _extract_title(self.html)

        self.content = self.grabArticle()

    def grabArticle(self):

        for elem in self.html.findAll(True):

            unlikelyMatchString = elem.get('id', '') + elem.get('class', '')

            if REGEXPS['unlikelyCandidates'].search(unlikelyMatchString) and \
                not REGEXPS['okMaybeItsACandidate'].search(unlikelyMatchString) and \
                elem.name != 'body':
#                print elem
#                print '--------------------'
                elem.extract()
                continue
#                pass

            if elem.name == 'div':
                s = elem.renderContents(encoding=None)
                if not REGEXPS['divToPElements'].search(s):
                    elem.name = 'p'

        for node in self.html.findAll('p'):

            parentNode = node.parent
            grandParentNode = parentNode.parent
            innerText = node.text

#            print '=================='
#            print node
#            print '------------------'
#            print parentNode

            if not parentNode or len(innerText) < 20:
                continue

            parentHash = hash(str(parentNode))
            grandParentHash = hash(str(grandParentNode))

            if parentHash not in self.candidates:
                self.candidates[parentHash] = self.initializeNode(parentNode)

            if grandParentNode and grandParentHash not in self.candidates:
                self.candidates[grandParentHash] = self.initializeNode(grandParentNode)

            contentScore = 1
            contentScore += innerText.count(',')
            contentScore += innerText.count(u'，')
            contentScore +=  min(math.floor(len(innerText) / 100), 3)

            self.candidates[parentHash]['score'] += contentScore

#            print '======================='
#            print self.candidates[parentHash]['score']
#            print self.candidates[parentHash]['node']
#            print '-----------------------'
#            print node

            if grandParentNode:
                self.candidates[grandParentHash]['score'] += contentScore / 2

        topCandidate = None

        for key in self.candidates:
#            print '======================='
#            print self.candidates[key]['score']
#            print self.candidates[key]['node']

            self.candidates[key]['score'] = self.candidates[key]['score'] * \
                                            (1 - get_link_density(self.candidates[key]['node']))

            if not topCandidate or self.candidates[key]['score'] > topCandidate['score']:
                topCandidate = self.candidates[key]

        content = ''

        if topCandidate:
            content = topCandidate['node']
#            print content
            content = self.cleanArticle(content)
        return content


    def cleanArticle(self, content):

        self.cleanStyle(content)
        self.clean(content, 'h1')
        self.clean(content, 'object')
        self.cleanConditionally(content, "form")

        if len(content.findAll('h2')) == 1:
            self.clean(content, 'h2')

        self.clean(content, 'iframe')

        self.cleanConditionally(content, "table")
        self.cleanConditionally(content, "ul")
        self.cleanConditionally(content, "div")

        self.fixImagesPath(content)

        content = content.renderContents(encoding=None)

        content = REGEXPS['killBreaks'].sub("<br />", content)

        return content

    def clean(self,e ,tag):

        targetList = e.findAll(tag)
        isEmbed = 0
        if tag =='object' or tag == 'embed':
            isEmbed = 1

        for target in targetList:
            attributeValues = ""
            for attribute in target.attrs:
                attributeValues += target[attribute[0]]

            if isEmbed and REGEXPS['videos'].search(attributeValues):
                continue

            if isEmbed and REGEXPS['videos'].search(target.renderContents(encoding=None)):
                continue
            target.extract()

    def cleanStyle(self, e):

        for elem in e.findAll(True):
            del elem['class']
            del elem['id']
            del elem['style']

    def cleanConditionally(self, e, tag):
        tagsList = e.findAll(tag)

        for node in tagsList:
            weight = _get_class_weight(node)
            hashNode = hash(str(node))
            if hashNode in self.candidates:
                contentScore = self.candidates[hashNode]['score']
            else:
                contentScore = 0

            if weight + contentScore < 0:
                node.extract()
            else:
                p = len(node.findAll("p"))
                img = len(node.findAll("img"))
                li = len(node.findAll("li"))-100
                input = len(node.findAll("input"))
                embedCount = 0
                embeds = node.findAll("embed")
                for embed in embeds:
                    if not REGEXPS['videos'].search(embed['src']):
                        embedCount += 1
                linkDensity = get_link_density(node)
                contentLength = len(node.text)
                toRemove = False

                if img > p:
                    toRemove = True
                elif li > p and tag != "ul" and tag != "ol":
                    toRemove = True
                elif input > math.floor(p/3):
                    toRemove = True
                elif contentLength < 25 and (img==0 or img>2):
                    toRemove = True
                elif weight < 25 and linkDensity > 0.2:
                    toRemove = True
                elif weight >= 25 and linkDensity > 0.5:
                    toRemove = True
                elif (embedCount == 1 and contentLength < 35) or embedCount > 1:
                    toRemove = True

                if toRemove:
                    node.extract()

    def initializeNode(self, node):
        contentScore = 0

        if node.name == 'div':
            contentScore += 5;
        elif node.name == 'blockquote':
            contentScore += 3;
        elif node.name == 'form':
            contentScore -= 3;
        elif node.name == 'th':
            contentScore -= 5;

        contentScore += _get_class_weight(node)

        return {'score':contentScore, 'node': node}

    def fixImagesPath(self, node):
        imgs = node.findAll('img')
        for img in imgs:
            src = img.get('src',None)
            if not src:
                img.extract()
                continue

            if 'http://' != src[:7] and 'https://' != src[:8]:
                newSrc = urlparse.urljoin(self.url, src)

                newSrcArr = urlparse.urlparse(newSrc)
                newPath = posixpath.normpath(newSrcArr[2])
                newSrc = urlparse.urlunparse((newSrcArr.scheme, newSrcArr.netloc, newPath,
                                              newSrcArr.params, newSrcArr.query, newSrcArr.fragment))
                img['src'] = newSrc

