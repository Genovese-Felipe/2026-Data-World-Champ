import time
from playwright.sync_api import sync_playwright

def test_app():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('http://127.0.0.1:3000')
        print("Page loaded")
        time.sleep(3) # Wait for loaders
        page.screenshot(path='screenshot1.png')
        print("Screenshot 1 taken")

        # Click a planet to make sure onPointerDown logic didn't break
        # Sun is likely around the center
        page.mouse.click(page.viewport_size['width'] // 2, page.viewport_size['height'] // 2)
        time.sleep(2)
        page.screenshot(path='screenshot2.png')
        print("Screenshot 2 taken")

        # Wait a bit longer to see if animate crashed
        time.sleep(2)
        page.screenshot(path='screenshot3.png')
        print("Screenshot 3 taken")

        browser.close()

if __name__ == '__main__':
    test_app()
