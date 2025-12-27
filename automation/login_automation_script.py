from playwright.sync_api import sync_playwright
from utils.test_data import USER_DATA
from utils.verified_email import VERIFIED_EMAIL

def run_login():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://authorized-partner.vercel.app/", timeout=60000)
        page.wait_for_load_state("networkidle")

        page.click("text=Login")
        page.fill("input[name='email']", VERIFIED_EMAIL)
        page.fill("input[name='password']", USER_DATA["password"])
        page.click("button:has-text('Log In')")



        page.wait_for_timeout(50000000)
        print(" Login completed successfully")

        browser.close()

if __name__ == "__main__":
    run_login()
