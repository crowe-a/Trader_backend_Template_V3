from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from bot import open_browser
import time
from selenium.webdriver.common.keys import Keys 
import websocket
import json,requests

def execute_buy(pair, amount):
    driver = open_browser.driver
    wait = WebDriverWait(driver, 15)

    # Click the "all" button
    # sellbutton = wait.until(EC.element_to_be_clickable((By.XPATH,
    #     '//*[@id="spot-layout"]/div[1]/div/div[3]/div/div[2]/div/div/div[2]/div[1]/div[2]'
    # )))
    # sellbutton.click()

   # Find the quantity input
    
    amount_input = wait.until(EC.presence_of_element_located((By.XPATH,
        "//div[text()='Total']/following-sibling::div//input"
    )))
    
    # 1) Normal clear
    amount_input.clear()
    
   # 2) Clear with CTRL+A and Backspace
    amount_input.send_keys(Keys.CONTROL + "a")
    amount_input.send_keys(Keys.BACKSPACE)

    #3) Empty the warranty with JavaScript
    driver.execute_script("arguments[0].value = '';", amount_input)

    # Write the new value
    amount_input.send_keys(str(amount))

    # Click the "Sell" confirmation button
    # confirm_button = wait.until(EC.element_to_be_clickable((By.XPATH,
    #     "//button[contains(text(), 'Buy')]"
    # )))
    # confirm_button.click()

    buybutton = wait.until(EC.element_to_be_clickable((By.XPATH,
        '//*[@id="spot-layout"]/div[2]/div/div[2]/div[4]/button'
    )))
    buybutton.click()
    # 

    return {
        "pair": pair,
        "type": "Buy",
        "amount": amount
    }


def execute_sell(pair, amount):
    driver = open_browser.driver
    wait = WebDriverWait(driver, 15)
    
    # sellbutton = wait.until(EC.element_to_be_clickable((By.XPATH,
    #     '//*[@id="spot-layout"]/div[1]/div/div[3]/div/div[2]/div/div/div[2]/div[1]/div[3]'
    # )))
    # sellbutton.click()

    
    # Find the quantity input
    amount_input = wait.until(EC.presence_of_element_located((By.XPATH,
        "//div[text()='Total']/following-sibling::div//input"
    )))

    # 1) Normal clear
    amount_input.clear()
    
    # 2) Clear with CTRL+A and Backspace
    amount_input.send_keys(Keys.CONTROL + "a")
    amount_input.send_keys(Keys.BACKSPACE)

    # 3)Empty the warranty with JavaScript
    driver.execute_script("arguments[0].value = '';", amount_input)

    # Write the new value
    amount_input.send_keys(str(amount))

    # Click the "Sell" confirmation button
    # confirm_button = wait.until(EC.element_to_be_clickable((By.XPATH,
    #     "//button[contains(text(), 'Sell')]"
    # )))
    # confirm_button.click()
    sellbuton = wait.until(EC.element_to_be_clickable((By.XPATH,
        '//*[@id="spot-layout"]/div[2]/div/div[2]/div[4]/button'
    )))
    sellbuton.click()

    return {
        "pair": pair,
        "type": "sell",
        "amount": amount
    }

def search(symbol):
    # driver = open_browser.driver
    # wait = WebDriverWait(driver, 15)

    driver = open_browser.driver
    driver.get(f"https://www.bydfi.com/en/spot/{symbol}")

    wait = WebDriverWait(driver, 15)

    #  buy button click
    buybutton = wait.until(EC.element_to_be_clickable((By.XPATH,
        '//*[@id="spot-layout"]/div[1]/div/div[2]/div/div[1]/span[1]/div'
    )))
    buybutton.click()
    time.sleep(1)

    container_xpath = "/html/body/div[3]/div/div/div/div/div/div[5]/div"

    container = wait.until(EC.presence_of_element_located((By.XPATH, container_xpath)))
    items = container.find_elements(By.XPATH, "./div")

    coin_list = []
    for item in items:
        try:
            coin_name = item.find_element(By.CSS_SELECTOR, "div.name-wrapper > span:first-child").text.strip()
            quote_coin = item.find_element(By.CSS_SELECTOR, "span.quoteCoin").text.strip()
            price = item.find_element(By.CSS_SELECTOR, "div.price").text.strip()
            change = item.find_element(By.CSS_SELECTOR, "div.change > span.rate").text.strip()
            coin_list.append({
                "coin": coin_name,
                "quote": quote_coin,
                "price": price,
                "change": change
            })
        except Exception as e:
            print("Hata:", e)
   
    return coin_list
    

def getcloseopen(symbol):
    try:
        
        driver = open_browser.driver
        #wait = WebDriverWait(driver, 15)
        
        
        # # target URL eth_usdt is given as an example
        url = f"https://www.bydfi.com/en/swap/{symbol}"
        driver.get(url)
        time.sleep(10)
        seconds_back=60
        now = int(time.time())          # integer timestamp
        from_ts = now - seconds_back
        upper_symbol=symbol.upper()
        print("upper_symbol :",upper_symbol)
        url = "https://www.bydfi.com/api/tv/tradingView/history"
        params = {
            "symbol": str(upper_symbol),
            "resolution": "1",
            "from": from_ts,
            "to": now
        }
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Cookie": "TOKEN=ebfbadd5-4b9c-46b7-a901-4d6886260ff8;"
        }

        r = requests.get(url, params=params, headers=headers)
        data = r.json()
        
        if data.get("s") != "ok" or not data.get("c"):
            print("No data received, possibly the interval is too short or the bar has not yet formed.")
            return None

        print("open:", data["o"][-1])
        print("close:", data["c"][-1])
        print("high:", data["h"][-1])
        print("low:", data["l"][-1])
        print("vol:", data["v"][-1])
        print("time (timestamp):", data["t"][-1])
        return data
        # for example
        # for i in range(50):
        #     get_eth_ohlcv_safe(60)  # son 60 saniyeyi al
        
        
    except KeyboardInterrupt:
        print("live stope")

        #k /html/body/div[3]/div[3]/div[2]/div[1]/div[2]/div[2]/div[1]/div[2]/div/div[2]/div/div/div[2]/div/div[5]/div[2]
        #a /html/body/div[3]/div[3]/div[2]/div[1]/div[2]/div[2]/div[1]/div[2]/div/div[2]/div/div/div[2]/div/div[2]/div[2]
