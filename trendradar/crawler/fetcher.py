# coding=utf-8
"""
数据获取器模块

负责从 指定公告网页 抓取公告数据（适配https://www.szvc.com.cn/notice），支持：
- 单个平台数据获取
- 批量平台数据爬取
- 自动重试机制
- 代理支持
"""

import json
import random
import time
from typing import Dict, List, Tuple, Optional, Union

import requests
from bs4 import BeautifulSoup  # 新增：用于网页解析

class DataFetcher:
    """数据获取器（适配公告网页爬取）"""

    # 默认目标公告链接（你指定的爬取地址）
    DEFAULT_API_URL = "https://www.szvc.com.cn/notice"

    # 默认请求头（增强适配性）
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "Cache-Control": "no-cache",
        "Referer": DEFAULT_API_URL
    }

    def __init__(
        self,
        proxy_url: Optional[str] = None,
        api_url: Optional[str] = None,
    ):
        """
        初始化数据获取器

        Args:
            proxy_url: 代理服务器 URL（可选）
            api_url: 目标公告页面URL（可选，默认使用你指定的公告链接）
        """
        self.proxy_url = proxy_url
        # 优先使用传入的url，否则用默认公告链接
        self.api_url = api_url or self.DEFAULT_API_URL

    def fetch_data(
        self,
        id_info: Union[str, Tuple[str, str]],
        max_retries: int = 2,
        min_retry_wait: int = 3,
        max_retry_wait: int = 5,
    ) -> Tuple[Optional[str], str, str]:
        """
        获取公告页面数据（适配原接口，id_info仅作为标识使用）

        Args:
            id_info: 标识名称 或 (标识名称, 别名) 元组（仅用于日志/标识，无实际请求作用）
            max_retries: 最大重试次数
            min_retry_wait: 最小重试等待时间（秒）
            max_retry_wait: 最大重试等待时间（秒）

        Returns:
            (响应文本(模拟JSON格式), 标识ID, 别名) 元组，失败时响应文本为 None
        """
        # 解析标识信息（兼容原接口）
        if isinstance(id_info, tuple):
            id_value, alias = id_info
        else:
            id_value = id_info
            alias = id_value

        # 代理配置
        proxies = None
        if self.proxy_url:
            proxies = {"http": self.proxy_url, "https": self.proxy_url}

        retries = 0
        while retries <= max_retries:
            try:
                # 请求目标公告页面
                response = requests.get(
                    self.api_url,
                    proxies=proxies,
                    headers=self.DEFAULT_HEADERS,
                    timeout=15,
                )
                response.raise_for_status()  # 非200状态码抛异常
                response.encoding = response.apparent_encoding  # 自动识别编码

                # 解析公告页面（核心：适配目标网站的HTML结构）
                soup = BeautifulSoup(response.text, "html.parser")
                notice_items = []

                # ========== 关键解析逻辑（适配目标网站）==========
                # 匹配公告列表项（已适配szvc.com.cn的公告页面结构，若后续结构变化可微调）
                list_items = soup.select("div[class*='notice'] li, ul[class*='notice'] li, .news-list li, .notice-list li")
                
                for idx, item in enumerate(list_items):
                    # 提取标题
                    title_tag = item.find("a")
                    if not title_tag:
                        continue
                    title = title_tag.get_text(strip=True)
                    if not title:
                        continue

                    # 提取链接（补全相对链接）
                    url = title_tag.get("href", "")
                    if url and not url.startswith(("http://", "https://")):
                        url = requests.compat.urljoin(self.api_url, url)
                    
                    # 提取移动端链接（无则复用普通链接）
                    mobile_url = url

                    # 封装成原API格式的item
                    notice_items.append({
                        "title": title,
                        "url": url,
                        "mobileUrl": mobile_url
                    })
                # ========== 解析结束 ==========

                # 模拟原API的JSON响应格式（保证后续处理逻辑兼容）
                mock_api_response = {
                    "status": "success",
                    "items": notice_items
                }
                data_text = json.dumps(mock_api_response, ensure_ascii=False)

                print(f"获取 {id_value} 成功（共{len(notice_items)}条公告）")
                return data_text, id_value, alias

            except Exception as e:
                retries += 1
                if retries <= max_retries:
                    # 指数退避重试等待
                    base_wait = random.uniform(min_retry_wait, max_retry_wait)
                    additional_wait = (retries - 1) * random.uniform(1, 2)
                    wait_time = base_wait + additional_wait
                    print(f"请求 {id_value} 失败: {e}. {wait_time:.2f}秒后重试...")
                    time.sleep(wait_time)
                else:
                    print(f"请求 {id_value} 失败: {e}")
                    return None, id_value, alias

        return None, id_value, alias

    def crawl_websites(
        self,
        ids_list: List[Union[str, Tuple[str, str]]],
        request_interval: int = 100,
    ) -> Tuple[Dict, Dict, List]:
        """
        爬取公告数据（兼容原接口，ids_list为标识列表）

        Args:
            ids_list: 标识列表，每个元素可以是字符串或 (标识, 别名) 元组（例如["szvc_notice"]）
            request_interval: 请求间隔（毫秒）

        Returns:
            (结果字典, ID到名称的映射, 失败ID列表) 元组
        """
        results = {}
        id_to_name = {}
        failed_ids = []

        for i, id_info in enumerate(ids_list):
            # 解析标识和名称
            if isinstance(id_info, tuple):
                id_value, name = id_info
            else:
                id_value = id_info
                name = id_value

            id_to_name[id_value] = name
            # 调用fetch_data获取公告数据
            response, _, _ = self.fetch_data(id_info)

            if response:
                try:
                    # 解析模拟的API响应
                    data = json.loads(response)
                    results[id_value] = {}

                    # 处理每条公告（兼容原逻辑）
                    for index, item in enumerate(data.get("items", []), 1):
                        title = item.get("title")
                        # 过滤无效标题
                        if title is None or isinstance(title, float) or not str(title).strip():
                            continue
                        title = str(title).strip()
                        url = item.get("url", "")
                        mobile_url = item.get("mobileUrl", "")

                        # 去重+记录排名
                        if title in results[id_value]:
                            results[id_value][title]["ranks"].append(index)
                        else:
                            results[id_value][title] = {
                                "ranks": [index],
                                "url": url,
                                "mobileUrl": mobile_url,
                            }
                except json.JSONDecodeError:
                    print(f"解析 {id_value} 响应失败")
                    failed_ids.append(id_value)
                except Exception as e:
                    print(f"处理 {id_value} 数据出错: {e}")
                    failed_ids.append(id_value)
            else:
                failed_ids.append(id_value)

            # 请求间隔（最后一个不等待）
            if i < len(ids_list) - 1:
                actual_interval = request_interval + random.randint(-10, 20)
                actual_interval = max(50, actual_interval)  # 最小间隔50ms
                time.sleep(actual_interval / 1000)

        print(f"\n爬取完成 | 成功: {list(results.keys())}, 失败: {failed_ids}")
        return results, id_to_name, failed_ids
