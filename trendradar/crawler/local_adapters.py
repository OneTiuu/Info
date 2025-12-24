# coding=utf-8
import requests
import json
from bs4 import BeautifulSoup

class LocalAdapters:
    """本地官网爬虫适配器集合"""

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def _to_newsnow_format(self, items):
        """统一封装成 NewsNow 的 API 返回格式"""
        return json.dumps({
            "status": "success",
            "items": items
        }, ensure_ascii=False)

    def get_szvc(self):
        """深创投官网公告适配器"""
        url = "https://www.szvc.com.cn/notice"
        try:
            res = requests.get(url, headers=self.headers, timeout=15)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            # 这里的 CSS 选择器是你提供的 HTML 结构中的关键点
            nodes = soup.select('.app-page-list-article .item')
            
            items = []
            for node in nodes:
                title_tag = node.select_one('.title a')
                if title_tag:
                    items.append({
                        "title": title_tag.get_text(strip=True),
                        "url": "https://www.szvc.com.cn" + title_tag['href'],
                        "mobileUrl": "https://www.szvc.com.cn" + title_tag['href']
                    })
            return self._to_newsnow_format(items)
        except Exception as e:
            return None

    def get_szse(self):
        """示例：深交所公告适配器（如果需要，按照类似逻辑添加）"""
        # 这里写深交所的爬取逻辑...
        return self._to_newsnow_format([])

# 映射表：ID 对应 处理函数
ADAPTER_MAP = {
    "szvc": "get_szvc",
    "szse": "get_szse", # 以后在这里加一行即可
}
