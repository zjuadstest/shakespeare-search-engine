from bs4 import BeautifulSoup
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
import nltk
import ssl
import string
import time
import json

import crawler
from index import Index
from term import Term
from bdict import BDict


try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

nltk.download('punkt')
nltk.download('stopwords')


class ShakeCrawler(crawler.Crawler):
    base_uri = 'shakespeare.mit.edu'

    def __init__(self):
        super(ShakeCrawler, self).__init__(self.base_uri)
        self.index = Index(300)
        self.bdict = BDict()

    # get all the links in the page previously crawled
    # 2 levels crawling

    # index the shakespeare page by levels
    def crawl_all(self):
        # get relative links of the level 0 index
        full = []
        relative_links0 = self.get_relative_links('')

        # level 0: crawl all the links on the index page
        if not self.bdict.is_page_crawled('index.html'):
            self.analyze_page('index.html', self.bdict.insert_new_link('index.html'))

        for link0 in relative_links0:
            # crawl all the pages
            if not self.bdict.is_page_crawled(link0):
                self.analyze_page(link0, self.bdict.insert_new_link(link0))

            # level 1

            short_links1 = self.get_relative_links(link0)
            if short_links1:
                sub_dir1 = link0[0:(link0.find('/') + 1)]
                print(sub_dir1)
                relative_links1 = [sub_dir1 + short_link for short_link in short_links1 if (-1 == short_link.find('/') and short_link != 'full.html')]
                if 'full.html' in short_links1 and sub_dir1 not in full:
                    full.append(sub_dir1)
                print(relative_links1)
                for link1 in relative_links1:
                    # crawl all pages
                    if not self.bdict.is_page_crawled(link1):
                        self.analyze_page(link1, self.bdict.insert_new_link(link1))

        # write data to disk
        with open('data/full', 'w') as out:
            json.dump(obj={'full': full}, fp=out)
            out.close()

        self.index.disk_write()
        self.bdict.disk_write()

    # analyze by term
    def analyze_page(self, relative_link, link_index):
        # from html recognize paragraphs
        html = self.crawl_html(relative_link)
        soup = BeautifulSoup(html, 'html.parser')
        page = ''
        title = soup.find('title')
        if title:
            page = page + title.getText()
        p = soup.find('p')
        if p:
            page = page + p.getText()

       # print(page)

        word_tokens = word_tokenize(page)
        # print(word_tokens)

        stop_words = set(stopwords.words('english'))

        punctuation_filtered = [word for word in word_tokens if word[0] not in string.punctuation]

        ps = PorterStemmer()

        # filter stop_words & word stemming
        filtered_words = [ps.stem(word).strip('.') for word in punctuation_filtered if word not in stop_words]

        # print(filtered_words)
        # for comparison
        # print([word for word in stop_words_filtered if word not in stop_words])

        # insert the term
        # a. if word is not indexed, index the word, the word occurrence
        # b. if indexed, word occurrence
        count = 0
        for word in filtered_words:
            term = Term(word)
            search_info = self.index.search(term)
            if search_info:
                node, ith_key = search_info
            else:
                node, ith_key = self.index.insert(term)

            # update the term node info
            # print('ith_key', ith_key)

            node.keys[ith_key].insert(link_index, count)
            # print('link_index', link_index)
            count += 1

# block tests
def test_crawl_html():
    sc = ShakeCrawler()
    print(sc.crawl_html('allswell/allswell.4.1.html'))


def test_crawl_relative_links():
    sc = ShakeCrawler()
    # get the links on the first page
    print(sc.get_relative_links(''))

    # when no link on the page
    print(sc.get_relative_links('allswell/allswell.4.1.html'))

def test_analyze_page():
    sc = ShakeCrawler()
    if not sc.bdict.is_page_crawled(1):
        sc.analyze_page('news.html', sc.bdict.insert_new_link('news.html'))

# test_crawl_relative_links()


# test_analyze_page()

# sc = ShakeCrawler()
# sc.crawl_all()


def crawl(times):
    try:
        if not times:
            return
        sc = ShakeCrawler()
        sc.crawl_all()
    except:
        time.sleep(1)
        crawl(times - 1)


crawl(10)
