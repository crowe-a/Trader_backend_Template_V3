
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from urllib.parse import urlparse, parse_qs
import time,requests,gzip,re,json

def captch_to_main(driver):
    start_time = time.time()
    while time.time() - start_time < 30:
        for request in driver.requests:
            if request.response and "gcaptcha4.geetest.com/load" in request.url:
                print("[✓] Captcha request founded:", request.url)
                raw_body = request.response.body
                # try gzip
                try:
                    decompressed = gzip.decompress(raw_body).decode('utf-8')
                except:
                    # if not gzip , check utf8
                    decompressed = raw_body.decode('utf-8', errors='ignore')

                #print("decode response:\n", decompressed)
                response_text = decompressed  # user comment

                # 1. 
                match = re.search(r'\((\{.*\})\)', response_text, re.S)
                if match:
                    json_str = match.group(1)
                    data = json.loads(json_str)
                    # 2. 
                    payload_value = data["data"]["payload"]
                    process_token = data["data"]["process_token"]
                    lot_number = data["data"]["lot_number"]
                #print("process token",process_token)
                url = request.url
                start_time1 = time.time()
                time.sleep(1)
                while time.time() - start_time1 < 30:
                    try:
                        if 'gcaptcha4.geetest.com/load' in url:
                            #print(f"\n[✓] foundedd urL:\n{url}")
                            
                            parsed_url = urlparse(url)
                            
                            query_params = parse_qs(parsed_url.query)
                            #print(query_params)

                            captcha_id = query_params.get('captcha_id', [None])[0]
                            return [captcha_id,data]
                        time.sleep(1)
                    except:
                        print("geetest.com not found")
            
       