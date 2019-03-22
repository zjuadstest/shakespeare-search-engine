import urllib.request
from bs4 import BeautifulSoup
import ssl

class Crawler:

    def __init__(self, base_uri):
        self.base_uri = base_uri.strip('/')

    # path: relative path of the uri
    def crawl_html(self, path):
        # Ignore SSL certificate errors
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        html = urllib.request.urlopen('http://{0}/{1}'.format(self.base_uri, path.strip('/')), context=ctx).read()
        return html

    # get all links in the html page
    def get_links(self, html):
        if type(html) is bytes:

            soup = BeautifulSoup(html, 'html.parser')

            # Retrieve all of the anchor tags
            links = []
            tags = soup('a')
            for tag in tags:
                links.append(tag.get('href', None))

            return links

        if type(html) is str:
            return self.get_links(self.crawl_html(html))

        return 'Error Relative Links & Bytes Supported Only'

    # filter out the links directing to outside websites
    # only get the relative ones
    def get_relative_links(self, html):
        if type(html) is bytes:

            soup = BeautifulSoup(html, 'html.parser')

            # Retrieve all of the anchor tags
            links = []
            tags = soup('a')
            if not tags:
                return None
            for tag in tags:
                href = tag.get('href', None)

                if href and 'http' not in href:
                    links.append(href)

            return links

        if type(html) is str:
            return self.get_relative_links(self.crawl_html(html))

        return 'Error Relative Links & Bytes Supported Only'


# # block test
# recursive crawl
def test_crawl():
    crawler = Crawler('shakespeare.mit.edu')
    links = crawler.get_relative_links('Poetry/LoversComplaint.html')
    print(links)
    # end of recursive get links
    links = crawler.get_relative_links('allswell/index.html')
    print(links)


