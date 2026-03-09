from playwright.sync_api import sync_playwright

def run():
    print("Starting Playwright check...")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        errors = []
        page.on("pageerror", lambda err: errors.append(f"Page Error: {err}"))
        page.on("console", lambda msg: errors.append(f"Console {msg.type}: {msg.text}") if msg.type in ["error", "warning"] else None)

        print("Navigating to login...")
        page.goto("http://127.0.0.1:5000/login")
        page.fill("input[name='username']", "admin")
        page.fill("input[name='password']", "admin123")
        page.click("button[type='submit']")
        
        print("Waiting for page load...")
        page.wait_for_timeout(3000)
        
        print("Captured Errors:")
        for e in errors:
            print("-", e)
        page.screenshot(path="/tmp/admin_test.png")
        print("Screenshot saved to /tmp/admin_test.png")
        browser.close()

if __name__ == "__main__":
    run()
