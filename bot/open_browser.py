from seleniumwire import webdriver
from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse, parse_qs
from backend.config import CAPSOLVER_API_KEY,EMAIL,PASSWORD,LOGIN_URL
import time,requests

from backend.listen_mail import checkmail
from selenium.webdriver.support.ui import WebDriverWait
# from capthsolv2 import solve_geetest_v4
# from captcha_solver import solve_captcha
from backend.testfromforum import capsolver 
from backend.trade_executor import getcloseopen
import logging, os, threading, psycopg2, requests
from backend import market_func

# from requesttosite import req
import gzip,requests,re,json
import re
import gzip,httpx,asyncio
import zlib
EMAIL = EMAIL
PASSWORD = PASSWORD
running = False  # Bot çalışıyor mu?

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
        
        # print("[edit_order] isteği yakalandı. Body değiştiriliyor...")
        try:
            if request.body:
                
                # print("old lenght",type(len(request.body)),len(request.body))#178
                data = json.loads(request.body.decode("utf-8"))
                # print("Orijinal body:", data)
                
                try:
                    # Body üzerinde değişiklik
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
                    
                    #request.headers["Content-Length"] = int(len(new_body))
                    # request.headers["Content-Length"] = len(new_body)

                    # print("new lenght",len(new_body))#177
                    # print("new 2 lenght",request.headers["Content-Length"])#178
                    # Content-Length güncelle
                    # request.headers["Content-Length"] = str(len(new_body))
                    #request.headers["Content-Type"] = "application/json"
                    # print("id symbol price",market_func.order_control_id,market_func.order_control_symbol,market_func.order_control_price)
                    # print("Yeni body:", data)

                except Exception as inner_e:
                    log.warning("error 1:", inner_e)

        except Exception as e:
            log.warning("req_interceptor error:", e)
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
    #                 # print("Yeni body:", data)

    #             except Exception as inner_e:
    #                 log.warning("error 1:", inner_e)

    #     except Exception as e:
    #         log.warning("req_interceptor error:", e)
                #orderId
#         : 
#         "9097621063784930465"
#         orderType
#         : 
#         1
#         source
#         : 
#         1
#         subWallet
#         : 
#         "W001"
#         symbol
#         : 
# "sxrp-susdt"
    # elif "bydfi.com/testnet/private/future/order/otoco" in request.url and request.method == "POST":
    #     print("[order] isteği yakalandı. Body değiştiriliyor...")

        
    #     try:
    #         #{"symbol":"sxrp-susdt","orderQty":8375,"future":0,"price":"2.7737","side":1,"type":"1","source":1}
    #         if request.body:
                
    #             data = json.loads(request.body.decode("utf-8"))
                

    #             data["symbol"] = "sxrp-susdt"#ssol-susdt
    #             data['price'] = "{:.4f}".format(3.533)  # string olarak 3.0150 yapar 202.385
    #             data['orderQty'] = 120  # string olarak 3.0150 yapar 202.385

    #             if "Content-Length" in request.headers:
    #                     del request.headers['Content-Length']
    #             # data["symbol"] = str("sxrp-susdt")#ssol-susdt
    #             # data['price'] = "{:.4f}".format(3.015)  # string olarak 3.0150 yapar 202.385

    #             # Tekrar encode et
    #             request.body = json.dumps(data, separators=(',', ':')).encode("utf-8")
                
    #             # request.headers["Content-Type"] = "application/json"
    #             #request.headers["Referer"] = "https://www.bydfi.com/en/swap/demo?id=ssol-susdt"
    #             print("new body: ",data)

    #     except Exception as e:
    #         print("req_interceptor error:", e)
       #https://www.bydfi.com/testnet/private/future/close

#

new_body_bytes_open_order=None
def combined_interceptor(request, response):
    global cikti_json, validate__token,new_body_bytes_open_order,edit_order
    global captured_headers
    global captured_body
    # print(f"[Interceptor] URL: {request.url}")

    # === Geetest verify cevabı ===
    if cikti_json and "gcaptcha4.geetest.com/verify" in request.url:
        # print("[Interceptor] verify cevabı değiştiriliyor...")

        # URL'den callback parametresini al
        parsed = urlparse(request.url)
        callback_name = parse_qs(parsed.query).get("callback", ["callback"])[0]

        # JSON'u stringe çevir
        json_str = json.dumps(cikti_json)

        # JSONP formatına çevir: geetest_xxxxx({...})
        jsonp_body = f"{callback_name}({json_str})"

        # Body'yi yaz
        response.body = jsonp_body.encode("utf-8")
        response.headers["Content-Type"] = "application/javascript"
        if "Content-Encoding" in response.headers:
            del response.headers["Content-Encoding"]

        # print("Yeni verify cevabı eklendi:", jsonp_body[:200], "...")


    # === bydfi validate cevabı ===
    elif validate__token and "bydfi.com/api/public/captcha/validate" in request.url:#/api/public/captcha/validate
        # print("[Interceptor] Validate cevabı değiştiriliyor...")
        
        json_str = json.dumps(validate__token)
        response.body = json_str.encode("utf-8")
        response.headers["Content-Type"] = "application/json"
        if "Content-Encoding" in response.headers:
            del response.headers["Content-Encoding"]
        # print("Yeni validate cevabı eklendi:", json_str)
        # print("jason validte",json_str)
        # print("resp body",response.body)
        # print("resp head",response.headers)
    # elif "wss://fquote.bydfi.pro/wsquote" in request.url:
        # print("[fquote dinleniyor]  ...")
        #response.body = json_str.encode("utf-8")
        # print("response :",response)
        #{"data":"{\"symbol\":\"BTC-USDT\",\"r\":\"1\",\"s\":\"ok\",\"t\":1755732540,\"c\":114180.5,\"o\":114192.3,\"h\":114192.5,\"l\":114173.5,\"v\":1924.0,\"isUp\":1,\"price\":114180.5,\"prev\":112872.7,\"buyPrice\":114180.5,\"buyVolume\":0,\"sellPrice\":114180.7,\"sellVolume\":0,\"max\":114569.1,\"min\":112301.9,\"volume\":8917934,\"open\":113297.1,\"close\":112872.7,\"settle_price_yes\":0,\"high_limit\":0,\"low_limit\":0,\"net_value\":0.0}","cmid":"4001"}

        # response.headers["Content-Type"] = "application/json"
        # if "Content-Encoding" in response.headers:
        #     del response.headers["Content-Encoding"]
        # print("Yeni validate cevabı eklendi:", json_str)


    elif "/testnet/private/future/wallet/position" in request.url:
        # print("\n[Pozisyon verisi yakalandı]...")
        open_position_list=[]
            
        # Yanıt gövdesini (body) al ve UTF-8 olarak çöz
        try:
            # Yanıt gövdesini JSON formatında yükle
            # Yanıt gövdesini (body) al
            body = response.body
            
            # Yanıt başlıklarını kontrol et
            content_encoding = response.headers.get('Content-Encoding', '')
            
            # Eğer yanıt sıkıştırılmışsa sıkıştırmayı aç
            if 'gzip' in content_encoding:
                try:
                    body = gzip.decompress(body)
                except (gzip.BadGzipFile, zlib.error) as e:
                    # print(f"Gzip sıkıştırması açılırken hata oluştu: {e}")
                    return
            elif 'deflate' in content_encoding:
                try:
                    body = zlib.decompress(body)
                except zlib.error as e:
                    # print(f"Deflate sıkıştırması açılırken hata oluştu: {e}")
                    return
            
            # Sıkıştırma açıldıktan sonra body'yi UTF-8 olarak çöz ve JSON'a dönüştür
            try:
                response_body = json.loads(body.decode("utf-8"))
                
                # JSON verisini okunabilir (girintili) formatta yazdır
                # print(json.dumps(response_body, indent=4, ensure_ascii=False))
                #open_position_list.append(json.dumps(response_body, indent=4, ensure_ascii=False))
                parse_positions(json.dumps(response_body, indent=4, ensure_ascii=False))
            except json.JSONDecodeError as e:
                print(f"Yanıt JSON formatında değil: {e}")
                # print("Ham Yanıt:", body.decode("utf-8", errors='ignore'))
        except json.JSONDecodeError as e:
            # JSON çözme hatası olursa
            log.warning(f"Yanıt JSON formatında değil: {e}")
            # print("Ham Yanıt:", response.body.decode("utf-8"))

    elif "/testnet/private/future/wallet/order/openOrders" in request.url:
        # print("\n[open orders verisi yakalandı]...")
        open_order_list=[]
        # Yanıt gövdesini (body) al ve UTF-8 olarak çöz
        try:
            body = response.body
            
            # Yanıt başlıklarını kontrol et
            content_encoding = response.headers.get('Content-Encoding', '')
            
            # Eğer yanıt sıkıştırılmışsa sıkıştırmayı aç
            if 'gzip' in content_encoding:
                try:
                    body = gzip.decompress(body)
                except (gzip.BadGzipFile, zlib.error) as e:
                    # print(f"Gzip sıkıştırması açılırken hata oluştu: {e}")
                    return
            elif 'deflate' in content_encoding:
                try:
                    body = zlib.decompress(body)
                except zlib.error as e:
                    # print(f"Deflate sıkıştırması açılırken hata oluştu: {e}")
                    return
            
            # Sıkıştırma açıldıktan sonra body'yi UTF-8 olarak çöz ve JSON'a dönüştür
            try:
                response_body = json.loads(body.decode("utf-8"))
                
                # JSON verisini okunabilir (girintili) formatta yazdır
                # print(json.dumps(response_body, indent=4, ensure_ascii=False))
                #open_order_list.append(json.dumps(response_body, indent=4, ensure_ascii=False))
                parse_orders(json.dumps(response_body, indent=4, ensure_ascii=False))
                
            except json.JSONDecodeError as e:
                print(f"Yanıt JSON formatında değil: {e}")
                # print("Ham Yanıt:", body.decode("utf-8", errors='ignore'))
            
        except json.JSONDecodeError as e:
            # JSON çözme hatası olursa
            print(f"Yanıt JSON formatında değil: {e}")
            # print("Ham Yanıt:", response.body.decode("utf-8"))
    
    elif "wss://testnetws.bydfi.in/wsquote" in request.url:
        # print("response :",response)
        print("\n[wsguote ] listeninig")
        # data = json.loads(request.body.decode("utf-8"))
        # print("body:",data)


    # elif "bydfi.com/testnet/private/future/order/otoco" in request.url and request.method == "POST":
    #     print("[order] isteği yakalandı. Body değiştiriliyor...")

        
    #     # try:
    #     #     #{"symbol":"sxrp-susdt","orderQty":8375,"future":0,"price":"2.7737","side":1,"type":"1","source":1}
    #     #     if request.body:
                
    #     #         # data = json.loads(request.body.decode("utf-8"))
                

    #     #         # data["symbol"] = "sxrp-susdt"#ssol-susdt
    #     #         # data['price'] = "{:.4f}".format(3.533)  # string olarak 3.0150 yapar 202.385
    #     #         # data['orderQty'] = 120  # string olarak 3.0150 yapar 202.385

    #     #         # if "Content-Length" in request.headers:
    #     #         #         del request.headers['Content-Length']
    #     #         # # data["symbol"] = str("sxrp-susdt")#ssol-susdt
    #     #         # # data['price'] = "{:.4f}".format(3.015)  # string olarak 3.0150 yapar 202.385

    #     #         # # Tekrar encode et
    #     #         # request.body = json.dumps(data, separators=(',', ':')).encode("utf-8")
                
    #     #         # request.headers["Content-Type"] = "application/json"
    #     #         #request.headers["Referer"] = "https://www.bydfi.com/en/swap/demo?id=ssol-susdt"
    #     #         print("new body: ",data)

    #     # except Exception as e:
    #     #     print("req_interceptor error:", e)

    #     try:
    #         # Yanıt gövdesini JSON formatında yükle
    #         # Yanıt gövdesini (body) al
    #         body = response.body
            
    #         # Yanıt başlıklarını kontrol et
    #         content_encoding = response.headers.get('Content-Encoding', '')
            
    #         # Eğer yanıt sıkıştırılmışsa sıkıştırmayı aç
    #         if 'gzip' in content_encoding:
    #             try:
    #                 body = gzip.decompress(body)
    #             except (gzip.BadGzipFile, zlib.error) as e:
    #                 # print(f"Gzip sıkıştırması açılırken hata oluştu: {e}")
    #                 return
    #         elif 'deflate' in content_encoding:
    #             try:
    #                 body = zlib.decompress(body)
    #             except zlib.error as e:
    #                 # print(f"Deflate sıkıştırması açılırken hata oluştu: {e}")
    #                 return
            
    #         # Sıkıştırma açıldıktan sonra body'yi UTF-8 olarak çöz ve JSON'a dönüştür
    #         try:
    #             response_body = json.loads(body.decode("utf-8"))
    #             orderId=response_body["data"]["orderId"]
    #             print(orderId)
    #             retrun_list[]
    #             # JSON verisini okunabilir (girintili) formatta yazdır
    #             # print(json.dumps(response_body, indent=4, ensure_ascii=False))
    #             #open_position_list.append(json.dumps(response_body, indent=4, ensure_ascii=False))
    #             #parse_positions(json.dumps(response_body, indent=4, ensure_ascii=False))
    #         except json.JSONDecodeError as e:
    #             print(f"Yanıt JSON formatında değil: {e}")
    #             # print("Ham Yanıt:", body.decode("utf-8", errors='ignore'))
    #     except json.JSONDecodeError as e:
    #         # JSON çözme hatası olursa
    #         log.warning(f"Yanıt JSON formatında değil: {e}")

    # elif "wss://fquote.bydfi.pro/wsquote" in request.url:
    #     print("response :",response)

        


def send_edit_order_sync(body: dict, headers: dict):
        # İstek gönderilecek URL
    time.sleep(0.1)
    url = "https://www.bydfi.com/testnet/private/future/order/edit_order"

    # İstek başlıkları (headers)
    # Bütün header bilgilerini buraya kopyalıyoruz
    headers = headers
    #id=body["originalOrderId"]
    # print("id",id)
    # İstek gövdesi (body). Bu bir JSON verisi olduğundan Python'da sözlük (dictionary) olarak tanımlanır.
    body = body

    # ----------------- Değiştirmek istediğiniz kısımları burada güncelleyin -----------------
    # Örneğin, "orderQty" (miktar) değerini 20 olarak değiştirelim
    #body2["orderQty"] = 20

    # "price" (fiyat) değerini 4.15 olarak değiştirelim
    #body["price"] = 4.15

    # ----------------- İstek Gönderme -----------------
    # requests.post() metodu ile POST isteği gönderiyoruz
    # json=body parametresi, body sözlüğünü otomatik olarak JSON formatına dönüştürüp Content-Type'ı ayarlar.
    try:
        response = requests.post(url, headers=headers, json=body)

        # Yanıt durum kodunu kontrol etme
        if response.status_code == 200:
            print("İstek başarıyla gönderildi! ✅")
            # Yanıt içeriğini JSON olarak yazdıralım
            # print("Yanıt:", response.json())
        else:
            print(f"İstek başarısız oldu. Durum Kodu: {response.status_code} ❌")
            # print("Yanıt:", response.text)

    except requests.exceptions.RequestException as e:
        log.warning(f"Bir hata oluştu: {e}")



def parse_positions(json_data):
    """
    Gelen JSON verisindeki pozisyon bilgilerini ayrıştırır ve yazdırır.

    Args:
        json_data (str): JSON formatındaki pozisyon verisi.

    """
    global position_main_list
    position_main_list=[]
    
    try:
        # JSON string'ini Python sözlüğüne dönüştür
        data = json.loads(json_data)

        # "data" anahtarının altında bir liste olup olmadığını kontrol et
        if "data" in data and isinstance(data["data"], list):
            positions = data["data"]
            
            # Her bir pozisyonu döngü ile gez
            for i, position in enumerate(positions):
                position_list=[]
                # print(f"--- Pozisyon #{i+1} için Veriler ---")
                
                # Her bir değişkeni yazdır
                # print(f"Pozisyon ID: {position.get('positionId')}")
                # print(f"Cüzdan: {position.get('subWallet')}")
                # print(f"Sembol: {position.get('symbol')}")
                # print(f"Mevcut Pozisyon: {position.get('currentPosition')}")
                # print(f"Kullanılabilir Pozisyon: {position.get('availPosition')}")
                # print(f"Maliyet Fiyatı: {position.get('avgCostPrice')}")
                # print(f"İşaret Fiyatı (Mark Price): {position.get('markPrice')}")
                # print(f"Gerçekleşmiş K/Z: {position.get('realizedPnl')}")
                # print(f"Likidasyon Fiyatı: {position.get('liquidationPrice')}")
                # print(f"Marjin: {position.get('margin')}")
                # print(f"Yön (Side): {position.get('side')}")  # 1: Long, 2: Short
                # print(f"Kaldıraç (Leverage): {position.get('leverage')}")
                # print(f"Pozisyon Tipi: {position.get('positionType')}")
                # print(f"Kapanış Durumu: {position.get('isClose')}")
                # print(f"Kapanış Emir ID: {position.get('closeOrderId')}")
                # print(f"Kapanış Emir Fiyatı: {position.get('closeOrderPrice')}")
                # print(f"Kapanış Emir Hacmi: {position.get('closeOrderVolume')}")
                # print(f"Taban Hassasiyet: {position.get('basePrecision')}")
                # print(f"Gösterim Hassasiyeti: {position.get('baseShowPrecision')}")
                # print(f"Emirler: {position.get('orders')}")
                # print(f"Marjin Tipi: {position.get('marginType')}")
                # print(f"Maksimum Ek Marjin: {position.get('maxAddMargin')}")
                # print(f"Maksimum Çıkarılabilir Marjin: {position.get('maxSubMargin')}")
                # print(f"Minimum Marjin Oranı (MMR): {position.get('mmr')}")
                # print(f"Risk Oranı (r): {position.get('r')}")
                # print(f"Hesap Bakiye (accb): {position.get('accb')}")
                # print(f"Donmuş (Frozen): {position.get('frozen')}")
                # print(f"Bakım Marjini (mm): {position.get('mm')}")
                # print(f"Otomatik Marjin Ekleme: {position.get('autoAddMargin')}")
                # print(f"Callback Değeri: {position.get('callbackValue')}")
                # print(f"Planlanan Emir Büyüklüğü: {position.get('planOrderSize')}")
              

                # print("Pnl: ",position.get('realizedPnl'))
                position_list.append(position.get('positionId'))
                position_list.append(position.get('symbol'))
                position_list.append(position.get('avgCostPrice'))
                #position_list.append(position.get('positionId'))
                position_main_list.append(position_list)
        else:
            print("JSON verisinde 'data' anahtarı veya liste formatı bulunamadı.")
        
        # print("position main list",position_main_list)
        position_main_list2=position_main_list
        #return position_main_list 

    except json.JSONDecodeError as e:
        log.warning(f"JSON verisi çözülürken hata oluştu: {e}")


def parse_orders(json_data):
    """
    Gelen JSON verisindeki sipariş bilgilerini ayrıştırır ve yazdırır.

    Args:
        json_data (str): JSON formatındaki sipariş verisi.

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
        # check_id(order_main_list)
    except json.JSONDecodeError as e:
        log.warning(f"Failed to decode JSON: {e}")
# Chrome options# Selenium'un thread-safe olması için lock nesnesi
driver_lock = threading.Lock()

req=None

from fastapi import FastAPI, HTTPException, Query
import db
from functools import wraps

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

        #print("Çözülmüş yanıt:\n", decompressed)
        response_text = decompressed  # response

        # 1.Extract JSON from callback brackets
        match = re.search(r'\((\{.*\})\)', response_text, re.S)
        if match:
            json_str = match.group(1)
            data = json.loads(json_str)

            # 2. Payload değerini al
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
    try:
                                                #/html/body/div[4]/div[1]/div[1]/div[2]/div/div/div[2]
        element = driver.find_element(By.XPATH, '/html/body/div[4]/div[1]/div[1]/div[2]/div/div/div[2]')

        # JavaScript ile class'ı kaldır
        driver.execute_script("""
        arguments[0].classList.remove('geetest_disable');
        """, element)
        # time.sleep(1)
        submit_button = driver.find_element(By.XPATH, '/html/body/div[4]/div[1]/div[1]/div[2]/div/div/div[2]')  # login butonun xpath'i
        submit_button.click()
        # time.sleep(1)

        #print(checkmail())

        
        # find passport input
        # mail_code = wait.until(EC.presence_of_element_located((
        #     By.XPATH,
        #     '/html/body/div[4]/div/div[2]/div/div[2]/div[2]/div/div/div/div/div/input'
        # )))#
        # mail_code.clear()
        # try:
        #     i=0
        #     for i in range(10):
        #         x=checkmail()
        #         time.sleep(15)
        #         if x!= "":
        #             break
        #         i+=1
        
        # except:
        #     print("code not found")
        # mail_code.send_keys(x)

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
    # düşük fiyattan sipariş 2.7905
    # yüksek fiyattan satış verilecek  2.9005
    #fiyat 2.8105
    
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
            log.warning(f"get payload second error {e}")
        
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
            #  #levarege sisemine bağlanıcak
            market_func.getpayload(payload2)
            
            # #print("payload:",payload)
        except Exception as e:
            log.warning("%s payload test sending failed: %s",  e)            
        