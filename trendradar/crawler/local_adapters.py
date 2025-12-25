# coding=utf-8
import requests
import json
import time
import re
from bs4 import BeautifulSoup


class LocalAdapters:
    """本地官网爬虫适配器集合"""

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self.base_url = "https://www.szvc.com.cn"

    def _to_newsnow_format(self, items):
        """统一封装成 NewsNow 的 API 返回格式"""
        return json.dumps({
            "status": "success",
            "items": items
        }, ensure_ascii=False)

    def get_szvc(self, max_pages=3):
        """
        深创投官网公告适配器 - 支持多页抓取
        :param max_pages: 默认抓取前3页，防止历史数据过多导致推送爆炸
        """
        all_items = []

        try:
            # 1. 先抓取第一页，获取总页数
            first_page_url = f"{self.base_url}/notice"
            res = requests.get(first_page_url, headers=self.headers, timeout=15)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')

            # 获取总页数 (解析 "1 / 7")
            pagination_text = soup.select_one('.app-pagination .m span')
            total_pages = 1
            if pagination_text:
                match = re.search(r'/ (\d+)', pagination_text.get_text())
                if match:
                    total_pages = int(match.group(1))

            # 确定实际要抓取的页数
            pages_to_crawl = min(total_pages, max_pages)
            print(f"深创投公告：检测到总页数 {total_pages}，准备抓取前 {pages_to_crawl} 页...")

            # 2. 循环爬取每一页
            for page in range(1, pages_to_crawl + 1):
                page_url = f"{self.base_url}/notice/{page}" if page > 1 else first_page_url
                print(f"正在抓取第 {page} 页: {page_url}")

                if page > 1:
                    page_res = requests.get(page_url, headers=self.headers, timeout=15)
                    page_res.encoding = 'utf-8'
                    page_soup = BeautifulSoup(page_res.text, 'html.parser')
                else:
                    page_soup = soup  # 第一页已经抓过了

                # 提取当前页的数据
                nodes = page_soup.select('.app-page-list-article .item')
                for node in nodes:
                    title_tag = node.select_one('.title a')
                    date_tag = node.select_one('.time')  # 获取日期标签

                    if title_tag:
                        item = {
                            "title": title_tag.get_text(strip=True),
                            "url": self.base_url + title_tag['href'],
                            "date": date_tag.get_text(strip=True) if date_tag else "",  # 新增日期字段
                            "mobileUrl": self.base_url + title_tag['href']
                        }
                        all_items.append(item)

                # 礼貌爬取，稍微停顿
                time.sleep(0.5)

            return self._to_newsnow_format(all_items)

        except Exception as e:
            print(f"抓取深创投多页数据失败: {e}")
            return self._to_newsnow_format([])


# 映射表保持不变
ADAPTER_MAP = {
    "szvc": "get_szvc",
}
