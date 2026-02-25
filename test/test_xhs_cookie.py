from playwright.sync_api import sync_playwright
import os
from dotenv import load_dotenv

load_dotenv()

xhs_cookie = os.getenv('XHS_COOKIE', '')
print(f"XHS_COOKIE length: {len(xhs_cookie)}")

print("\n=== Testing with raw cookie string ===")
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        viewport={"width": 1920, "height": 1080},
        locale="zh-CN",
    )
    
    page = context.new_page()
    
    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)
    
    print("\n1. Visiting xiaohongshu.com first...")
    page.goto("https://www.xiaohongshu.com", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(2000)
    
    print("\n2. Setting cookies via JavaScript...")
    cookie_pairs = xhs_cookie.split('; ')
    for pair in cookie_pairs[:10]:
        if '=' in pair:
            idx = pair.index('=')
            name = pair[:idx]
            value = pair[idx+1:]
            try:
                page.evaluate(f"document.cookie = '{name}={value}; domain=.xiaohongshu.com; path=/';")
            except Exception as e:
                print(f"Error setting {name}: {e}")
    
    print("\n3. Reloading page...")
    page.reload(wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(5000)
    
    html = page.content()
    title = page.title()
    print(f"Page title: {title}")
    
    if "登录后推荐更懂你的笔记" in html or "手机号登录" in html:
        print("\n=== 未登录状态 ===")
        print("Cookie 已过期，请重新获取")
    else:
        print("\n=== 已登录状态 ===")
    
    input("\n按 Enter 关闭浏览器...")
    browser.close()
