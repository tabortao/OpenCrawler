import asyncio
import hashlib
import json
import os
import re
import time
from datetime import datetime
from typing import Any, Optional
from urllib.parse import urlparse, quote

import httpx
from dotenv import load_dotenv
from playwright.async_api import async_playwright, BrowserContext, Page

load_dotenv()

XHS_COOKIE = os.getenv("XHS_COOKIE", "")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
BROWSER_DATA_DIR = os.path.join(os.getcwd(), "browser_data", "xhs")


class XiaoHongShuCrawler:
    def __init__(self):
        self.index_url = "https://www.xiaohongshu.com"
        self.api_host = "https://edith.xiaohongshu.com"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        self.browser_context: Optional[BrowserContext] = None
        self.context_page: Optional[Page] = None
        self.cookie_dict: dict[str, str] = {}
        self._playwright = None
        self._browser = None

    async def start(self, headless: bool = True) -> None:
        from playwright.async_api import async_playwright
        self._playwright = await async_playwright().start()
        
        chromium = self._playwright.chromium
        self.browser_context = await self.launch_browser(chromium, headless=headless)
        
        stealth_js_path = os.path.join(os.path.dirname(__file__), "libs", "stealth.min.js")
        if os.path.exists(stealth_js_path):
            await self.browser_context.add_init_script(path=stealth_js_path)
        else:
            await self.browser_context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh', 'en']
                });
                window.chrome = { runtime: {} };
            """)
        
        self.context_page = await self.browser_context.new_page()
        await self.context_page.goto(self.index_url)
        
        if XHS_COOKIE:
            await self.login_by_cookie(XHS_COOKIE)
        
        if not await self.check_login_state():
            print("[XiaoHongShuCrawler] 未检测到登录状态，尝试二维码登录...")
            await self.login_by_qrcode()
        
        await self.update_cookies()
        print("[XiaoHongShuCrawler] 登录成功!")

    async def launch_browser(self, chromium, headless: bool = True) -> BrowserContext:
        os.makedirs(BROWSER_DATA_DIR, exist_ok=True)
        
        browser_context = await chromium.launch_persistent_context(
            user_data_dir=BROWSER_DATA_DIR,
            accept_downloads=True,
            headless=headless,
            viewport={"width": 1920, "height": 1080},
            user_agent=self.user_agent,
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
        )
        return browser_context

    async def check_login_state(self) -> bool:
        try:
            user_profile_selector = "xpath=//a[contains(@href, '/user/profile/')]//span[text()='我']"
            is_visible = await self.context_page.is_visible(user_profile_selector, timeout=2000)
            if is_visible:
                return True
        except Exception:
            pass
        
        current_cookie = await self.browser_context.cookies()
        self.cookie_dict = self._convert_cookies_to_dict(current_cookie)
        return bool(self.cookie_dict.get("web_session"))

    async def login_by_cookie(self, cookie_str: str) -> None:
        print("[XiaoHongShuCrawler] 使用 Cookie 登录...")
        cookie_dict = self._convert_str_cookie_to_dict(cookie_str)
        cookies_to_add = []
        for key, value in cookie_dict.items():
            cookies_to_add.append({
                'name': key,
                'value': value,
                'domain': ".xiaohongshu.com",
                'path': "/"
            })
        await self.browser_context.add_cookies(cookies_to_add)
        await self.context_page.reload()
        await asyncio.sleep(2)

    async def login_by_qrcode(self) -> None:
        print("[XiaoHongShuCrawler] 请扫描二维码登录...")
        
        try:
            login_button = await self.context_page.wait_for_selector(
                selector="xpath=//*[@id='app']/div[1]/div[2]/div[1]/ul/div[1]/button",
                timeout=5000
            )
            await login_button.click()
        except Exception:
            pass
        
        qrcode_selector = "xpath=//img[@class='qrcode-img']"
        try:
            qrcode_img = await self.context_page.wait_for_selector(qrcode_selector, timeout=5000)
            print("[XiaoHongShuCrawler] 二维码已显示，请使用小红书 App 扫码登录...")
        except Exception:
            print("[XiaoHongShuCrawler] 未找到二维码，请手动登录...")
        
        no_logged_in_session = self.cookie_dict.get("web_session", "")
        
        max_wait_time = 120
        while max_wait_time > 0:
            await asyncio.sleep(1)
            max_wait_time -= 1
            
            try:
                user_profile_selector = "xpath=//a[contains(@href, '/user/profile/')]//span[text()='我']"
                is_visible = await self.context_page.is_visible(user_profile_selector, timeout=500)
                if is_visible:
                    print("[XiaoHongShuCrawler] 登录成功!")
                    return
            except Exception:
                pass
            
            current_cookie = await self.browser_context.cookies()
            current_dict = self._convert_cookies_to_dict(current_cookie)
            current_web_session = current_dict.get("web_session")
            
            if current_web_session and current_web_session != no_logged_in_session:
                print("[XiaoHongShuCrawler] 登录成功!")
                return
            
            if max_wait_time % 10 == 0:
                print(f"[XiaoHongShuCrawler] 等待扫码登录，剩余 {max_wait_time} 秒...")
        
        raise Exception("登录超时")

    async def update_cookies(self) -> None:
        current_cookie = await self.browser_context.cookies()
        self.cookie_dict = self._convert_cookies_to_dict(current_cookie)

    def _convert_cookies_to_dict(self, cookies: list) -> dict[str, str]:
        return {cookie['name']: cookie['value'] for cookie in cookies}

    def _convert_str_cookie_to_dict(self, cookie_str: str) -> dict[str, str]:
        cookie_dict = {}
        for item in cookie_str.split('; '):
            if '=' in item:
                idx = item.index('=')
                key = item[:idx]
                value = item[idx+1:]
                cookie_dict[key] = value
        return cookie_dict

    def _decode_unicode(self, s: str) -> str:
        if not s:
            return s
        try:
            if '\\u' in s:
                import codecs
                decoded = codecs.decode(s, 'unicode_escape')
                return decoded
            return s
        except Exception:
            return s

    def _decode_json_string(self, s: str) -> str:
        if not s:
            return s
        try:
            return s.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')
        except Exception:
            return s

    def _extract_desc_from_html(self, html: str) -> str:
        if not html:
            return ""
        
        desc = ""
        
        desc_matches = re.findall(r'"desc"\s*:\s*"((?:[^"\\]|\\.)*)"', html, re.DOTALL)
        
        if desc_matches:
            for match in desc_matches:
                decoded = self._decode_json_string(match)
                try:
                    decoded = self._decode_unicode(decoded)
                except Exception:
                    pass
                if len(decoded) > len(desc):
                    desc = decoded
        
        if not desc:
            meta_match = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', html)
            if meta_match:
                desc = meta_match.group(1)
        
        return desc.strip()

    async def get_note_by_url(self, url: str) -> dict[str, Any]:
        note_id, xsec_token, xsec_source = self._parse_note_url(url)
        
        if "xhslink.com" in url.lower():
            print(f"[XiaoHongShuCrawler] 访问短链接: {url}")
            await self.context_page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)
            final_url = self.context_page.url
            print(f"[XiaoHongShuCrawler] 重定向到: {final_url}")
            note_id, xsec_token, xsec_source = self._parse_note_url(final_url)
        
        if not note_id:
            raise ValueError("无法解析笔记 URL")
        
        note_detail = await self.get_note_by_id(note_id, xsec_source or "pc_share", xsec_token or "")
        
        if not note_detail:
            note_detail = await self.get_note_by_id_from_html(note_id, xsec_source or "pc_share", xsec_token or "")
        
        return note_detail

    def _parse_note_url(self, url: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
        parsed = urlparse(url)
        
        if "xhslink.com" in url:
            return None, None, None
        
        path_parts = parsed.path.split('/')
        note_id = None
        for part in path_parts:
            if len(part) == 24 and part.isalnum():
                note_id = part
                break
        
        query_params = {}
        if parsed.query:
            for param in parsed.query.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    query_params[key] = value
        
        xsec_token = query_params.get('xsec_token')
        xsec_source = query_params.get('xsec_source', 'pc_share')
        
        return note_id, xsec_token, xsec_source

    async def get_note_by_id(self, note_id: str, xsec_source: str, xsec_token: str) -> Optional[dict]:
        uri = "/api/sns/web/v1/feed"
        data = {
            "source_note_id": note_id,
            "image_formats": ["jpg", "webp", "avif"],
            "extra": {"need_body_topic": 1},
            "xsec_source": xsec_source,
            "xsec_token": xsec_token,
        }
        
        try:
            headers = await self._build_headers(uri, data, "POST")
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_host}{uri}",
                    json=data,
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success") and result.get("items"):
                        return result["items"][0].get("note_card", {})
        except Exception as e:
            print(f"[XiaoHongShuCrawler] API 请求失败: {e}")
        
        return None

    async def get_note_by_id_from_html(self, note_id: str, xsec_source: str, xsec_token: str) -> Optional[dict]:
        url = f"https://www.xiaohongshu.com/explore/{note_id}?xsec_token={xsec_token}&xsec_source={xsec_source}"
        
        try:
            await self.context_page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)
            
            html = await self.context_page.content()
            return self._extract_note_from_html(note_id, html)
        except Exception as e:
            print(f"[XiaoHongShuCrawler] HTML 解析失败: {e}")
        
        return None

    def _extract_note_from_html(self, note_id: str, html: str) -> Optional[dict]:
        try:
            start_idx = html.find('window.__INITIAL_STATE__')
            if start_idx != -1:
                json_start = html.find('{', start_idx)
                if json_start != -1:
                    brace_count = 0
                    json_end = json_start
                    in_string = False
                    escape_next = False
                    
                    for i, char in enumerate(html[json_start:], json_start):
                        if escape_next:
                            escape_next = False
                            continue
                        if char == '\\':
                            escape_next = True
                            continue
                        if char == '"' and not escape_next:
                            in_string = not in_string
                            continue
                        if in_string:
                            continue
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                json_end = i + 1
                                break
                    
                    if json_end > json_start:
                        json_str = html[json_start:json_end]
                        try:
                            state = json.loads(json_str)
                            note_detail = state.get("note", {}).get("noteDetailMap", {}).get(note_id, {}).get("note", {})
                            if note_detail:
                                return {
                                    "note_id": note_id,
                                    "title": note_detail.get("title", ""),
                                    "desc": note_detail.get("desc", ""),
                                    "type": note_detail.get("type", "normal"),
                                    "user": note_detail.get("user", {}),
                                    "image_list": note_detail.get("imageList", []),
                                    "video": note_detail.get("video", {}),
                                    "interact_info": note_detail.get("interactInfo", {}),
                                    "time": note_detail.get("time", 0),
                                    "liked_count": note_detail.get("interactInfo", {}).get("likedCount", 0),
                                    "collected_count": note_detail.get("interactInfo", {}).get("collectedCount", 0),
                                    "comment_count": note_detail.get("interactInfo", {}).get("commentCount", 0),
                                    "share_count": note_detail.get("interactInfo", {}).get("shareCount", 0),
                                }
                        except json.JSONDecodeError as e:
                            print(f"[XiaoHongShuCrawler] JSON 解析失败: {e}")
                            image_urls = re.findall(r'"urlDefault"\s*:\s*"([^"]+)"', html)
                            image_urls += re.findall(r'"url_default"\s*:\s*"([^"]+)"', html)
                            
                            title = ""
                            title_match = re.search(r'<title>([^<]+)</title>', html)
                            if title_match:
                                title = title_match.group(1).replace(" - 小红书", "").strip()
                            
                            desc = self._extract_desc_from_html(html)
                            
                            if title or desc or image_urls:
                                return {
                                    "note_id": note_id,
                                    "title": title,
                                    "desc": desc,
                                    "type": "normal",
                                    "user": {},
                                    "image_list": [{"url": self._decode_unicode(url), "url_default": self._decode_unicode(url)} for url in image_urls[:9]],
                                    "video": {},
                                    "interact_info": {},
                                }
            
            title_match = re.search(r'<title>([^<]+)</title>', html)
            if title_match:
                title = title_match.group(1).replace(" - 小红书", "").strip()
                
                desc = self._extract_desc_from_html(html)
                
                image_urls = re.findall(r'data-src="([^"]+)"', html)
                image_urls += re.findall(r'src="https://[^"]*xhscdn[^"]*"', html)
                image_list = [{"url": url, "url_default": url} for url in image_urls[:9]]
                
                return {
                    "note_id": note_id,
                    "title": title,
                    "desc": desc,
                    "type": "normal",
                    "user": {},
                    "image_list": image_list,
                    "video": {},
                    "interact_info": {},
                }
        except Exception as e:
            print(f"[XiaoHongShuCrawler] 提取笔记内容失败: {e}")
        
        return None

    async def _build_headers(self, uri: str, data: dict, method: str = "POST") -> dict:
        a1 = self.cookie_dict.get("a1", "")
        signs = await self._sign_with_playwright(uri, data, a1, method)
        
        cookie_str = "; ".join([f"{k}={v}" for k, v in self.cookie_dict.items()])
        
        return {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9",
            "cache-control": "no-cache",
            "content-type": "application/json;charset=UTF-8",
            "origin": "https://www.xiaohongshu.com",
            "pragma": "no-cache",
            "referer": "https://www.xiaohongshu.com/",
            "sec-ch-ua": '"Chromium";v="122", "Google Chrome";v="122", "Not.A/Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": self.user_agent,
            "Cookie": cookie_str,
            "X-S": signs["x-s"],
            "X-T": signs["x-t"],
            "x-S-Common": signs["x-s-common"],
            "X-B3-Traceid": signs["x-b3-traceid"],
        }

    async def _sign_with_playwright(self, uri: str, data: dict, a1: str, method: str = "POST") -> dict:
        sign_str = self._build_sign_string(uri, data, method)
        md5_str = hashlib.md5(sign_str.encode("utf-8")).hexdigest()
        
        try:
            x3_value = await self.context_page.evaluate(f"window.mnsv2('{sign_str}', '{md5_str}')")
        except Exception:
            x3_value = ""
        
        x_s = self._build_xs_payload(x3_value or "")
        x_t = str(int(time.time() * 1000))
        
        b1 = await self._get_b1_from_localstorage()
        x_s_common = self._build_xs_common(a1, b1, x_s, x_t)
        
        return {
            "x-s": x_s,
            "x-t": x_t,
            "x-s-common": x_s_common,
            "x-b3-traceid": self._get_trace_id(),
        }

    def _build_sign_string(self, uri: str, data: dict, method: str) -> str:
        if method.upper() == "POST":
            c = uri
            if data:
                c += json.dumps(data, separators=(",", ":"), ensure_ascii=False)
            return c
        else:
            if not data:
                return uri
            params = []
            for key in sorted(data.keys()):
                value = data[key]
                if isinstance(value, list):
                    value_str = ",".join(str(v) for v in value)
                elif value is not None:
                    value_str = str(value)
                else:
                    value_str = ""
                value_str = quote(value_str, safe='')
                params.append(f"{key}={value_str}")
            return f"{uri}?{'&'.join(params)}"

    def _build_xs_payload(self, x3_value: str) -> str:
        s = {
            "x0": "4.2.1",
            "x1": "xhs-pc-web",
            "x2": "Windows",
            "x3": x3_value,
            "x4": "object",
        }
        import base64
        json_str = json.dumps(s, separators=(",", ":"))
        return "XYS_" + base64.b64encode(json_str.encode("utf-8")).decode("utf-8")

    def _build_xs_common(self, a1: str, b1: str, x_s: str, x_t: str) -> str:
        import base64
        payload = {
            "s0": 3,
            "s1": "",
            "x0": "1",
            "x1": "4.2.2",
            "x2": "Windows",
            "x3": "xhs-pc-web",
            "x4": "4.74.0",
            "x5": a1,
            "x6": x_t,
            "x7": x_s,
            "x8": b1,
            "x9": self._mrc(x_t + x_s + b1),
            "x10": 154,
            "x11": "normal",
        }
        json_str = json.dumps(payload, separators=(",", ":"))
        return base64.b64encode(json_str.encode("utf-8")).decode("utf-8")

    def _mrc(self, s: str) -> str:
        result = []
        for i, c in enumerate(s):
            result.append(chr(ord(c) ^ (i % 7 + 1)))
        return "".join(result)

    def _get_trace_id(self) -> str:
        import random
        chars = "0123456789abcdef"
        trace_id = "".join(random.choice(chars) for _ in range(32))
        return trace_id

    async def _get_b1_from_localstorage(self) -> str:
        try:
            local_storage = await self.context_page.evaluate("() => window.localStorage")
            return local_storage.get("b1", "")
        except Exception:
            return ""

    async def close(self):
        try:
            if self.browser_context:
                await self.browser_context.close()
        except Exception as e:
            print(f"[XiaoHongShuCrawler] 关闭浏览器时出错: {e}")
        
        try:
            if self._playwright:
                await self._playwright.stop()
        except Exception as e:
            print(f"[XiaoHongShuCrawler] 关闭 Playwright 时出错: {e}")


def _remove_xhs_tags(text: str) -> str:
    """
    移除小红书话题标签
    
    将 #xxx[话题]# 格式的标签完全移除，保留原有换行
    """
    if not text:
        return ""
    
    xhs_tag_pattern = r'[ \t]*#([^#\[\]]+)\[话题\]#[ \t]*'
    text = re.sub(xhs_tag_pattern, '', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def convert_note_to_markdown(note: dict, url: str) -> str:
    """
    将小红书笔记转换为 Markdown 格式
    
    Args:
        note: 笔记数据字典，包含 title、desc、image_list 等字段
        url: 笔记原始链接
    
    Returns:
        转换后的 Markdown 文本
    """
    title = note.get("title", "小红书笔记")
    desc = note.get("desc", "")
    image_list = note.get("image_list", [])
    
    lines = [
        f"> 来源: [{url}]({url})",
        "",
        "---",
        "",
    ]
    
    if desc:
        desc = _remove_xhs_tags(desc)
        lines.append(desc)
        lines.append("")
    
    if image_list:
        lines.append("## 图片")
        lines.append("")
        for i, img in enumerate(image_list):
            img_url = img.get("url_default") or img.get("url", "")
            if img_url:
                lines.append(f"![图片{i+1}]({img_url})")
                lines.append("")
    
    return "\n".join(lines)


async def crawl_xiaohongshu(url: str, headless: bool = True) -> dict[str, Any]:
    """
    爬取小红书笔记
    
    Args:
        url: 小红书笔记链接
        headless: 是否使用无头模式
    
    Returns:
        包含笔记信息的字典
    
    Raises:
        ValueError: 当 Cookie 过期或无法获取内容时抛出
    """
    crawler = XiaoHongShuCrawler()
    try:
        await crawler.start(headless=headless)
        
        # 检查登录状态
        is_logged_in = await crawler.check_login_state()
        if not is_logged_in:
            raise ValueError(
                "小红书 Cookie 已过期，请更新 Cookie。\n"
                "解决方法：\n"
                "1. 打开小红书网页版并登录\n"
                "2. 按 F12 打开开发者工具，在 Application -> Cookies 中复制 Cookie\n"
                "3. 更新 .env 文件中的 XHS_COOKIE 变量"
            )
        
        note = await crawler.get_note_by_url(url)
        
        if note:
            # 检查是否获取到有效内容
            title = note.get("title", "")
            desc = note.get("desc", "")
            image_list = note.get("image_list", [])
            
            if not title and not desc and not image_list:
                raise ValueError(
                    "无法获取笔记内容，可能是 Cookie 已过期。\n"
                    "解决方法：\n"
                    "1. 打开小红书网页版并登录\n"
                    "2. 按 F12 打开开发者工具，在 Application -> Cookies 中复制 Cookie\n"
                    "3. 更新 .env 文件中的 XHS_COOKIE 变量"
                )
            
            markdown = convert_note_to_markdown(note, url)
            return {
                "title": note.get("title", "小红书笔记"),
                "markdown": markdown,
                "url": url,
                "note": note,
            }
        else:
            raise ValueError(
                "无法获取笔记内容，可能是 Cookie 已过期或链接无效。\n"
                "解决方法：\n"
                "1. 检查链接是否正确\n"
                "2. 更新 .env 文件中的 XHS_COOKIE 变量"
            )
    finally:
        await crawler.close()
