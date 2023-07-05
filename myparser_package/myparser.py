from bs4 import BeautifulSoup
import requests


class MyParser:
    def __init__(self, url):
        self.url = self.url_corrector(url)
        response = requests.get(self.url)
        self.soup = BeautifulSoup(response.text, 'lxml')
        self.is_that_tv_series = self.is_this_tv_show()

    def url_corrector(self, url):
        if 'http' not in url:
            url = 'https://' + url
        elif 'www' not in url:
            url = 'www.' + url
        return url

    def get_main_title(self):
        main_title = self.soup.find('section', id='topSection').find('h1', class_='title')
        return main_title.text.strip()[:70]

    def is_this_tv_show(self):
        """ Return True > series. False > Movie """
        scnd_domain = 'rottentomatoes.com'
        cutted_url = self.url[self.url.index(scnd_domain) + len(scnd_domain):]
        if cutted_url.startswith('/m/'):
            return False
        return True

    def get_series_info(self):
        if not self.is_that_tv_series:
            series_info = self.soup.find('section', id='movie-info').find('p')
            return series_info.text.strip()
        series_info = self.soup.find('section', id='series-info').find('p')
        return series_info.text.strip()

    def get_preview_img(self):
        result = 'imgs/placeholder.jpg'
        if not self.is_that_tv_series:
            preview = self.soup.find('tile-dynamic', class_='thumbnail')
            if preview:
                result = preview.find('img').get('src')
        elif self.is_that_tv_series:
            preview = self.soup.find('tile-dynamic', class_='thumbnail')
            if preview:
                result = preview.find('img').get('src')
        return result

