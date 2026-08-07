from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 1024})
    page.goto('http://127.0.0.1:3000')
    page.wait_for_timeout(2000)

    page.screenshot(path='screenshot.png')
    browser.close()
