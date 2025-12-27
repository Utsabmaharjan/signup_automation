from playwright.sync_api import sync_playwright
from utils.test_data import USER_DATA
import time
from datetime import datetime
import requests
import re
import subprocess
import sys

RAPIDAPI_KEY = "aeb766b91dmshd81e4428e9ae274p1db678jsnb860cd66a1f7"
RAPIDAPI_HOST = "temp-email-api-disposable-temporary-email-service.p.rapidapi.com"
BASE_URL = f"https://{RAPIDAPI_HOST}/api/rapidapi/temp-email"


def extract_latest_otp(api_response: dict) -> str:
    """
    Extract OTP from the most recent email message
    """
    messages = api_response.get("member", [])
    if not messages:
        raise Exception("No messages found")

    messages.sort(
        key=lambda m: datetime.fromisoformat(
            m["createdAt"].replace("Z", "+00:00")),
        reverse=True
    )

    latest_message = messages[0]

    text = latest_message.get("intro", "")

    if not text:
        text = latest_message.get("bodyHtml", "")

    match = re.search(r"\b\d{6}\b", text)
    if not match:
        raise Exception("OTP not found in email")

    return match.group()


def get_temp_gmail_account():
    """Create a temporary Gmail account"""
    url = f"{BASE_URL}/new-email"
    response = requests.post(
        url,
        headers={
            "X-Rapidapi-Key": RAPIDAPI_KEY,
            "X-Rapidapi-Host": RAPIDAPI_HOST,
            "Content-Type": "application/json"
        },
        json={}
    )
    response.raise_for_status()
    result = response.json()

    print(result) 

    return {
        "email": result["data"]["email"],
        "token": result["data"]["token"]
    }


def get_messages(email):
    """STEP 2: Get messages from temp Gmail"""
    url = f"{BASE_URL}/show-mails"
    response = requests.get(
        url,
        headers={
            "X-Rapidapi-Key": RAPIDAPI_KEY,
            "X-Rapidapi-Host": RAPIDAPI_HOST,
            "Content-Type": "application/json"
        },
        params={
            "email": email  
        },
        timeout=10
    )
    response.raise_for_status()
    data = response.json()
    return data


def get_otp_from_gmail(email):
    """
    Poll temp email inbox and extract OTP from body_text
    """
    for attempt in range(30):
        time.sleep(3)

        response = get_messages(email)

        emails = response.get("data", [])

        if not emails:
            print(f"[{attempt+1}] No emails yet...")
            continue

        latest_email = emails[0]

        body_text = latest_email.get("body_text", "")

        match = re.search(r"\b\d{6}\b", body_text)
        if match:
            otp = match.group()
            print("OTP received:", otp)
            return otp

        print(f"[{attempt+1}] Email received but OTP not found...")

    raise Exception("OTP not received after retries")


def save_verified_email(email, file_path="verified_email.py"):
    """
    Save or update the verified email in a Python file.
    If the file exists, overwrite the existing email.
    """
    content = f'VERIFIED_EMAIL = "{email}"\n'
    
    with open(file_path, "w") as f:
        f.write(content)
    
    print(f"Verified email saved/updated in {file_path}")


def run_signup():
    with sync_playwright() as p:
        gmail_account = get_temp_gmail_account()
        USER_DATA["email"] = gmail_account["email"]
        USER_DATA['token'] = gmail_account['token']
        print(f"Using temp Gmail: {USER_DATA['email']}, token:{USER_DATA['token']}")

        browser = p.chromium.launch(headless=False, slow_mo=300)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://authorized-partner.vercel.app/", timeout=60000)
        page.wait_for_load_state("networkidle")

        page.click("text=Get Started")
        page.click("button[type='button']")
        page.click("text=Continue")

        page.fill("input[name='firstName']", USER_DATA["first_name"])
        page.fill("input[name='lastName']", USER_DATA["last_name"])
        page.fill("input[name='email']", USER_DATA["email"])
        page.fill("input[name='phoneNumber']", USER_DATA["phone"])
        page.fill("input[name='password']", USER_DATA["password"])
        page.fill("input[name='confirmPassword']", USER_DATA["password"])

        page.click("button:has-text('Next')")

        page.wait_for_selector("input[data-input-otp='true']", timeout=15000)
        otp = get_otp_from_gmail(gmail_account["email"])
        page.fill("input[data-input-otp='true']", otp)
        page.click("button:has-text('Verify')")
        
        save_verified_email(USER_DATA["email"])

        page.fill("input[name='agency_name']", USER_DATA["agency_name"])
        page.fill("input[name='role_in_agency']", USER_DATA["role_in_agency"])
        page.fill("input[name='agency_email']", USER_DATA["agency_email"])
        page.fill("input[name='agency_website']", USER_DATA["agency_website"])
        page.fill("input[name='agency_address']", USER_DATA["agency_address"])

        regions = ["Canada", "United Kingdom"]
        page.locator("button[role='combobox']").first.click()
        for region in regions:
            page.locator(f"text={region}").click()

        page.click("button:has-text('Next')")

        page.locator("button[role='combobox']").filter(
            has_text="Experience").click()
        page.locator("div[role='listbox'] >> text=5 years").click()

        page.fill(
            "input[name='number_of_students_recruited_annually']",
            USER_DATA["number_of_students_recruited_annually"]
        )
        page.fill("input[name='focus_area']", USER_DATA["focus_area"])
        page.fill("input[name='success_metrics']",
                  USER_DATA["success_metrics"])

        for i in [0, 2, 3]:
            page.locator("button[role='checkbox']").nth(i).click()

        page.click("button:has-text('Next')")

        page.fill(
            "input[name='business_registration_number']",
            USER_DATA["business_registration_number"]
        )

        page.locator("button[role='combobox']").first.click()

        for region in regions:
            page.locator(f"text={region}").click()

        checkboxes_to_select = [0, 2, 3]
        for i in checkboxes_to_select:
            page.locator("button[role='checkbox']").nth(i).click()


#         page.click("button[role='combobox']")

        page.fill(
            "input[name='certification_details']",
            USER_DATA["certification_details"]
        )

        page.set_input_files(
            "input[type='file']",
            "images/logo3.png"
        )

        page.click("button:has-text('Submit')")

        page.wait_for_timeout(5000)
        print("Signup automation completed successfully")

        print("Opening login automation...")
        subprocess.run([sys.executable, "login_automation_script.py"])
        browser.close()
        # print("Opening login automation...")
        # subprocess.run([sys.executable, "login_test.py"])


if __name__ == "__main__":
    run_signup()
