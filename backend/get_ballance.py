
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from seleniumwire import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from bot import open_browser
# open_browser.driver


import time
def get_bl():
    # send_but = open_browser.wait.until(EC.element_to_be_clickable((
    # By.XPATH,
    #     '//*[@id="uni-layout"]/header/div[2]/div[2]'
    # )))
    # send_but.click()
    open_browser.driver.get("https://partner.bydfi.com/en/account/fund-management/assets-overview/pnl-analysis?type=asset-spot")
    time.sleep(1)
    XPATH_LIST = [
    # '/html/body/div[3]/div/div[3]/div/div/div[2]/div/div[3]/a/div/div/div[2]/div/p',
    # '/html/body/div[3]/div/div[3]/div/div/div[2]/div/div[4]/a/div/div/div[2]/div/p',
    # '/html/body/div[3]/div/div[3]/div/div/div[2]/div/div[5]/a/div/div/div[2]/div/p',
    # '/html/body/div[3]/div/div[3]/div/div/div[2]/div/div[6]/a/div/div/div[2]/div/p',
    '//*[@id="uni-layout"]/main/div/div/div[2]/div/div[2]/div[1]/div[1]'
]
    balances = []
    try:
        for xpath in XPATH_LIST:
            try:
                element = open_browser.wait.until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
                text_value = element.text.strip()
                balances.append(text_value)
            except:
                balances.append(None)  # Bulunamadıysa None ekle
        print(balances)
        return balances
    except Exception as e:
        return f"Hata: {e}"
    
    