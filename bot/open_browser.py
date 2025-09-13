from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from urllib.parse import urlparse, parse_qs
import logging, os, threading, psycopg2, requests
import time,requests,re,json,gzip,re,zlib,httpx,asyncio

from backend.testfromforum import capsolver 
from backend.trade_executor import getcloseopen
from backend import market_func
from backend.listen_mail import checkmail
from backend.imap import listen_mail_imap
from backend.config import CAPSOLVER_API_KEY,EMAIL,PASSWORD,LOGIN_URL

# from capthsolv2 import solve_geetest_v4
# from captcha_solver import solve_captcha

from fastapi import FastAPI, HTTPException, Query
import db
from functools import wraps


# from requesttosite import req

EMAIL = EMAIL
PASSWORD = PASSWORD
running = False  # the bot is working

validate__token = None
cikti_json = None
edit_order=None
driver = None
wait = None

log = logging.getLogger(__name__)

open_position_list=[]
open_order_list=[]
position_main_list=[]
order_main_list=[]


retrun_list=[]
"""
--------------------check admin control funtions begin------------


"""

JS_FILE = "user_list.js"
 
def update_amount(username, new_amount, path=JS_FILE):
    users = load_users_from_js(path)
    for user in users:
        if user["username"] == username:
            user["amount"] = new_amount
            break
    save_users_to_js(users, path)

def save_users_to_js(users, path=JS_FILE):
    new_content = "const users = " + json.dumps(users, indent=2, ensure_ascii=False) + ";"
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)

def load_users_from_js(path=JS_FILE):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r"\[.*\]", content, re.S)
    if not match:
        raise ValueError("Kullanıcı listesi bulunamadı")
    return json.loads(match.group(0))

def is_admin(username, path="active_users.js"):
    users = load_users_from_js(path)
    for user in users:
        if user["username"] == username and user.get("role") == "admin":
            return True
    return False


"""
--------------------check admin control funtions end----------------


"""



""" comfigure orders"""

def check_id(orders_list):
    global s_sol_id
    for i in orders_list:
        if i[2]=='ssol-susdt':
            s_sol_id=i[0]
            # print("ssol_id: ",type(s_sol_id))
def req_interceptor(request):
    if "bydfi.com/testnet/private/future/order/edit_order" in request.url and request.method == "POST":
        
        # print("[edit_order] request caught. Changing body...")
        try:
            if request.body:
                
                # print("old lenght",type(len(request.body)),len(request.body))#178
                data = json.loads(request.body.decode("utf-8"))
                # print("Orijinal body:", data)
                
                try:
                    # Changes on the body
                    data['originalOrderId'] = str(market_func.order_control_id)
                    data['symbol'] = str(market_func.order_control_symbol)#'ssol-susdt'
                    data['price'] = market_func.order_control_price#221.12  # string fiyat
                    data["side"]= str(market_func.order_control_side)
                    data["orderQty"]= int(market_func.order_control_qty)
                    # Encode et
                    # print("body : ",data)#
                    new_body = json.dumps(data, separators=(',', ':')).encode("utf-8")
                    request.body = new_body
                    if "Content-Length" in request.headers:
                        del request.headers['Content-Length']
                    
                    

                except Exception as inner_e:
                    print("error 1:", inner_e)

        except Exception as e:
            print("req_interceptor error:", e)
            
    elif "bydfi.com/testnet/private/future/order/otoco" in request.url and request.method == "POST":
        print("[order] req...")

        
        try:
            #{"symbol":"sxrp-susdt","orderQty":8375,"future":0,"price":"2.7737","side":1,"type":"1","source":1}

            data = json.loads(request.body.decode("utf-8"))
                # print("Orijinal body:", data)
                
            try:
                # Changes on the body
                print("old body",data)
                data_edidted=market_func.global_otoco_list[1]
                # data={'symbol': 'ssol-susdt', 'orderQty': 2, 'future': 0, 'price': '224.385', 'side': 2, 'type': '1', 'source': 1}
                data=data_edidted
                # Encode 
                # print("body : ",data)#
                print("new body",data)
                new_body = json.dumps(data, separators=(',', ':')).encode("utf-8")
                request.body = new_body
                if "Content-Length" in request.headers:
                        del request.headers['Content-Length']
            except:
                print("body didint changed")



            # data = json.loads(request.body.decode("utf-8"))
            # if data:
            #     print("body: ",data)
                
            #     print("goba otocolist: ",data_edidted)
            #     print("goba otocolist: ",market_func.global_otoco_list[1])
                

        except:
            print("otoco req change error")

    # elif "bydfi.com/testnet/private/future/order" in request.url and request.method == "DELETE":
    #     try:
    #         if request.body:
                
    #             # print("old lenght",type(len(request.body)),len(request.body))#178
    #             data = json.loads(request.body.decode("utf-8"))
    #             # print("Orijinal body:", data)
                
    #             try:
    #                 # Body üzerinde değişiklik
    #                 data['originalOrderId'] = str(market_func.order_control_id)
    #                 data['symbol'] = str(market_func.order_control_symbol)#'ssol-susdt'
    #                 #data['price'] = market_func.order_control_price#221.12  # string fiyat
    #                 data["orderType"]= str(market_func.order_control_side)
    #                 data["orderQty"]= int(market_func.order_control_qty)
    #                 # Encode et
    #                 # print("body : ",data)#
    #                 new_body = json.dumps(data, separators=(',', ':')).encode("utf-8")
    #                 request.body = new_body
    #                 if "Content-Length" in request.headers:
    #                     del request.headers['Content-Length']
                    
    #                 #request.headers["Content-Length"] = int(len(new_body))
    #                 # request.headers["Content-Length"] = len(new_body)

    #                 # print("new lenght",len(new_body))#177
    #                 # print("new 2 lenght",request.headers["Content-Length"])#178
    #                 # Content-Length güncelle
    #                 # request.headers["Content-Length"] = str(len(new_body))
    #                 #request.headers["Content-Type"] = "application/json"
    #                 # print("id symbol price",market_func.order_control_id,market_func.order_control_symbol,market_func.order_control_price)
    #                 # print("new  body:", data)

    #             except Exception as inner_e:
    #                 print("error 1:", inner_e)

    #     except Exception as e:
    #         print("req_interceptor error:", e)
                
new_body_bytes_open_order=None
def combined_interceptor(request, response):
    global cikti_json, validate__token,new_body_bytes_open_order,edit_order
    
    global captured_headers
    global captured_body
    # print(f"[Interceptor] URL: {request.url}")

    # === Geetest verify response ===
    if cikti_json and "gcaptcha4.geetest.com/verify" in request.url:
        # print("Changing [Interceptor] verify response...")

       # Get callback parameter from URL
        parsed = urlparse(request.url)
        callback_name = parse_qs(parsed.query).get("callback", ["callback"])[0]

        # Convert JSON to string
        json_str = json.dumps(cikti_json)

       # Convert to JSONP format: geetest_xxxxx({...})
        jsonp_body = f"{callback_name}({json_str})"

        # Write Body
        response.body = jsonp_body.encode("utf-8")
        response.headers["Content-Type"] = "application/javascript"
        if "Content-Encoding" in response.headers:
            del response.headers["Content-Encoding"]

    
       # print("New verify response added:", jsonp_body[:200], "...")


    # === bydfi validate answer ===
    elif validate__token and "bydfi.com/api/public/captcha/validate" in request.url:#/api/public/captcha/validate
        # print("[Interceptor] Changing Validate response...")
        
        json_str = json.dumps(validate__token)
        response.body = json_str.encode("utf-8")
        response.headers["Content-Type"] = "application/json"
        if "Content-Encoding" in response.headers:
            del response.headers["Content-Encoding"]
        # print("New validate response added:", json_str)

    

    elif "/testnet/private/future/wallet/position" in request.url:
        # print("\n[Position data captured]...")
        open_position_list=[]
            
        # Get the response body and decode it as UTF-8
        try:
           # Load the response body in JSON format
            # Get the response body
            body = response.body
            
           # Check response headers
            content_encoding = response.headers.get('Content-Encoding', '')
            
            # If the response is compressed, uncompress it
            if 'gzip' in content_encoding:
                try:
                    body = gzip.decompress(body)
                except (gzip.BadGzipFile, zlib.error) as e:
                    # print(f"Error while decompressing gzip: {e}")
                    return
            elif 'deflate' in content_encoding:
                try:
                    body = zlib.decompress(body)
                except zlib.error as e:
                    # print(f"Error while deflating: {e}")
                    return
            
            # After decompression, decode the body as UTF-8 and convert it to JSON
            try:
                response_body = json.loads(body.decode("utf-8"))
                
                # Print JSON data in human-readable (indented) format
                # print(json.dumps(response_body, indent=4, ensure_ascii=False))
                #open_position_list.append(json.dumps(response_body, indent=4, ensure_ascii=False))
                parse_positions(json.dumps(response_body, indent=4, ensure_ascii=False))
            except json.JSONDecodeError as e:
                print(f"Response is not in JSON format: {e}")
                # print("Raw Response:", body.decode("utf-8", errors='ignore'))
        except json.JSONDecodeError as e:
            # JSON çözme hatası olursa
            print(f"Response not in JSON format: {e}")
            # print("Raw Response:", response.body.decode("utf-8"))

    elif "/testnet/private/future/wallet/order/openOrders" in request.url:
       # print("\n[open orders data captured]...")
        open_order_list=[]
        # Get the response body and decode it as UTF-8
        try:
            body = response.body
            
            # Check response headers
            content_encoding = response.headers.get('Content-Encoding', '')
            
           # If the response is compressed, uncompress it
            if 'gzip' in content_encoding:
                try:
                    body = gzip.decompress(body)
                except (gzip.BadGzipFile, zlib.error) as e:
                   # print(f"Error while decompressing gzip: {e}")
                    return
            elif 'deflate' in content_encoding:
                try:
                    body = zlib.decompress(body)
                except zlib.error as e:
                    # print(f"Error while deflating: {e}")
                    return
            
           # After decompression, decode the body as UTF-8 and convert it to JSON
            try:
                response_body = json.loads(body.decode("utf-8"))
                
                # Print JSON data in human-readable (indented) format
                # print(json.dumps(response_body, indent=4, ensure_ascii=False))
                #open_order_list.append(json.dumps(response_body, indent=4, ensure_ascii=False))
                parse_orders(json.dumps(response_body, indent=4, ensure_ascii=False))
                
            except json.JSONDecodeError as e:
                print(f"Response not in JSON format: {e}")
                # print("Raw Response:", body.decode("utf-8", errors='ignore'))
                            
        except json.JSONDecodeError as e:
            # If a JSON decoding error occurs,
            print(f"Response not in JSON format: {e}")
            # print("Raw Response:", response.body.decode("utf-8"))
    
    elif "wss://testnetws.bydfi.in/wsquote" in request.url:
        # print("response :",response)
        print("\n[wsguote ] listeninig")
        # data = json.loads(request.body.decode("utf-8"))
        # print("body:",data)


    elif "bydfi.com/testnet/private/future/order/otoco" in  request.url:
        print("[order] req...")

        try:
           # Load the response body in JSON format
            # Get the response body
            body = response.body
            
            # Check response headers
            content_encoding = response.headers.get('Content-Encoding', '')
            
            # If the response is compressed, uncompress it
            if 'gzip' in content_encoding:
                try:
                    body = gzip.decompress(body)
                except (gzip.BadGzipFile, zlib.error) as e:
                    print(f"Error while decompressing gzip: {e}")
                    return
            elif 'deflate' in content_encoding:
                try:
                    body = zlib.decompress(body)
                except zlib.error as e:
                    print(f"Error while deflating: {e}")
                    return
            
            # After decompression, decode the body as UTF-8 and convert it to JSON
            try:
                response_body = json.loads(body.decode("utf-8"))
                orderId=response_body["data"]["orderId"]

                print("order id",orderId)
                # ["c",{"symbol":"-susdt","orderQty":0,"future":0,"price":"","side":1,"type":"1","source":1},lvx,1,identifier,runner_id]
                runner_id=market_func.global_otoco_list[-1]
                indentifer=market_func.global_otoco_list[-2]
                # print(runner_id,indentifer)
                
                fetchet_list=db.fetch_trade_backup_by_runner_and_identifier(runner_id,indentifer)
                # [{'runner_id': 208, 'identifier': 'ssol', 'first_balance': 1000.0, 'now_balance': 800.0, 'buyed_or_selled_coin_qty': -0.8353660574063555, 'trade_count': 1, 'trade_id': None, 'order_id': None}]
                print("fetchd list",fetchet_list)
                fetchet_list[0]["order_id"]=str(orderId)
                new_dict=fetchet_list[0]
                print("new dict",new_dict)
                db.upsert_trade_backup(new_dict)

                # Print JSON data in readable (indented) format
                # print(json.dumps(response_body, indent=4, ensure_ascii=False))
                #open_position_list.append(json.dumps(response_body, indent=4, ensure_ascii=False))
                #parse_positions(json.dumps(response_body, indent=4, ensure_ascii=False))
            except:
                print(f"Response not in JSON format:")
                # print("Raw Response:", body.decode("utf-8", errors='ignore'))
        except json.JSONDecodeError as e:
            # If a JSON decoding error occurs,
            print(f"Response is not in JSON format: {e}")



def parse_positions(json_data):
    """
    Searches and prints position information in incoming JSON data. Args: json data (str): Position data in JSON format.

    """
    global position_main_list
    position_main_list=[]
    
    try:
        # Convert JSON string to Python dictionary
        data = json.loads(json_data)

        # Check if there is a list under the "data" key
        if "data" in data and isinstance(data["data"], list):
            positions = data["data"]
            
            # Loop through each position
            for i, position in enumerate(positions):
                position_list=[]
                # print(f"--- Data for Position #{i+1} ---")
                # Print each variable
                # print(f"Position ID: {position.get('positionId')}")
                # print(f"Wallet: {position.get('subWallet')}")
                # print(f"Symbol: {position.get('symbol')}")
                # print(f"Current Position: {position.get('currentPosition')}")
                # print(f"Available Position: {position.get('availPosition')}")
                # print(f"Cost Price: {position.get('avgCostPrice')}")
                # print(f"Mark Price: {position.get('markPrice')}")
                # print(f"Realized P/L: {position.get('realizedPnl')}")
                # print(f"Liquidation Price: {position.get('liquidationPrice')}")
                # print(f"Margin: {position.get('margin')}")
                # print(f"Side: {position.get('side')}") # 1: Long, 2: Short
                # print(f"Leverage: {position.get('leverage')}")
                # print(f"Position Type: {position.get('positionType')}")
                # print(f"Close Status: {position.get('isClose')}")
                # print(f"Close Order ID: {position.get('closeOrderId')}")
                # print(f"Close Order Price: {position.get('closeOrderPrice')}")
                # print(f"Close Order Volume: {position.get('closeOrderVolume')}")
                # print(f"Base Precision: {position.get('basePrecision')}")
                # print(f"Display Precision: {position.get('baseShowPrecision')}")
                # print(f"Orders: {position.get('orders')}")
                # print(f"Margin Type: {position.get('marginType')}")
                # print(f"Maximum Additional Margin: {position.get('maxAddMargin')}")
                # print(f"Maximum Subtractable Margin: {position.get('maxSubMargin')}")
                # print(f"Minimum Margin Ratio (MMR): {position.get('mmr')}")
                # print(f"Risk Ratio (r): {position.get('r')}")
                # print(f"Account Balance (accb): {position.get('accb')}")
                # print(f"Frozen): {position.get('frozen')}")
                # print(f"Maintenance Margin (mm): {position.get('mm')}")
                # print(f"Automatic Margin Addition: {position.get('autoAddMargin')}")
                # print(f"Callback Value: {position.get('callbackValue')}")
                # print(f"Planned Order Size: {position.get('planOrderSize')}")

                # print("Pnl: ",position.get('realizedPnl'))
                position_list.append(position.get('positionId'))
                position_list.append(position.get('symbol'))
                position_list.append(position.get('avgCostPrice'))
                #position_list.append(position.get('positionId'))
                position_main_list.append(position_list)
        else:
            print("The 'data' key or list format was not found in the JSON data.")
        
        # print("position main list",position_main_list)
        position_main_list2=position_main_list
        #return position_main_list 

    except json.JSONDecodeError as e:
        print(f"Error while parsing JSON data: {e}")


def parse_orders(json_data):
    """
   Parses and prints order information from incoming JSON data.

    Args:
    json_data (str): Order data in JSON format.
    """
    global order_main_list,order_delete_list
    order_main_list=[]
    order_delete_list=[]
   
    try:
        # Load the JSON string into a Python dictionary
        response_data = json.loads(json_data)
        # print("response data:",response_data)
        # Access the 'data' key, then the 'pageData' list within it
        if "data" in response_data and "pageData" in response_data["data"]:
            orders = response_data["data"]["pageData"]

            if orders:
                # print("--- Extracting Order Data ---")
                # print(f"Total orders found: {len(orders)}\n")
                # print(f"Total orders found: {orders}\n")
                
                # Iterate through each order in the list
                for i, order in enumerate(orders):
                    # print(f"--- Order #{i+1} ---")
                    order_list=[]
                    
                    # Safely extract and print each key-value pair
                    # using the .get() method for robustness
                    order_type = order.get("orderType")
                    order_id = order.get("orderId")
                    symbol = order.get("symbol")
                    volume = order.get("volume")
                    side = order.get("side")
                    position_side = order.get("positionSide")
                    position_avg_price = order.get("positionAvgPrice")
                    position_volume = order.get("positionVolume")
                    reduce_only = order.get("reduceOnly")
                    close_position = order.get("closePosition")
                    action = order.get("action")
                    price = order.get("price")
                    avg_price = order.get("avgPrice")
                    deal_volume = order.get("dealVolume")
                    status = order.get("status")
                    order_type_str = order.get("type") # Renamed to avoid conflict with order_type variable
                    creation_time = order.get("ctime")
                    uid = order.get("uid")
                    sub_wallet = order.get("subWallet")
                    contract_id = order.get("contractId")
                    modification_time = order.get("mtime")
                    fixed_price = order.get("fixedPrice")
                    direction = order.get("direction")
                    trigger_price = order.get("triggerPrice")
                    price_type = order.get("priceType")
                    base_precision = order.get("basePrecision")
                    base_show_precision = order.get("baseShowPrecision")
                    strategy_type = order.get("strategyType")
                    leverage_level = order.get("leverageLevel")
                    margin_type = order.get("marginType")
                    remark = order.get("remark")
                    callback_rate = order.get("callbackRate")
                    callback_value = order.get("callbackValue")
                    trigger_orders = order.get("triggerOrders")
                    otoco_order = order.get("otocoOrder")
                                    
                    # print(f"  Order Type: {order_type}")
                    # print(f"  Order ID: {order_id}")
                    # print(f"  Symbol: {symbol}")
                    # print(f"  Volume: {volume}")
                    # print(f"  Side: {side}")
                    # print(f"  Price: {price}")
                    # print(f"  Status: {status}")
                    # print("-" * 25)
                    # id,side,symbol,oQty,price

                    order_list.append(order_id)
                    order_list.append(side)
                    order_list.append(symbol)
                    order_list.append(volume)
                    order_list.append(price)
                    order_main_list.append(order_list)
                    
            else:
                print("No orders found in 'pageData' list.")
        else:
            print("Invalid JSON structure. 'data' or 'pageData' key is missing.")
        # print("order main list:",order_main_list)
        order_main_list2=order_main_list
        # check_id(order_main_list)""
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON: {e}")
# Chrome options# Lock object to make Selenium thread-safe
driver_lock = threading.Lock()

req=None



def retry(times=3, delay=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"{func.__name__} failed: {e}, retrying {attempt+1}/{times}")
                    time.sleep(delay)
            return False
        return wrapper
    return decorator




def email_info_write():
    
    driver.get('https://www.bydfi.com/en/login')

    wait = WebDriverWait(driver, 10)
    # Bağlantı aç

    # import db
    # from datetime import datetime
    
    # conn = db.connect()
    # cur = conn.cursor()
    
    # # DB bağlantısı aç
    # with db.connect() as conn, conn.cursor() as cur:
    #     cur.execute("SELECT * FROM trades ORDER BY entry_time DESC LIMIT 1000")
    #     all_trades = cur.fetchall()
    #     # print("all trades", all_trades)
    #     # print("all trades",all_trades)
    # # Çıktıyı görmek
    # for trade in all_trades:
    #     print(trade)

    # for trade in all_trades:
    #     print(trade)
    # wait mail and passposrt
    email_input = wait.until(EC.presence_of_element_located((
    By.XPATH,
    '//*[@id="uni-layout"]/main/div/div/div[2]/div/div[1]/div/div/div/div[1]/div/div/input'
    
    )))
    email_input.clear()
    email_input.send_keys(EMAIL)
    time.sleep(0.1)

    # find passport input
    password_input = wait.until(EC.presence_of_element_located((
        By.XPATH,
        '//*[@id="uni-layout"]/main/div/div/div[2]/div/div[1]/div/div/div/div[2]/div/div/input'
    )))
    password_input.clear()
    password_input.send_keys(PASSWORD)
    time.sleep(0.1)

    # enter enter button
    login_button = wait.until(EC.element_to_be_clickable((
        By.XPATH,
        '//*[@id="uni-layout"]/main/div/div/div[2]/div/div[1]/div/div/div/div[3]/button'
    )))
    login_button.click()

    for request in driver.requests:
        if request.response and "gcaptcha4.geetest.com/load" in request.url:
            raw_body = request.response.body
            
            
            return True,request
        
    return False,None

def raw_body_decompres(request):
    try:
        raw_body = request.response.body
        #time.sleep(5)
        # first gzip
        try:
            decompressed = gzip.decompress(raw_body).decode('utf-8')
        except:
            # If not gzip, decode directly to UTF-8
            decompressed = raw_body.decode('utf-8', errors='ignore')

        #print("Decompressed answer:\n", decompressed)
        response_text = decompressed  # response

        # 1.Extract JSON from callback brackets
        match = re.search(r'\((\{.*\})\)', response_text, re.S)
        if match:
            json_str = match.group(1)
            data = json.loads(json_str)

            # 2. Get the payload value
            payload_value = data["data"]["payload"]
            process_token = data["data"]["process_token"]
            lot_number = data["data"]["lot_number"]
            #print("Payload:", payload_value)
            url = request.url
            if 'gcaptcha4.geetest.com/load' in url:
                
                return True,url,lot_number,payload_value,process_token
    except:
        return False,None,None,None,None
        print("")

def before_capsolver(url,lot_number,payload_value,process_token):

    parsed_url = urlparse(url)
                                
    query_params = parse_qs(parsed_url.query)
    #print(query_params)

    captcha_id = query_params.get('captcha_id', [None])[0]
    call_back=query_params.get('callback', [None])[0]
    print("capth id:",captcha_id)

    response=capsolver(captcha_id)
    if response!=None:
        
        return True,response,lot_number,payload_value,process_token
    return False,None,None,None,None
def after_capsolver(response,lot_number,payload_value,process_token):
    #print(response)
    captcha_id2 = response['captcha_id']
    captcha_output = response['captcha_output']
    gen_time = response['gen_time']
    lot_number2 = response['lot_number']
    pass_token = response['pass_token']
    risk_type = response['risk_type']
    user_agent = response['userAgent']

    
    
    global cikti_json
    cikti_json={
    "status": "success",
    "data": {
        "lot_number": lot_number,
        "result": "success",
        "fail_count": 0,
        "seccode": 
        {'captcha_id': captcha_id2, 
        'captcha_output': captcha_output, 
        'gen_time': gen_time,
        'lot_number': lot_number, 
        'pass_token': pass_token},

        "score": "12",
        "payload": payload_value,
        "process_token": process_token,
        "payload_protocol": 1
    }
    }
    


    url_validate = "https://www.bydfi.com/api/geetest/validate"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": response.get('userAgent', 'Mozilla/5.0'),
        "Referer": "https://www.bydfi.com/"
    }
    data_validate = {
        "captcha_id": response['captcha_id'],
        "lot_number": response['lot_number'],
        "captcha_output": response['captcha_output'],
        "pass_token": response['pass_token'],
        "gen_time": response['gen_time']
    }
    validate_resp = requests.post(url_validate, headers=headers, json=data_validate)
    if validate_resp.status_code==200:
        # validate_response(validate_resp)
        return True,validate_resp
        
    return False,None
def validate_response(validate_resp):
    #print("validate resp: ",validate_resp.json())
    
    print("validate resp",validate_resp)
    global validate__token
    validate__token={
                    "code": 200,
                    "message": "",
                    "data": {
                        "valid": "true",
                        "token": validate_resp.json()["data"]["token"]
                    }
                } 
    return True
    
    
def scriptc():
    try:                                        #/html/body/div[3]/div[1]/div[1]/div[2]/div/div/div[2]
                                                #/html/body/div[4]/div[1]/div[1]/div[2]/div/div/div[2]
                                                #/html/body/div[3]/div[1]/div[1]/div[2]/div/div/div[2]
        element = driver.find_element(By.XPATH, '/html/body/div[3]/div[1]/div[1]/div[2]/div/div/div[2]')

        # Remove class with JavaScript
        driver.execute_script("""
        arguments[0].classList.remove('geetest_disable');
        """, element)
        # time.sleep(1)
        submit_button = driver.find_element(By.XPATH, '/html/body/div[3]/div[1]/div[1]/div[2]/div/div/div[2]')  # login buton xpath
        submit_button.click()
        # time.sleep(1)

        #print(checkmail())

        
        # find passport input
        mail_code = wait.until(EC.presence_of_element_located((
            By.XPATH,
            '//*[@id="uni-layout"]/main/div/div/div[2]/div/div/div/div[2]/div/div[2]/div/input[1]'
            # '/html/body/div[4]/div/div[2]/div/div[2]/div[2]/div/div/div/div/div/input'
        )))#
        mail_code.clear()
        try:
            i=0
            for i in range(10):
                x=listen_mail_imap()
                # x=checkmail()
                time.sleep(15)
                if x!= "":
                    break
                i+=1
        
        except:
            print("code not found")
        
        try:
            mail_code.click()  # önce inputa tıkla
            mail_code.send_keys(Keys.CONTROL, 'a')  # tümünü seç
            mail_code.send_keys(Keys.CONTROL, 'c')  # kopyala
            mail_code.send_keys(x)
        except:
            print("mail verf code send error")
        time.sleep(1)
        
                        # enter enter button
        login_button = wait.until(EC.element_to_be_clickable((
            By.XPATH,
            '/html/body/div[4]/div[1]/div[1]/div[2]/div/div/div[2]'
        )))
        login_button.click()
        return True
    except:
        return False
        print("script")


def run():
    # go page
    global position_main_list2,order_main_list2
    global running,driver,wait
    running = True
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')  # work in back screen
    options.add_argument('--start-maximized')
    options.add_argument('--lang=en')
    options.add_argument("--proxy-bypass-list=<-loopback>")
    seleniumwire_options = {
                'request_storage': 'memory'
            }

    # Driver başlat
    driver = webdriver.Chrome(options=options,seleniumwire_options=seleniumwire_options)
    options.add_experimental_option("detach", True)
    
    driver.response_interceptor = combined_interceptor
    driver.request_interceptor=req_interceptor
    driver.get('https://www.bydfi.com/en/login')

    wait = WebDriverWait(driver, 10)
    # 

    # import db
    # from datetime import datetime
    
    # conn = db.connect()
    # cur = conn.cursor()
    
    # # DB connection
    # with db.connect() as conn, conn.cursor() as cur:
    #     cur.execute("SELECT * FROM trades ORDER BY entry_time DESC LIMIT 1000")
    #     all_trades = cur.fetchall()
    #     # print("all trades", all_trades)
    #     # print("all trades",all_trades)
    # # Çıktıyı görmek
    # for trade in all_trades:
    #     print(trade)

    # for trade in all_trades:
    #     print(trade)
    # wait mail and passposrt
    while True:
        f,request=email_info_write()
        time.sleep(5)
        print("f req",f,request)
        if f==True:
            print("email info status",f)
            break
    while True:
        f,url,lot_number,payload_value,process_token=raw_body_decompres(request)
        time.sleep(1)
        if True==f:
            print("raw_body_decompres info status",f)
            break
    while True:
        f,response,lot_number,payload_value,process_token=before_capsolver(url,lot_number,payload_value,process_token)
        time.sleep(1)
        if True==f:
            print("before_capsolver info status",f)
            break

    while True:
        f,validate_resp=after_capsolver(response,lot_number,payload_value,process_token)
        time.sleep(1)
        if True==f:
            print("after_capsolver info status",f)
            break
    while True:
        f=validate_response(validate_resp)
        time.sleep(1)
        if True==f:
            print("validate_response info status",f)
            break 
    while True:
        time.sleep(5)
        
        current_url = driver.current_url
        print(f"current URL: {current_url}")

        if current_url == "https://www.bydfi.com/en":
            """ dummy beign"""
            # payload={'identifier': "ssol", 'kind': 'open', 'Recalc': True, 'chart': {'url': 'https://www.tradingview.com/chart/JSAqsyMo/', 'interval': '1m'}, 'trade': {'id': '825', 'entry_type': 'Entry', 'entry_signal': 'Strong Sell, Open', 'entry_price': 224.38, 'entry_time': 'Sep 11, 2025, 00:07', 'position': '0.39, 86.32 usdt'}, 'raw': {'num': '825', 'signal': 'Strong Sell, Open', 'type': 'Entry', 'open_time': 'Sep 11, 2025, 00:07', 'close_time': 'Sep 11, 2025, 00:07', 'open_price': '224.38', 'close_price': '224.38', 'position_size': '0.39, 86.32 usdt'}}

            # market_func.getpayload(payload)
            """ dummy end"""
            break
        f=scriptc()
        
        print("scriptc info status",f)
        if f==True:
            print("scriptc info status",f)
            #dummy()
            
            break
        

    print("url found ")

    
    
        
            


            
    




 

                
    
                
                


                                    
                
                
  
def stop():
    global running, driver,wait
    running = False
    if driver:
        driver.quit()
        driver = None

flag=100
def dummy():
    # order at low price 2.7905
    # sell at high price 2.9005
    # price 2.8105
    
    global driver,flag
    
    current_url = driver.current_url
    print(f"current URL: {current_url}")
    for i in range(5):
        
        payload = {#sxrp-susdt
                'identifier': '1',
                'kind': 'open',
                'Recalc': False,
                'chart': {
                    'url': 'https://www.tradingview.com/chart/JSAqsyMo/',
                    'interval': '1m'
                },
                'trade': {
                    'id': '3249',
                    'entry_type': 'Entry',
                    'entry_signal': 'Strong Buy',
                    'entry_price': 2.9050,
                    'entry_time': 'Aug 24, 2025, 21:40',
                    'position': '50.3 K, 13.42 K usdt'
                },
                'raw': {
                    'num': '3249',
                    'signal': 'Strong Buy',
                    'type': 'Entry',
                    'open_time': 'Aug 24, 2025, 21:40',
                    'close_time': 'Aug 24, 2025, 21:57',
                    'open_price': '2.9050',
                    'close_price': '2.9050',
                    'position_size': '50.3 K, 13.42 K usdt'
                }
            }
        i=0
        # print("waiting first payload")
        time.sleep(35) 
        # print("waiting second payload")
        try:
            market_func.getpayload(payload)
            # print("listeÇ:",order_main_list2,position_main_list2)
        except json.JSONDecodeError as e:
            print(f"get payload second error {e}")
        
        #201.585 sell
        #199.615 buy
            
        payload2 = {#ssol-susdt
                    'identifier': '2',
                    'kind': 'open',
                    'Recalc': False,
                    'chart': {
                        'url': 'https://www.tradingview.com/chart/JSAqsyMo/',
                        'interval': '1m'
                    },
                    'trade': {
                        'id': '3249',
                        'entry_type': 'Entry',
                        'entry_signal': 'Strong Sell, Open',
                        'entry_price': 201.585,
                        'entry_time': 'Aug 24, 2025, 21:40',
                        'position': '50.5 K, 13.42 K usdt'
                    },
                    'raw': {
                        'num': '3249',
                        'signal': 'Strong Sell, Open',
                        'type': 'Entry',
                        'open_time': 'Aug 24, 2025, 21:40',
                        'close_time': 'Aug 24, 2025, 21:57',
                        'open_price': '201.585',
                        'close_price': '201.585',
                        'position_size': '50.5 K, 13.42 K usdt'
                    }
                }

        try:
            time.sleep(15) 
            #  #will be connected to the levarege system
            market_func.getpayload(payload2)
            
            # #print("payload:",payload)
        except Exception as e:
            print("%s payload test sending failed: %s",  e)            
        