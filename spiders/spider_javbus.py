
import time
from .spider import Spider
from selenium.webdriver.common.by import By


class JavBusSpider(Spider):

    def __init__(self, chrome_hide, coll):
        """

        :param coll: Save Data MongoDb Collection
        """
        super().__init__(chrome_hide)

        self.domain = "https://www.javbus.com"
        self.coll = coll

    def next(self, soup):
        """ 是否有下一页

        :param soup:页面soup
        :return:
        """

        if not len(soup.select("a[id='next']")):
            return False
        else:
            return True

    def exists(self, code) -> bool:
        """ 查询数据库番号是否存在

        :param code:番号
        :return:
        """

        if self.coll.find_one({"code": code}):
            return True

        else:
            return None

    def capture_star_pages(self, star_browse_url: str) -> list:
        """ 捕获该演员所有作品URL

        :param code:番号
        :return:
        """

        pages = []

        driver = self.chrome_web_driver(self.chrome_hide)
        try:
            driver.get(star_browse_url)

        except:
            print(f"capture_star_pages url: {star_browse_url} fail")
            time.sleep(60 * 5)
            return pages

        goon = True
        while goon:
            driver.find_element(By.ID, "resultshowall").click()
            root_soup = self.soup(driver.page_source)
            items = root_soup.select("div[class='item masonry-brick'] a")
            for item in items:
                movie_url = item.attrs["href"].strip()
                pages.append({"movie_url": movie_url, "item": item})

            if self.next(root_soup):
                for _ in range(20):
                    driver.execute_script('window.scrollBy(0,1000)')
                    time.sleep(0.1)
                driver.find_element(By.ID, "next").click()

            else:
                goon = False

        driver.close()
        return pages

    def capture_movie_info(self, browse_page_url, movie_url, item):
        """ 捕获电影信息
        """

        single_cover_url = item.select(
            "img")[0].attrs["src"].strip(),  # 单封面URL
        if single_cover_url and single_cover_url[0] == "/":
            single_cover_url = self.domain + single_cover_url

        movie_info = {
            "browse_page_url": browse_page_url,  # 浏览页面URL
            "detail_page_url": item.attrs["href"].strip(),  # 详情页面URL
            "single_cover_url": single_cover_url,
            "full_cover_url": "",  # 全封面URL
            "title": item.select("img")[0].attrs["title"].strip(),  # 标题
            "code": item.select("date")[0].string.strip(),  # 番号
            "date": item.select("date")[1].string.strip(),  # 日期
            "tags": [],  # 标签列表
            "actors": [],  # 演员列表
            "magnets": [],  # 磁力连接
            "browse_imgs": []  # 浏览图片
        }

        if self.exists(movie_info["code"]):
            return

        print("\t\tcode:\t{}".format(movie_info["code"]))

        driver = self.chrome_web_driver(self.chrome_hide)
        try:
            driver.get(movie_url)

        except:
            driver.close()
            print("ERR_CONNECTION_CLOSED")
            time.sleep(60 * 5)
            return

        print("start > ", movie_info["code"])

        # 获取详情页soup
        detail_page_soup = self.soup(driver.page_source)
        if not detail_page_soup:
            print("get soup fail: ", browse_page_url, " > ",
                  movie_info["detail_page_url"], " > ", movie_info["code"])
            return

        # 获取全封面URL
        try:
            full_cover_url = detail_page_soup.select("div[class='container'] div[class='row movie']")[
                0].select("a[class='bigImage']")[0].attrs["href"]

            if full_cover_url and full_cover_url[0] == "/":
                full_cover_url = self.domain + full_cover_url

            movie_info["full_cover_url"] = full_cover_url

        except:
            print("\t\tget full_cover_url fail: ", movie_info["code"])

        # 获取标签列表
        try:
            for item in detail_page_soup.select("div[class='container'] div[class='row movie']")[0].select(
                    "span[class='genre']"):
                if item.string:
                    movie_info["tags"].append(item.string)
        except:
            print("\t\tget tags fail: ", movie_info["code"])

        # 获取演员列表
        for item in detail_page_soup.select("a[class='avatar-box']"):
            portrait_url = item.select("img")[0].attrs["src"].strip()
            if portrait_url and portrait_url[0] == "/":
                portrait_url = self.domain + portrait_url
            actor_info = {
                "page_url": item.attrs["href"].strip(),
                "portrait_url": portrait_url,
                "name": item.select("img")[0].attrs["title"].strip(),
            }
            movie_info["actors"].append(actor_info)

        # 获取磁力连接
        items = detail_page_soup.select(
            "table[id='magnet-table'] a[rel='nofollow']")
        items = [items[i:i + 3] for i in range(0, len(items), 3)]
        for item in items:
            magnet_info = {
                "link": item[0].attrs["href"].strip(),
                "size": item[1].string.strip(),
                "date": item[2].string.strip()
            }
            movie_info["magnets"].append(magnet_info)

        # 获取浏览图片
        for item in detail_page_soup.select("div[id='sample-waterfall'] a[class='sample-box']"):
            img = item.attrs["href"].strip()
            if img and img[0] == "/":
                img = self.domain + img
            movie_info["browse_imgs"].append(img)

        # 插入数据库
        self.coll.insert_one(movie_info)
        driver.close()

    def capture_star_movies(self, star_browse_url):
        """ 捕获这位明星下所有电影

        :param star_browse_url: 明星作品浏览地址
        :return:
        """
        pages = self.capture_star_pages(star_browse_url)
        for page in pages:
            print("\tstar_browse_url:\t{}".format(page["movie_url"]))
            self.capture_movie_info(
                star_browse_url, item=page["item"], movie_url=page["movie_url"])

    def update_star_movie(self):
        """ 更新演员电影
        """
        browse_page_url_group = self.coll.aggregate([
            {"$unwind": "$browse_page_url"}, {
                "$group": {"_id": "$browse_page_url"}}
        ])
        star_browse_urls = []
        for browse_page_url in list(browse_page_url_group):
            url = browse_page_url["_id"]
            splits = url.split("/", url.count("/"))
            browse_root_url = "{}/star/{}".format(
                self.domain, splits[splits.index("star")+1])
            if browse_root_url not in star_browse_urls:
                star_browse_urls.append(browse_root_url)

        items = star_browse_urls[::-1]

        for star_browse_url in items:
            print("update start:\t{}".format(star_browse_url))
            self.capture_star_movies(star_browse_url)
            print("update over:\t{}".format(star_browse_url))

        self.adjust_data()

    def update_magnet_link(self):
        """ 更新电影磁力链接
        """
        results = self.coll.find({})
        for result in results:
            detail_page_url = result["detail_page_url"]
            print("update start:\t{}".format(detail_page_url))
            driver = self.chrome_web_driver(self.chrome_hide)
            try:
                driver.get(detail_page_url)

            except:
                driver.close()
                return

            # 获取详情页soup
            detail_page_soup = self.soup(driver.page_source)
            if not detail_page_soup:
                return

            # 磁力链接
            items = detail_page_soup.select(
                "table[id='magnet-table'] a[rel='nofollow']")
            items = [items[i:i + 3] for i in range(0, len(items), 3)]
            magnets = []
            for item in items:
                magnet_info = {
                    "link": item[0].attrs["href"].strip(),
                    "size": item[1].string.strip(),
                    "date": item[2].string.strip()
                }
                magnets.append(magnet_info)

            self.coll.update_one({"_id": result["_id"]}, {
                                 "$set": {"magnets": magnets}})
