from bs4 import BeautifulSoup
from selenium import webdriver


class Spider(object):

    def __init__(self, chrome_web_hide: bool = True):
        self.chrome_web_hide = chrome_web_hide

    @staticmethod
    def chrome_web_driver(hide: bool):
        """ 获取Chrome浏览器驱动

        :param hide:隐藏浏览器
        :return:
        """
        if hide:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
            return webdriver.Chrome(chrome_options=chrome_options)

        else:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_experimental_option(
                "prefs", {"profile.managed_default_content_settings.images": 2}
                )
            return webdriver.Chrome(chrome_options=chrome_options)

    @staticmethod
    def soup(page_source: str):
        """ 网页源码转BeautifulSoup类

        :param page_source: 网页源码
        :return:
        """
        return BeautifulSoup(page_source, "lxml")