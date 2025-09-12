
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from backend.listen_mail import checkmail
from selenium.webdriver.support.ui import WebDriverWait
import time

def open_button_with_js(driver,wait,timeout=10):
    """
    The function that activates the login button after the captcha, clicks it, and enters the email code..
    """

    # 1. find Login button
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div[1]/div[1]/div[2]/div/div/div[2]'))
        )
    except:
        print("[!] Login butonu bulunamadı.")
        return False

    # 2. dele 'geetest_disable' class with js 
    driver.execute_script("""
        arguments[0].classList.remove('geetest_disable');
    """, element)
    print("[✓] Button was activated after Captcha.")

    # 3. click button
    try:
        element.click()
        print("[✓] The Login button was clicked.")
    except:
        print("[!] The Login button wasn't clicked..")
        return False

    # 4. Wait for the zip code field
    try:
        mail_code_input = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div[4]/div/div[2]/div/div[2]/div[2]/div/div/div/div/div/input'))
        )
    except:
        print("[!] The zip code field was not found.")
        return False

    # 5. Take your zip code and write it down
    code = checkmail()
    if not code:
        print("[!] Could not get the mail code.")
        return False

    mail_code_input.clear()
    mail_code_input.send_keys(code)
    print(f"[✓]Email code entered: {code}")

    return True
