
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from backend.listen_mail import checkmail
from selenium.webdriver.support.ui import WebDriverWait
import time

def open_button_with_js(driver,wait,timeout=10):
    """
    Captcha sonrası login butonunu aktif edip tıklayan ve
    mail kodunu giren fonksiyon.
    """

    # 1. Login butonunu bul
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div[1]/div[1]/div[2]/div/div/div[2]'))
        )
    except:
        print("[!] Login butonu bulunamadı.")
        return False

    # 2. JavaScript ile 'geetest_disable' class'ını kaldır
    driver.execute_script("""
        arguments[0].classList.remove('geetest_disable');
    """, element)
    print("[✓] Captcha sonrası buton aktif edildi.")

    # 3. Butona tıkla
    try:
        element.click()
        print("[✓] Login butonuna tıklandı.")
    except:
        print("[!] Login butonuna tıklanamadı.")
        return False

    # 4. Mail kodu alanını bekle
    try:
        mail_code_input = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div[4]/div/div[2]/div/div[2]/div[2]/div/div/div/div/div/input'))
        )
    except:
        print("[!] Mail kodu alanı bulunamadı.")
        return False

    # 5. Mail kodunu çek ve yaz
    code = checkmail()
    if not code:
        print("[!] Mail kodu alınamadı.")
        return False

    mail_code_input.clear()
    mail_code_input.send_keys(code)
    print(f"[✓] Mail kodu girildi: {code}")

    return True
