
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import time,db,asyncio,json,requests
from selenium.webdriver.common.keys import Keys # Import the Keys module
from datetime import datetime

from bot import open_browser
from backend import swap_open_close_values_From_websocket,signaler_req




flag=0
trade_list=[]

# log = logging.getLogger(__name__)
# from backend import market_func
#  #levarege sisemine bağlanıcak
# market_func.getpayload(payload)
# #print("payload:",payload)
pair_list=[]

is_running = False  # global flag

# async def turn():
#     global is_running
#     if is_running:
#         # Önceki işlem devam ediyorsa yeni döngü başlamasın
#         return  

#     is_running = True
#     try:
#         r = await signaler_req.get_debug_webhooks(clear=True)  # debug endpointten çek
#         classified_events = signaler_req.filter_open_events(r)

#         if not classified_events:
#             return None

#         for evt in classified_events:
#             # payload işleme
#             getpayload(evt)

#     finally:
#         is_running = False  # işlem bittiğinde tekrar çalışmaya hazır hale getir

# async def scheduler():
#     while True:
#         await turn()              # turn fonksiyonunu çağır
#         await asyncio.sleep(30)   # 30 saniye bekle


def getpayload(payload):
    
    json_data=payload

    # Verileri çekme
    identifier = json_data['identifier']
    kind = json_data['kind']
    recalc = json_data['Recalc']

    # 'chart' verilerini çekme
    chart_url = json_data['chart']['url']
    chart_interval = json_data['chart']['interval']

    # 'trade' verilerini çekme
    trade_id = json_data['trade']['id']
    trade_entry_type = json_data['trade']['entry_type']
    trade_entry_signal = json_data['trade']['entry_signal']
    trade_entry_price = json_data['trade']['entry_price']
    trade_entry_time = json_data['trade']['entry_time']
    trade_position = json_data['trade']['position']

    # 'raw' verilerini çekme
    raw_num = json_data['raw']['num']
    raw_signal = json_data['raw']['signal']
    raw_type = json_data['raw']['type']
    raw_open_time = json_data['raw']['open_time']
    raw_close_time = json_data['raw']['close_time']
    raw_open_price = json_data['raw']['open_price']
    raw_close_price = json_data['raw']['close_price']
    raw_position_size = json_data['raw']['position_size']
    #print("open price:",raw_open_price)
    """
    {'identifier': 'JSAqsyMo', 'kind': 'close', 'Recalc': False, 'chart': {'url': 'https://www.tradingview.com/chart/JSAqsyMo/', 'interval': '1m'},
      'trade': {'id': '2177', 'entry_type': 'Entry', 'entry_signal': 'Strong Sell, Strong Buy', 'entry_price': 1.2638, 'entry_time': 'Aug 27, 2025, 14:48', 'exit_price': 1.2638, 'exit_time': 'Aug 27, 2025, 14:50', 'exit_signal': 'Strong Buy', 'position': '289.98, 365.75 usdt'},
      'raw': {'num': '2177', 'signal': 'Strong Sell, Strong Buy', 'type': 
    'Entry', 'open_time': 'Aug 27, 2025, 14:48', 'close_time': 'Aug 27, 2025, 14:50', 'open_price': '1.2638', 'close_price': '1.2638', 'position_size': '289.98, 365.75 usdt'}}

    """

    """ db connection and save trade signal"""
    
    trade = {
        "id": trade_id,
        "entry_type": trade_entry_type,
        "entry_signal": trade_entry_signal,
        "entry_price": trade_entry_price,
        "entry_time": trade_entry_time,
        "exit_price": raw_close_price,
        "exit_time": raw_close_time,
        "exit_signal": trade_entry_type,
        "raw_json": json_data
    }
  


    # try:
    #     DSN = "host=localhost port=5432 dbname=nextlayer user=nl_user password=nlpass"

    #     UPSERT_SQL = """
    #     INSERT INTO trades
    #     (tradeid, identifier, opened_at, closed_at, type, signal, open_price, close_price, position)
    #     VALUES (%(tradeid)s, %(identifier)s, %(opened_at)s, %(closed_at)s, %(type)s, %(signal)s, %(open_price)s, %(close_price)s, %(position)s)
    #     ON CONFLICT (tradeid) 
    #     DO UPDATE SET
    #         closed_at    = EXCLUDED.closed_at,
    #         type         = EXCLUDED.type,
    #         signal       = EXCLUDED.signal,
    #         close_price  = EXCLUDED.close_price,
    #         position     = EXCLUDED.position;
    #     """

    #     def upsert_trade(trade: dict):
    #         """trades tablosuna kayıt ekler veya varsa günceller"""
    #         with psycopg2.connect(DSN) as conn, conn.cursor() as cur:
    #             cur.execute(UPSERT_SQL, trade)
    #             conn.commit()
    #         print("Trade added in db ✅")

    #     trade_data = {
    #         "tradeid": trade_id,
    #         "identifier": "BTCUSDT2",
    #         "opened_at": datetime(2025, 9, 10, 12, 0),
    #         "closed_at": None,
    #         "type": "long",
    #         "signal": "buy",
    #         "open_price": raw_open_price,
    #         "close_price": None,
    #         "position": 1.0,
    #     }
    #     upsert_trade(trade_data)
        
    # except json.JSONDecodeError as e:
    #     print(" insert trade db error: %s",e)


    # try:
    #     with db.connect() as conn, conn.cursor() as cur:
    #         rows = db.fetch_all_trades(cur,limit=2000)
    #         #print({"identifier": identifier, "count": len(rows), "rows": rows})
            

    # except:
    #     print(" fetch all trades  db error: ")

    signal_parts = raw_signal.split(',')
    first_part_of_signal = signal_parts[0].strip()

    first_par_posiiton_size = raw_position_size.split(',')[0]

    # Float’a çevirmek istersen
    first_par_posiiton_size = float(first_par_posiiton_size)

    if first_part_of_signal=="Strong Sell":
        signal="Sell"

    if first_part_of_signal=="Strong Buy":
       signal="Buy"
    try:
        new_signal = {
        "tradeid": trade_id,
        "identifier": identifier,
        "opened_at": datetime.utcnow(),
        "closed_at": None,
        "type": first_part_of_signal,
        "signal": signal,
        "open_price": raw_open_price,
        "close_price": None,
        "position": first_par_posiiton_size
        }
        db.insert_signal(new_signal)

    except:
        print(" insert signals  db error: ")


        

    target_pair = identifier  # currency_pair== signaler identifier

    try:
        limit: int = 100
        with db.connect() as conn:
            with conn.cursor() as cur:
                configurations = db.fetch_all_configurations(cur, limit)
                # Eşleşenleri filtrele
                matched = [conf for conf in configurations if conf.get("currency_pair") == target_pair]

        # print("matched:",matched)  # matched listesinde sadece istediğin currency_pair olan satırlar var

    except Exception as e:
        print("Catch configurations db error: %s", e)

    config = matched[0]

    #  variables
    runner_id = config['runner_id']
    tv_username = config['tv_username']
    tv_password = config['tv_password']
    executor = config['executor']
    exchange = config['exchange']
    starting_balance = config['starting_balance']
    margin_type = config['margin_type']
    leverage = config['leverage']
    currency_pair = config['currency_pair']
    order_type = config['order_type']
    base_point = config['base_point']
    divide_equity = config['divide_equity']
    trade_entry_time = config['trade_entry_time']
    trade_exit_time = config['trade_exit_time']
    trade_pnl = config['trade_pnl']
    tr=config['transaction_ratio']

    # all_trad = db.fetch_trade_backup()  # fetch_trade_backup() bir tuple döndürüyor, [0] ile alıyoruz
    result = db.fetch_trade_backup()  # tuple dönüyor
    all_trades = result          # tuple içindeki listeyi alıyoruz

    # print(all_trades)
    # # Örnek: runner_id=1 ve identifier='BTCUSDT' olan kayıt
    # runner_id = runner_id
    identifier = identifier

    filtered = [t for t in all_trades if t["runner_id"] == runner_id and t["identifier"] == identifier]
    
    print("filtered:",filtered)
    #Qty=float

    qty=None
    list_of_trade=[]
    """
    list or trade = 
    
    
    
    """
    print("order type",order_type)
    if order_type=="Limit":#limit== type=1
        list_of_trade=["",{"symbol":"-susdt","orderQty":0,"future":0,"price":"","side":1,"type":"1","source":1}]
        list_of_trade[1]["type"]="1"
        list_of_trade[1]["price"]=str(raw_open_price)# add raw_open_price
    if order_type=="Market":# market== type=2
        list_of_trade=["",{"symbol":"sxrp-susdt","orderQty":11,"side":2,"type":"2","source":1}]
        list_of_trade[1]["type"]="2"
    print("margin_type",margin_type)
    if margin_type=="cross":
        list_of_trade[0]="c"
    
    if margin_type=="isolated":
        list_of_trade[0]="i"

    
    if first_part_of_signal=="Strong Buy":#side=1 long
        list_of_trade[1]["side"]=1
    
    if first_part_of_signal=="Strong Sell":#side=2 short
        list_of_trade[1]["side"]=2
    
    list_of_trade[1]["symbol"]=currency_pair+"-susdt"# add currency_pair
    #["",{"symbol":"-susdt","orderQty":0,"future":0,"price":"","side":1,"type":"1","source":1}]
    
    list_of_trade.append(leverage)# add leverage
    #["",{"symbol":"-susdt","orderQty":0,"future":0,"price":"","side":1,"type":"1","source":1},lvx]

    
    #     type   side 
    #cross,limit,buy,43x,SSOL,203000,203000/500
    #cross manuel
    #["c",{"symbol":"sxrp-susdt","orderQty":123,"future":0,"price":"2.9885","side":1,"type":"1","source":1}]
    #{"symbol":"sxrp-susdt","orderQty":123,"future":0,"price":"2.9885","side":1,"type":"1","source":1}

    ["c",{"symbol":"sxrp-susdt","orderQty":11, "side":2,  "type":"2","source":1},10]
    ["c",{"symbol":"-susdt",    "orderQty":0,  "future":0,"price":"","side":1,"type":"1","source":1},10]

    if first_part_of_signal=="Strong Sell":
        try:
            #buysellLimit(pair,margin,last_price,levaregeX,raw_open_price,number_as_float,BY,TPSL,TP,SL)
            # satınalma işlemi tamamlandıktan sonra güncelleme yapıalcak
            
            if len(filtered)==0:
                trade_data = {
                "runner_id": runner_id,
                "identifier": identifier,
                "first_balance": float(starting_balance),#800
                "now_balance": float(starting_balance-starting_balance*tr),
                "buyed_or_selled_coin_qty":float(-starting_balance*tr/float(raw_open_price)),
                "trade_count": 1,
                 "trade_id":trade_id,
                 "order_id":""
            }
                qty=starting_balance*tr/float(raw_open_price)#qty to next trade

                list_of_trade[1]["orderQty"]=str(qty)
                list_of_trade.append(1)
                list_of_trade.append(identifier)
                list_of_trade.append(runner_id)
                # ["c",{"symbol":"-susdt","orderQty":0,"future":0,"price":"","side":1,"type":"1","source":1},lvx,1,identifier,runner_id]

                db.upsert_trade_backup(trade_data)
                print("file didint found in db and added")
            else:
                for data in filtered:
                    if data["trade_count"]:
                        trade_data = {
                        "runner_id": runner_id,
                        "identifier": identifier,
                        "first_balance": float(starting_balance),#800
                        
                        "now_balance": float(data["now_balance"]-data["now_balance"]*tr),
                        "buyed_or_selled_coin_qty":float(data["buyed_or_selled_coin_qty"]-data["now_balance"]*tr/float(raw_open_price)),
                        "trade_count": data["trade_count"]+1,
                        "trade_id":trade_id,
                        "order_id":""
                    }
                        
                        qty=starting_balance*tr/float(raw_open_price)#qty to next trade
                        
                        list_of_trade[1]["orderQty"]=str(qty)
                        list_of_trade.append(data["trade_count"]+1)
                        list_of_trade.append(identifier)
                        list_of_trade.append(runner_id)
                        # ["c",{"symbol":"-susdt","orderQty":0,"future":0,"price":"","side":1,"type":"1","source":1},lvx,1,identifier,runner_id]
                        db.upsert_trade_backup(trade_data)
                        print("file  found in db ")


            
            



            
            
            # print("sell ",record_list[6],record_list[7],"0",record_list[5],raw_open_price,1,"SELL",0,0,0)
            
            buysellLimit(list_of_trade)
        except Exception as e:
            print("sell function error: %s", e)


    if first_part_of_signal=="Strong Buy":
        try:#                   Limit      10           0   sxrp-susdt      2.9060        10 BUY 0 0 0
            
            if  len(filtered)==0:
                
                trade_data = {
                "runner_id": runner_id,
                "identifier": identifier,
                "first_balance": float(starting_balance),#800
                "now_balance": float(starting_balance-starting_balance*tr),
                "buyed_or_selled_coin_qty":float(+starting_balance*tr/float(raw_open_price)),
                "trade_count": 1,
                "trade_id":trade_id,
                 "order_id":""
            }
                qty=float(starting_balance)*float(tr)/float(raw_open_price)#qty to next trade

                list_of_trade[1]["orderQty"]=str(qty)
                list_of_trade.append(1)
                list_of_trade.append(identifier)
                list_of_trade.append(runner_id)
                db.upsert_trade_backup(trade_data)
                print("file didint found in db and added")
            else:
                print(2)
                for data in filtered:
                    if data["trade_count"]:
                        trade_data = {
                        "runner_id": runner_id,
                        "identifier": identifier,
                        "first_balance": float(starting_balance),#800
                        "buyed_or_selled_coin_qty":float(data["buyed_or_selled_coin_qty"]+data["now_balance"]*tr/float(raw_open_price)),
                        "now_balance": float(data["now_balance"]-data["now_balance"]*tr),
                        
                        "trade_count": data["trade_count"]+1,
                        "trade_id":trade_id,
                        "order_id":""
                    }
                        qty=starting_balance*tr/float(raw_open_price)#qty to next trade

                        list_of_trade[1]["orderQty"]=str(qty)
                        list_of_trade.append(data["trade_count"]+1)
                        list_of_trade.append(identifier)
                        list_of_trade.append(runner_id)

                        db.upsert_trade_backup(trade_data)
                        print("file  found in db")

           
            

            


            #
            # print("buy ",record_list[6],record_list[7],"0",record_list[5],raw_open_price,10,"BUY",0,0,0)
            buysellLimit(list_of_trade)
        except Exception as e:
            print("buy  function error: %s", e)
     

""" open broserin sonuna iki durum içinde çalıaşcak bi sistem hazırla 1. cross 2. si isolated"""

#last_price is marketing type , market or limit
def buysellLimit(list_of_trade):
    margin_type=list_of_trade[0]
    lvx=list_of_trade[-4]
    trade_count=list_of_trade[-3]

    indentifer=list_of_trade[-2]
    runner_id=list_of_trade[-1]

    
  

    print(margin_type,lvx,trade_count,indentifer,runner_id)

    fetchet_list=db.fetch_trade_backup_by_runner_and_identifier(runner_id,indentifer)
    # print("fetched list:",fetchet_list)

    first_config_list=[]
    
    try:
        limit: int = 100
        with db.connect() as conn:
            with conn.cursor() as cur:
                configurations = db.fetch_all_configurations(cur, limit)
                
                
                # for i in range(len(configurations)):
                #     
        i=0    
        print(len(configurations))
        for i in range(len(configurations)):
            a=[]
            a.append(configurations[i]["runner_id"])#0
            a.append(configurations[i]["currency_pair"])#1
            a.append(configurations[i]["margin_type"])#2
            a.append(configurations[i]["leverage"])#3
            a.append(configurations[i]["order_type"])#4
            a.append(configurations[i]["trade_entry_time"])#5
            a.append(configurations[i]["trade_exit_time"])#6
            a.append(configurations[i]["trade_pnl"])#7

            first_config_list.append(a)

        # print("matched:",matched)  # matched listesinde sadece istediğin currency_pair olan satırlar var
        print("fcl ",first_config_list)
    except Exception as e:
        print("Catch configurations db error: %s", e)


    # all_fetch_list=db.fetch_trade_backup()
    # for i in all_fetch_list:

    # print("all fetch:",all_fetch_list)
    # first_ballance=fetchet_list[2]
    # now_ballance=fetchet_list[3]
    # buyyed_selled_qty=fetchet_list[4]
    trade_count=fetchet_list[0]["trade_count"]
    # print("tct",fetchet_list)
    # print("tlst",trade_list)
    global flag
    driver = open_browser.driver
    #print("trade list:",trade_list)
    
    if len(trade_list)==0:
        # print("tlst",trade_list)
        for i in first_config_list:
            a=[]
            if i[4]=="Limit":#limit== type=1

                a.append("l")
                
            if i[4]=="Market":# market== type=2

                
                a.append("m")

            print("margin_type",margin_type)

            if i[2]=="cross":

                a.append("c")
            
            if i[2]=="isolated":

                a.append("i")

            a.append(i[3])
            a.append(i[1])
            trade_list.append(a)

            b=0
            print(trade_list)
            for i in trade_list:
                first_configuration(i[3],i[1],i[2])
    print("tl",trade_list)

    if len(trade_list)!=0:

        # değilse trade_list i kontrol edip iligli symbol için işlemelr gerçkleştir.
        margin_type=list_of_trade[0]
        lvx=list_of_trade[-4]
        trade_count=list_of_trade[-3]

        indentifer=list_of_trade[-2]
        runner_id=list_of_trade[-1]

        for i in trade_list:
            if indentifer==i[1]:
                pair_index=trade_list.index(i)
                pair=indentifer+"susdt"
                
                window_handles = driver.window_handles
                    
                
                
                # 3. Use the index to get the correct window handle from the list
                target_handle = window_handles[pair_index+1]
                
                # 4. Switch to the tab using the correct handle
                driver.switch_to.window(target_handle)
                
                print("Switched to pair:", pair, "on tab index:", pair_index+1)
        # time.sleep(10)
        wait = WebDriverWait(driver, 15)
        try:

            ["c",{"symbol":"-susdt","orderQty":0,"future":0,"price":"","side":1,"type":"1","source":1},lvx,1,identifier,runner_id]
            
            if list_of_trade[1]["type"]==1:
                
                """ click last price"""
                try:
                    i=0
                    #swap-layout-desktop > div.jsx-1790752364.swap-layout-content > div.jsx-1790752364.swap-layout-right > div.jsx-1790752364.trade-view.bg.card-radius > div:nth-child(4) > div.swap-guide-step-3.trade-view-input-wrap > div.jsx-1147981079.input-view > div:nth-child(1) > div > div.jsx-1147981079.newest
                    for i in range(3):
                        clickGETLASTPRICE = wait.until(EC.element_to_be_clickable((By.XPATH,"//div[text()='Last']")))
                        clickGETLASTPRICE.click()
                        time.sleep(0.1)
                        i+=1


                    # #get last price
                    # time.sleep(1)
                    input_selector = 'input[aria-label="Price"]'
                    #wait = WebDriverWait(driver, 10)
                    
                    input_element = wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, input_selector))
                    )

                    # # `value` niteliğindeki mevcut değeri al
                    mevcut_deger_str = input_element.get_attribute("value")
                    print("price ",mevcut_deger_str)
                except:
                    print("didnt clicked last price")
            
                
                
                    # #write raw_open_price to buy or sell like price (trade_price)/price = 1000/114700=0.0087183958
                    # PRELcount = wait.until(
                    #     EC.presence_of_element_located((By.CSS_SELECTOR, 'input[aria-label="Price"]'))#//*[@id="swap-layout-desktop"]/div[3]/div[2]/div[1]/div[4]/div[1]/div[1]/div[1]/input
                    # )                                                                                  
                    # PRELcount.send_keys(Keys.BACKSPACE)
                    # PRELcount.send_keys(Keys.BACKSPACE)
                    # PRELcount.send_keys(Keys.BACKSPACE)
                    # PRELcount.send_keys(Keys.BACKSPACE)
                    # PRELcount.send_keys(Keys.BACKSPACE)
                    # PRELcount.send_keys(Keys.BACKSPACE)
                    # PRELcount.send_keys(Keys.BACKSPACE)
                    # PRELcount.send_keys(Keys.BACKSPACE)
                    # #print("price writeded",raw_open_price)
                    # time.sleep(0.1)
                    # # 6. Belirlenen değeri yaz
                    # PRELcount.send_keys("123")# gönderilen para satın alıncaka ürün değeri kadardır.
                    # #print(type(raw_open_price))
                """ add qty"""
                try:
                    
                    QTY = wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'input[aria-label="Qty"]'))#
                    )                                                                                  
                    QTY.send_keys(Keys.BACKSPACE)
                    QTY.send_keys(Keys.BACKSPACE)
                    QTY.send_keys(Keys.BACKSPACE)
                    QTY.send_keys(Keys.BACKSPACE)
                    QTY.send_keys(Keys.BACKSPACE)
                    QTY.send_keys(Keys.BACKSPACE)
                    QTY.send_keys(Keys.BACKSPACE)
                    QTY.send_keys(Keys.BACKSPACE)
                    time.sleep(0.1)
                    #print("price writeded",number_as_float)
                    # 6. Belirlenen değeri yaz
                    QTY.send_keys(1.23)

                except json.JSONDecodeError as e:
                    print(f"didnt writeded Qty value {e}")
                
        except Exception as e:
            print(f"limit marketing error {e}", )
        

        try:

            ["c",{"symbol":"-susdt","orderQty":0,"future":0,"price":"","side":1,"type":"1","source":1},lvx,1,identifier,runner_id]
            
            if list_of_trade[1]["type"]==2:
                
                """ dont click last price"""
                # try:
                #     i=0
                #     #swap-layout-desktop > div.jsx-1790752364.swap-layout-content > div.jsx-1790752364.swap-layout-right > div.jsx-1790752364.trade-view.bg.card-radius > div:nth-child(4) > div.swap-guide-step-3.trade-view-input-wrap > div.jsx-1147981079.input-view > div:nth-child(1) > div > div.jsx-1147981079.newest
                #     for i in range(3):
                #         clickGETLASTPRICE = wait.until(EC.element_to_be_clickable((By.XPATH,"//div[text()='Last']")))
                #         clickGETLASTPRICE.click()
                #         time.sleep(0.1)
                #         i+=1


                #     # #get last price
                #     # time.sleep(1)
                #     input_selector = 'input[aria-label="Price"]'
                #     #wait = WebDriverWait(driver, 10)
                    
                #     input_element = wait.until(
                #         EC.presence_of_element_located((By.CSS_SELECTOR, input_selector))
                #     )

                #     # # `value` niteliğindeki mevcut değeri al
                #     mevcut_deger_str = input_element.get_attribute("value")
                #     print("price ",mevcut_deger_str)
                # except:
                #     print("didnt clicked last price")
            
                
                
                    # #write raw_open_price to buy or sell like price (trade_price)/price = 1000/114700=0.0087183958
                    # PRELcount = wait.until(
                    #     EC.presence_of_element_located((By.CSS_SELECTOR, 'input[aria-label="Price"]'))#//*[@id="swap-layout-desktop"]/div[3]/div[2]/div[1]/div[4]/div[1]/div[1]/div[1]/input
                    # )                                                                                  
                    # PRELcount.send_keys(Keys.BACKSPACE)
                    # PRELcount.send_keys(Keys.BACKSPACE)
                    # PRELcount.send_keys(Keys.BACKSPACE)
                    # PRELcount.send_keys(Keys.BACKSPACE)
                    # PRELcount.send_keys(Keys.BACKSPACE)
                    # PRELcount.send_keys(Keys.BACKSPACE)
                    # PRELcount.send_keys(Keys.BACKSPACE)
                    # PRELcount.send_keys(Keys.BACKSPACE)
                    # #print("price writeded",raw_open_price)
                    # time.sleep(0.1)
                    # # 6. Belirlenen değeri yaz
                    # PRELcount.send_keys("123")# gönderilen para satın alıncaka ürün değeri kadardır.
                    # #print(type(raw_open_price))
                """ add qty"""
                try:
                    
                    QTY = wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'input[aria-label="Qty"]'))#
                    )                                                                                  
                    QTY.send_keys(Keys.BACKSPACE)
                    QTY.send_keys(Keys.BACKSPACE)
                    QTY.send_keys(Keys.BACKSPACE)
                    QTY.send_keys(Keys.BACKSPACE)
                    QTY.send_keys(Keys.BACKSPACE)
                    QTY.send_keys(Keys.BACKSPACE)
                    QTY.send_keys(Keys.BACKSPACE)
                    QTY.send_keys(Keys.BACKSPACE)
                    time.sleep(0.1)
                    #print("price writeded",number_as_float)
                    # 6. Belirlenen değeri yaz
                    QTY.send_keys(1.23)

                except json.JSONDecodeError as e:
                    print(f"didnt writeded Qty value {e}")
                
        except Exception as e:
            print(f"limit marketing error {e}", )


    """ click buy or sell"""
    try:
        # click buy or sell
        # if(BY=="BUY"):
        clickBUY = wait.until(EC.element_to_be_clickable((By.ID,'btn_buy')))
        clickBUY.click()
            #open_browser.new_body_bytes_open_order={"symbol":"sxrp-susdt","orderQty":1000,"future":0,"price":"3.45","side":1,"type":"1","source":1}
            #print("buy clicked")
        
        # if(BY=="SELL"):
        #     clickSELL = wait.until(EC.element_to_be_clickable((By.ID,'btn_sell')))
        #     clickSELL.click()
        #     #open_browser.new_body_bytes_open_order={"symbol":"sxrp-susdt","orderQty":200,"future":0,"price":"3.7","side":2,"type":"1","source":1}
        #     #print("sell clicked")
    except json.JSONDecodeError as e:
        print(f"didnt clicked buy or sell button {e}")
    time.sleep(1)


    """ buy or sell comfrm"""
    try:
        
        clickCONFIRM = wait.until(EC.element_to_be_clickable((By.XPATH,"//div[text()='Confirm']")))
        clickCONFIRM.click()

        
    except Exception as e:
        print("didnt clicked confirm: %s", e)
        
        
    """ check comfigure orders price"""
    # try:
        
    #     market_reaction()

    # except Exception as e:
    #     print("starting market_reaction error: %s", e)
        

    


def first_configuration(pair,margin,levaregeX,):
    
    pair=pair+"susdt"
    driver = open_browser.driver
    driver.execute_script("window.open('');")
    all_tabs = driver.window_handles
    driver.switch_to.window(all_tabs[-1])
    driver.get(f"https://www.bydfi.com/en/swap/demo?id={pair}")#bu sekme açık işllemelrin kontrol edileceği 1 sekme olacak 0. indexte
    wait = WebDriverWait(driver, 15)


    
        
       
    try:

        #click x button 
        clickX = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'.trade-toolbar-wrap .swap-guide-step-2 > div > div')))
        clickX.click()
    except json.JSONDecodeError as e:
        print(f"didnt clicked X button {e}")

    try:
        # #select cross or isolated
        if(margin=="c"):
            clickCROSS = wait.until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[9]/div/div[2]/div/div[2]/div[1]/div/div/div[2]/div[1]/div[1]/div[1]')))
               
            #clickCROSS = wait.until(EC.element_to_be_clickable((By.XPATH,"//div[text()='Cross']")))
            clickCROSS.click()
        
        if(margin=="i"):
            # clickisolated = wait.until(EC.element_to_be_clickable((By.XPATH,'./html/body/div[8]/div/div[2]/div/div[2]/div[1]/div/div/div[2]/div[1]/div[1]/div[2]')))
            # clickisolated.click()
            clickisolated = wait.until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[9]/div/div[2]/div/div[2]/div[1]/div/div/div[2]/div[1]/div[1]/div[2]')))
               
            #clickisolated = wait.until(EC.element_to_be_clickable((By.XPATH,"//div[text()='Isolated']")))
            clickisolated.click()
        #"body > div:nth-child(12) > div > div.ant-modal-wrap.ant-modal-centered > div > div.ant-modal-content > div.ant-modal-body > div > div > div.jsx-3434185282.swap-common-modal-content-component.hide-scroll-bar > div.jsx-1884500109.margin-type-modal > div.jsx-1884500109.buttons > div.jsx-1884500109.active"
    except json.JSONDecodeError as e:
        print(f"didnt clicked cross or isolated {e}")


    # #write X size    
    # time.sleep(0)
    try:
        LVX = wait.until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div/div[2]/div/div[2]/div[1]/div/div/div[2]/div[3]/div/div[1]/input'))#jsx-2185320666 components-numeric-input focus-active text-center full-width jsx-1225381481 trade-view-input dark jsx-2208463890 input
        )        
        time.sleep(0.1)                                                                          #jsx-2185320666
        LVX.send_keys(Keys.BACKSPACE)
        time.sleep(0.1)  
        LVX.send_keys(Keys.BACKSPACE)
        time.sleep(0.1)  
        LVX.send_keys(Keys.BACKSPACE)
        # 6. Belirlenen değeri yaz
        time.sleep(0.1)  
        #print("sendet")
        LVX.send_keys(levaregeX)

        clickCONFRM = wait.until(EC.element_to_be_clickable((By.XPATH,"//div[text()='Confirm']")))
        clickCONFRM.click()#jsx-3418843714 trade-base-button jsx-3434185282 confirm
    except json.JSONDecodeError as e:
        print(f"didnt sended x value or clicked confirm button {e}")
    
    
    try:

        #click x button 
        clickmarket = wait.until(EC.element_to_be_clickable((By.XPATH,'//*[@id="swap-layout-desktop"]/div[3]/div[2]/div[1]/div[2]/div[1]/div[2]')))
        clickmarket.click()
    except json.JSONDecodeError as e:
        print(f"didnt clicked Market button {e}")
    
    



def market_reaction():
    """ check orders price function"""
    driver = open_browser.driver

    all_tabs = driver.window_handles
    driver.switch_to.window(all_tabs[1])
    #driver.get(f"https://www.bydfi.com/en/swap/demo?id=ssol-susdt")
    wait = WebDriverWait(driver, 5)
    try:

        """ click order menu beign"""
        # try:
        #     click_open_orders_menu1 = wait.until(
        #                 EC.element_to_be_clickable((By.XPATH, '//*[@id="swap-layout-desktop"]/div[2]/div[1]/div[2]/div/div[1]/div/div[2]'))
        #     )                                                                              
        #     # 6. Belirlenen değeri yaz
        #     click_open_orders_menu1.click()  
        # #EC.element_to_be_clickable((By.XPATH,"//div[text()='Cross']"))
        # except Exception as e:
        #     print("didnt getted prices1") 
        try:
            click_open_orders_menu2 = wait.until(
                EC.element_to_be_clickable((By.XPATH,'//*[@id="swap-layout-desktop"]/div[3]/div[1]/div[2]/div/div[1]/div[1]/div[2]'))
            )                                                                              
            # 6. Belirlenen değeri yaz
            click_open_orders_menu2.click()

            # print("clicked open orders menu") 
        except Exception as e:
            print("didnt clicked open orders menu") 

        time.sleep(3)
        # try:
        #     #print("flag= ",flag)       #                                //*[@id="swap-layout-desktop"]/div[3]/div[1]/div[2]/div/div[3]/div/div[2]/div/div/div/div/div[2]/table/tbody/tr[2]/td[6]/div/span                                                 
        #     # 1. Elementi bul
        #     element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="swap-layout-desktop"]/div[3]/div[1]/div[2]/div/div[3]/div/div[2]/div/div/div/div/div[2]/table/tbody/tr[2]/td[6]/div/span')))
            
        #     # 2. Elementi görüntü alanına getirmek için JavaScript kullan
        #     driver.execute_script("arguments[0].scrollIntoView(true);", element)
            
        #     # 3. Elementin tıklanabilir olduğundan emin olmak için tekrar bekle
        #     wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="swap-layout-desktop"]/div[3]/div[1]/div[2]/div/div[3]/div/div[2]/div/div/div/div/div[2]/table/tbody/tr[2]/td[6]/div/span')))
            
        #     # 4. Tıklama işlemini gerçekleştir
        #     element.click()
        #     time.sleep(1)
        # except:
        #     print("click error1")

        # try:
        #     # 2. Input alanının XPath'ini tanımla
        #     input_xpath = '//div[contains(@class, "trade-view-input")]/input'
            
        #     # 3. Elementin DOM'da var olmasını bekle (tıklanabilir olması zorunlu değil)
        #     price_input = wait.until(EC.presence_of_element_located((By.XPATH, input_xpath)))
            
        #     # 4. JavaScript kullanarak değeri doğrudan gir
        #     price_to_enter = "2.7585"
        #     driver.execute_script(f"arguments[0].value = '{price_to_enter}';", price_input)
        #     print(f"Fiyat JavaScript ile başarıyla girildi: {price_to_enter}")
            
        # except Exception as e:
        #     print(f"sending error: {e}")
        # try:
            
        # except:
        #     print("didnt sendet edit order api")




        # try:
        #     # 4. Onay butonuna tıkla
        #     time.sleep(1)
        
        #     check_button_xpath = "//span[@aria-label='check']"
        #     check_button = wait.until(EC.element_to_be_clickable((By.XPATH, check_button_xpath)))
        #     check_button.click()
        #     print("Onay butonuna tıklandı.")

        # except Exception as e:
        #     print(f"An error occurred while entering the price: {e}")
        try: 
            
            click_on_price_icons_for_all_rows2()###
        except json.JSONDecodeError as e:
            print(f" didinc licked price icon {e}")

        # try:
        #     click_open_orders_menu3 = wait.until(
        #         EC.element_to_be_clickable((By.XPATH,"//div[text()='Open Orders(1)']"))
        #     )                                                                              
        #     # 6. Belirlenen değeri yaz
        #     click_open_orders_menu3.click()
        # except Exception as e:
        #     print("didnt getted prices3") 

        # try:
        #     click_open_orders_menu4 = wait.until(
        #         EC.element_to_be_clickable((By.XPATH,"//div[text()='Open Orders(2)']"))
        #     )                                                                              
        #     # 6. Belirlenen değeri yaz
        #     click_open_orders_menu4.click()
        # except Exception as e:
        #     print("didnt getted prices4") 
        """ click order menu end"""

    except Exception as e:
        print(f"didnt getted prices5 {e}") 
    
    """ yedek fiyat çekme bölümü
    try:


        # bütün fiyatları listeleme
        # Fiyat elementlerinin ortak XPath'ini tanımlıyoruz.
        # Bu XPath, verdiğiniz HTML yapısına göre en uygun seçenektir.
        xpath = "//div[contains(@class, 'edit-order-item')]"#ant-table-cell
        
        # XPath'e uyan tüm elementleri bir liste olarak bulur.
        price_elements = driver.find_elements(By.XPATH, xpath)
        
        # Eğer hiç element bulunamazsa kullanıcıya bilgi verir.
        if not price_elements:
            print("Belirtilen XPath ile herhangi bir fiyat elementi bulunamadı.")
            return

        print(f"Toplam {len(price_elements)} adet fiyat elementi bulundu. Fiyatlar:")
        all_prices = []
    
        # Tüm elementlerin metinlerini alıp bir listeye ekler
        for element in price_elements:
            price_text = element.text.split('\n')[0].strip()
            all_prices.append(price_text)

        grouped_prices = []
        
        # Her üç elemanı bir grup olarak işler
        for i in range(0, len(all_prices), 3):
            # Listenin sonunda eksik eleman varsa hata vermesini önler
            if i + 2 < len(all_prices):
                group = {
                    "TP-SL": all_prices[i],
                    "order price": all_prices[i+1],
                    "Qty": all_prices[i+2]
                }
                grouped_prices.append(group)

        print("group rpiceses:",grouped_prices)
        print("trade list:",trade_list)

    except:
        print("didnt getted prices6")
    """


    # # Tüm tablo satırlarını bulmak için genel bir XPath ifadesi
    # try:
    #     rows_xpath = '//*[@id="swap-layout-desktop"]/div[3]/div[1]/div[2]/div/div[3]/div/div[2]/div/div/div/div/div[2]/table/tbody/tr'
    #     try:
    #         wait = WebDriverWait(driver, 10)
            
    #         # Tüm satır elementlerini bul
    #         all_rows = wait.until(EC.presence_of_all_elements_located((By.XPATH, rows_xpath)))
            
    #         print(f"Toplam {len(all_rows)} adet satır bulundu.")
            
    #         all_table_data = [] # Tüm tablo verilerini saklamak için ana liste
            
    #         # Her bir satır (tr) için döngü oluştur
    #         for i, row_element in enumerate(all_rows):
    #             row_data = [] # Bu satırdaki hücre verilerini saklamak için geçici liste
                
    #             # Bu satırın içindeki tüm td etiketlerini bul
    #             cell_elements = row_element.find_elements(By.TAG_NAME, 'td')
                
    #             # Her bir hücrenin metin içeriğini row_data listesine ekle
    #             for cell in cell_elements:
    #                 row_data.append(cell.text.strip())
                
    #             # Bu satırdaki verileri ana listeye ekle
    #             all_table_data.append(row_data)

    #         #print("all data:",all_table_data)
    #         market_revise(all_table_data)
    #     except Exception as e:
    #         print(f"Tablo verileri çekilirken bir hata oluştu: {e}")
    #         return None
    # except:
    #     print("didnt getted prices7")
    # fiyat işlemesi yapılacak burda fiyat ile canlı fiyat arasında işlem yapılıp sonuc fiyat bi aşağıda yazdırıalacak
   
    #market_revise(open_browser.order_main_list)
    




def market_revise(order_list):
    """
    Verilen liste formatındaki verileri ayıklar ve anlamlı değişkenlere atar.
    
    Args:
        order_list: Tablodan çekilen, hücre verilerini içeren bir liste.
        
    Returns:
        Her siparişin ayıklanmış verilerini içeren bir sözlükler listesi ve kontrol listesi.
    """
    # Fiyat değişkenlerini tanımla, ancak değer atama
    Op, Hp, Lp, Cp = None, None, None, None

    # Fiyat verisini bir kerede ve doğru şekilde çek
    for _ in range(5): # Sadece 5 deneme yapar
        open_price, high_price, low_price, close_price = asyncio.run(swap_open_close_values_From_websocket.receive_bydfi_data_once())
        
        # Eğer bir değer alınırsa, döngüyü kır
        if open_price is not None or  high_price is not None or  low_price is not None or  close_price is not None:
            Op, Hp, Lp, Cp = open_price, high_price, low_price, close_price
            break
    
    if Cp is None:
        print("Hata: WebSocket'ten geçerli bir kapanış fiyatı alınamadı.")
        return [], []
    
    extracted_data = []
    order_check_list_main = []

    for order_details_list in order_list:
        # for par in order_details_list:

        if not order_details_list or not order_details_list[0]:
            continue

        (time, coin_info, market_type, trade_type, tpsl_null, price, 
         qty_info, null1, null2, null3, null4) = order_details_list
        
        coin_parts = coin_info.split('\n')
        coin_name = coin_parts[0].strip()
        levaregeX = coin_parts[1].strip()
        market_account_type = coin_parts[2].strip().split(' ')[0]
        qty_price = qty_info.split('\n')[0].strip()

        order_details = {
            "date": time.strip(),
            "coin_name": coin_name,
            "levaregeX": levaregeX,
            "market_account_type": market_account_type,
            "market_type": market_type.strip(),
            "trade_type": trade_type.strip(),
            "price": price.strip(),
            "qty_price": qty_price
        }
        extracted_data.append(order_details)
        
        print(f"close price: {Cp} ({type(Cp)}), order price: {order_details['price']}")
        
        order_check_list = []
        
        try:
            order_price_float = float(order_details["price"])
        except (ValueError, IndexError):
            print(f"Hata: Geçersiz fiyat değeri: '{order_details['price']}'. Bu satır atlanıyor.")
            order_check_list_main.append([])
            continue
        threshold_small = 0.05
        threshold_medium = 0.10
        threshold_large = 0.20
        if order_details["trade_type"] == "Sell":#Sipariş fiyatınızın piyasa fiyatından biraz daha düşük olması gerekir. S 12, P 11 S->11.5
            price_diff = order_price_float - Cp
            print(price_diff)
            # Koşulları büyükten küçüğe sırala
            #   9.98                10     -0.02 işlem gerçekelşir
            #   10.2                10      0.02  işlem gerçkeleşmez
            if order_price_float - Cp > threshold_large:
                order_check_list.append(Cp-0.05)# kontrol edilecek
                order_check_list.append("--")# kontrol edilecek
            elif order_price_float - Cp > threshold_medium:
                order_check_list.append(Cp-0.05)# kontrol edilecek
                order_check_list.append("-")# kontrol edilecek
            elif order_price_float - Cp > threshold_small:
                order_check_list.append(Cp-0.05)# kontrol edilecek
                order_check_list.append("0")# kontrol edilecek
            elif order_price_float - Cp<=0:
                order_check_list.append(Cp-0.05)# kontrol edilecek
                order_check_list.append("00")# kontrol edilecek

        elif order_details["trade_type"] == "Buy":#Sipariş fiyatınızın piyasa fiyatından biraz daha yüksek olması gerekir.
            price_diff = Cp - order_price_float
            print(price_diff)
            # Koşulları büyükten küçüğe sırala ve operatörü düzelt

            #    10.2               10  0.2 işlem gerçkelşir
            #    9.98               10  -0.2 işlem gerçkelşemez

            if order_price_float - Cp > threshold_large:
                order_check_list.append(Cp+0.05)
                order_check_list.append("--")
            elif order_price_float - Cp > threshold_medium:
                order_check_list.append(Cp+0.05)
                order_check_list.append("-")
            elif order_price_float - Cp > threshold_small:
                order_check_list.append(Cp+0.05)
                order_check_list.append("0")
            elif order_price_float - Cp<=0:
                order_check_list.append(Cp+0.05)
                order_check_list.append("00")

        order_check_list_main.append(order_check_list)

    print("order check list main:", order_check_list_main)
    #click_on_price_icons_for_all_rows(order_check_list_main)
    #click_on_price_icons_for_all_rows2()
    #print(extracted_data)
    # print("extracted_data:",extracted_data)

    #return extracted_data


def click_on_price_icons_for_all_rows(order_check_list_main):
    """
    Belirtilen XPath'teki tablonun her satırının 6. sütunundaki simgeye tıklar.
    
    Args:
        driver: Selenium WebDriver nesnesi.
    """
    try:
        # Tüm tablo satırlarını bulan genel XPath
                    #//*[@id="swap-layout-desktop"]/div[2]/div[1]/div[2]/div/div[3]/div/div[2]/div/div/div/div/div[2]/table/tbody/tr[3]/td[6]/div/span/svg/path[2]
        rows_xpath = '//*[@id="swap-layout-desktop"]/div[2]/div[1]/div[2]/div/div[3]/div/div[2]/div/div/div/div/div[2]/table/tbody/tr'
        driver = open_browser.driver
        wait = WebDriverWait(driver, 10)
        
        # Tüm satır elementlerini bul
        all_rows = wait.until(EC.presence_of_all_elements_located((By.XPATH, rows_xpath)))
        
        print(f"Toplam {len(all_rows)} adet satır bulundu. Her satırdaki simgeye tıklanıyor...")
        
        # Her bir satır için döngü oluştur
        for i, row_element in enumerate(all_rows):
            # Dinamik XPath oluşturma
            # tr'nin indeksi 1'den başlar, bu yüzden i+1 kullanılır.
            # td[6] 6. sütunu, div/span/svg/* ise içindeki simgeyi hedef alır.
            icon_xpath = f'//*[@id="swap-layout-desktop"]/div[2]/div[1]/div[2]/div/div[3]/div/div[2]/div/div/div/div/div[2]/table/tbody/tr[{i+1}]/td[6]/div/span/svg/path[2]'
            
            try:
                # Simge elementini bul ve tıkla
                icon_element = wait.until(EC.element_to_be_clickable((By.XPATH, icon_xpath)))
                icon_element.click()
                print(f"Satır {i+1}'deki simgeye başarıyla tıklandı.")
                price_input = wait.until(
                EC.presence_of_element_located((By.XPATH, '/html/body/div[6]/div/div/div[2]/input'))#jsx-2185320666 components-numeric-input focus-active text-center full-width jsx-1225381481 trade-view-input dark jsx-2208463890 input
                )        
                                                                                        #jsx-2185320666
                price_input.send_keys(Keys.BACKSPACE)
                price_input.send_keys(Keys.BACKSPACE)
                price_input.send_keys(Keys.BACKSPACE)
                price_input.send_keys(Keys.BACKSPACE)
                price_input.send_keys(Keys.BACKSPACE)
                price_input.send_keys(Keys.BACKSPACE)
                price_input.send_keys(Keys.BACKSPACE)
                # 6. Belirlenen değeri yaz
                
                print("sendet")
                if order_check_list_main[i][1]=="--":
                    price_input.send_keys(order_check_list_main[0])
                    print("price from comfigriure:",order_check_list_main[0])
                elif order_check_list_main[i][1]=="-":
                    price_input.send_keys(order_check_list_main[0])
                    print("price from comfigriure:",order_check_list_main[0])
                elif order_check_list_main[i][1]=="0":
                    price_input.send_keys(order_check_list_main[0])
                    print("price from comfigriure:",order_check_list_main[0])
                elif order_check_list_main[i][1]=="00":
                    price_input.send_keys(order_check_list_main[0])
                    print("price from comfigriure:",order_check_list_main[0])
                
                    
                
            except Exception as e:
                print(f"Satır {i+1}'deki simgeye tıklanırken hata oluştu: {e}")
                # Hata durumunda döngü devam eder, tüm satırları denemeye devam eder.

    except Exception as e:
        print(f"Tablo verileri çekilirken bir hata oluştu: {e}")

# def delete_order():
#     driver = open_browser.driver
#     wait = WebDriverWait(driver, 10)
#     try:
        
#         del_element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="swap-layout-desktop"]/div[2]/div[1]/div[2]/div/div[3]/div/div[2]/div/div/div/div/div[2]/table/tbody/tr[2]/td[11]/div')))
                        
#         # 2. Elementi görüntü alanına getirmek için JavaScript kullan
#         driver.execute_script("arguments[0].scrollIntoView(true);", del_element)
        
#         # 3. Elementin tıklanabilir olduğundan emin olmak için tekrar bekle
#         wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="swap-layout-desktop"]/div[2]/div[1]/div[2]/div/div[3]/div/div[2]/div/div/div/div/div[2]/table/tbody/tr[2]/td[11]/div')))
        
#         # 4. Tıklama işlemini gerçekleştir
#         del_element.click()
#     except:


#         try:
#         global order_control_id
#         global order_control_symbol
#         global order_control_qty
#         global order_control_price
#         global order_control_side
        
#         # open_browser.order_control_id=""
#         # open_browser.order_control_symbol=""
#         # open_browser.order_contro=float
#         """
#         Belirtilen XPath'teki tablonun her satırının 6. sütunundaki simgeye tıklar.
        
#         Args:
#             driver: Selenium WebDriver nesnesi.
#         """
#         # print("for i in order_main_list start")
#         try:
#             # Tüm tablo satırlarını bulan genel XPath
#                         #//*[@id="swap-layout-desktop"]/div[2]/div[1]/div[2]/div/div[3]/div/div[2]/div/div/div/div/div[2]/table/tbody/tr[3]/td[6]/div/span/svg/path[2]
#             rows_xpath = '//*[@id="swap-layout-desktop"]/div[2]/div[1]/div[2]/div/div[3]/div/div[2]/div/div/div/div/div[2]/table/tbody/tr'
#             driver = open_browser.driver
#             wait = WebDriverWait(driver, 10)
#             # print("for i in order_main_list")
#             range_list=len(open_browser.order_delete_list)
#             # print("range list ",range_list)
#             i=0
#             for i in range(range_list):#[['9096981525974680409', '2', 'sxrp-susdt', 120, '3.533'], ['9096955343854046673', '2', 'ssol-susdt', 150, '221.12'], ['9096952079678906352', '2', 'sxrp-susdt', 150, '220.12']]
#                 #i+=1
#                 order_control_id=open_browser.order_main_list[i][0]
#                 order_control_side=open_browser.order_main_list[i][1]
#                 order_control_symbol=open_browser.order_main_list[i][2]
#                 order_control_price=float(open_browser.order_main_list[i][4])
#                 order_control_qty = open_browser.order_main_list[i][3]
#                 try:
#                     liste=check_price_value(order_control_symbol,order_control_side,order_control_price)
#                 except json.JSONDecodeError as e:
#                     print(f"check_price_value error {e}")

#                 flag=liste[0]
#                 new_price=liste[1] 
#                 order_control_price=round(new_price, 3)
#                 # print("order_main_list: ",open_browser.order_main_list)
#                 print("flag:",flag,"new price: ",order_control_price)

#                 if flag=="flag=0":
#                     print("flag= ",flag)
#                     continue
                

#                 elif flag =="flag=1":

#                     """ clcik """
#                     try:
#                         print("flag= ",flag)       #                                //*[@id="swap-layout-desktop"]/div[3]/div[1]/div[2]/div/div[3]/div/div[2]/div/div/div/div/div[2]/table/tbody/tr[2]/td[6]/div/span                                                 
#                         # 1. Elementi bul
#                         element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="swap-layout-desktop"]/div[3]/div[1]/div[2]/div/div[3]/div/div[2]/div/div/div/div/div[2]/table/tbody/tr[2]/td[6]/div/span')))
                        
#                         # 2. Elementi görüntü alanına getirmek için JavaScript kullan
#                         driver.execute_script("arguments[0].scrollIntoView(true);", element)
                        
#                         # 3. Elementin tıklanabilir olduğundan emin olmak için tekrar bekle
#                         wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="swap-layout-desktop"]/div[3]/div[1]/div[2]/div/div[3]/div/div[2]/div/div/div/div/div[2]/table/tbody/tr[2]/td[6]/div/span')))
                        
#                         # 4. Tıklama işlemini gerçekleştir
#                         element.click()
#                         time.sleep(1)
#                     except json.JSONDecodeError as e:
#                         print(f"click error1 {e}")

                 


                  
            
#         except Exception as e:
#             print(f"click error2")
#     except json.JSONDecodeError as e:
#         print("fin row error {e}")


def click_on_price_icons_for_all_rows2():
    try:
        global order_control_id
        global order_control_symbol
        global order_control_qty
        global order_control_price
        global order_control_side
        
        # open_browser.order_control_id=""
        # open_browser.order_control_symbol=""
        # open_browser.order_contro=float
        """
        Belirtilen XPath'teki tablonun her satırının 6. sütunundaki simgeye tıklar.
        
        Args:
            driver: Selenium WebDriver nesnesi.
        """
        # print("for i in order_main_list start")
        try:
            # Tüm tablo satırlarını bulan genel XPath
                        #//*[@id="swap-layout-desktop"]/div[2]/div[1]/div[2]/div/div[3]/div/div[2]/div/div/div/div/div[2]/table/tbody/tr[3]/td[6]/div/span/svg/path[2]
            rows_xpath = '//*[@id="swap-layout-desktop"]/div[2]/div[1]/div[2]/div/div[3]/div/div[2]/div/div/div/div/div[2]/table/tbody/tr'
            driver = open_browser.driver
            wait = WebDriverWait(driver, 10)
            # print("for i in order_main_list")
            range_list=len(open_browser.order_main_list)
            # print("range list ",range_list)
            i=0
            for i in range(range_list):#[['9096981525974680409', '2', 'sxrp-susdt', 120, '3.533'], ['9096955343854046673', '2', 'ssol-susdt', 150, '221.12'], ['9096952079678906352', '2', 'sxrp-susdt', 150, '220.12']]
                #i+=1
                order_control_id=open_browser.order_main_list[i][0]
                order_control_side=open_browser.order_main_list[i][1]
                order_control_symbol=open_browser.order_main_list[i][2]
                order_control_price=float(open_browser.order_main_list[i][4])
                order_control_qty = open_browser.order_main_list[i][3]
                try:
                    liste=check_price_value(order_control_symbol,order_control_side,order_control_price)
                except json.JSONDecodeError as e:
                    print(f"check_price_value error {e}")

                flag=liste[0]
                new_price=liste[1] 
                order_control_price=round(new_price, 3)
                # print("order_main_list: ",open_browser.order_main_list)
                print("flag:",flag,"new price: ",order_control_price)

                if flag=="flag=0":
                    print("flag= ",flag)
                    continue
                

                elif flag =="flag=1":

                    """ clcik """
                    try:
                        print("flag= ",flag)       #                                //*[@id="swap-layout-desktop"]/div[3]/div[1]/div[2]/div/div[3]/div/div[2]/div/div/div/div/div[2]/table/tbody/tr[2]/td[6]/div/span                                                 
                        # 1. Elementi bul
                        element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="swap-layout-desktop"]/div[3]/div[1]/div[2]/div/div[3]/div/div[2]/div/div/div/div/div[2]/table/tbody/tr[2]/td[6]/div/span')))
                        
                        # 2. Elementi görüntü alanına getirmek için JavaScript kullan
                        driver.execute_script("arguments[0].scrollIntoView(true);", element)
                        
                        # 3. Elementin tıklanabilir olduğundan emin olmak için tekrar bekle
                        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="swap-layout-desktop"]/div[3]/div[1]/div[2]/div/div[3]/div/div[2]/div/div/div/div/div[2]/table/tbody/tr[2]/td[6]/div/span')))
                        
                        # 4. Tıklama işlemini gerçekleştir
                        element.click()
                        time.sleep(1)
                    except json.JSONDecodeError as e:
                        print(f"click error1 {e}")

                    # try:
                    #     # 2. Input alanının XPath'ini tanımla
                    #     input_xpath = '//div[contains(@class, "trade-view-input")]/input'
                        
                    #     # 3. Elementin DOM'da var olmasını bekle (tıklanabilir olması zorunlu değil)
                    #     price_input = wait.until(EC.presence_of_element_located((By.XPATH, input_xpath)))
                        
                    #     # 4. JavaScript kullanarak değeri doğrudan gir
                    #     price_to_enter = "2.7585"
                    #     driver.execute_script(f"arguments[0].value = '{price_to_enter}';", price_input)
                    #     print(f"Fiyat JavaScript ile başarıyla girildi: {price_to_enter}")
                        
                    # except Exception as e:
                    #     print(f"sending error: {e}")
                    # try:
                        
                    # except:
                    #     print("didnt sendet edit order api")


                    """ clcik  comfirum"""

                    try:
                        # 4. Onay butonuna tıkla
                        time.sleep(1)
                        # print("id symbol price",order_control_id,order_control_symbol,order_control_price)
                        check_button_xpath = "//span[@aria-label='check']"
                        check_button = wait.until(EC.element_to_be_clickable((By.XPATH, check_button_xpath)))
                        check_button.click()
                        # print("Onay butonuna tıklandı.")

                    except Exception as e:
                        print(f"An error occurred while entering the price: {e}")    
                    print("price  configired")
            
        except Exception as e:
            print(f"click error2")
    except json.JSONDecodeError as e:
        print("fin row error {e}")


def check_price_value(symbol,side,price):
    try:
        try:
            for a in range(5): # Sadece 5 deneme yapar
                open_price, high_price, low_price, close_price = asyncio.run(swap_open_close_values_From_websocket.receive_bydfi_data_once(symbol))
                
                # Eğer bir değer alınırsa, döngüyü kır
                if open_price is not None or  high_price is not None or  low_price is not None or  close_price is not None:
                    Op, Hp, Lp, Cp = open_price, high_price, low_price, float(close_price)
                    print("op hp lp cp",Op, Hp, Lp, Cp)
                    break
                    
        except json.JSONDecodeError as e:
            print(f"recive socket error {e}")
        threshold_small = 0.001
        threshold_medium = 0.02
        threshold_large = 0.05    
        print("symbol side price",symbol,side,price)
        
        if str(side) == "2":  # SELL
                        #3.0035 - 2.7561
            price_diff = price - Cp
            print("sell price diff: ",price_diff)#0.2474

            if price_diff > threshold_small:
                try:
                    decimal_part = str(Cp).split(".")[1]
                    last_two = decimal_part[-2:]
                    last_two_val = int(last_two) / 4000  # 2 basamaklı ondalık değer

                    new_price = Cp - last_two_val
                    return ["flag=1", new_price]
                except json.JSONDecodeError as e:
                    print(f"sell price didint configuret {e}")
                    return ["flag=1", price]
            elif Cp - price > 0:
                print("price under the target")
                return ["flag=0", Cp]  # fallback olarak Cp veya price dönebilirsin
            else:
                return ["flag=0", Cp]
        elif str(side) == "1":  # BUY
            price_diff = Cp - price
            print("buy price diff: ",price_diff)

            if price_diff > threshold_small:
                try:
                    decimal_part = str(Cp).split(".")[1]
                    last_two = decimal_part[-2:]
                    last_two_val = int(last_two) / 4000

                    new_price = Cp + last_two_val
                    return ["flag=1", new_price]
                except json.JSONDecodeError as e:
                    print(f"Buy price didint configuret {e}")
                    return ["flag=1", price]

            elif Cp - price < 0:
                print("price under the target")
                return ["flag=0", Cp]
            else:
                return ["flag=0", Cp]
            
    except json.JSONDecodeError as e:
        print(f"check price value function error {e}")






def place_bydfi_order():
    """
    Verilen HTTP isteğine dayanarak ByDFi'ye API çağrısı yapar.
    
    Not: Bu kodun çalışması için 'Cookie' ve 'TOKEN' değerlerinin güncel olması gerekir.
    """
    url = "https://www.bydfi.com/testnet/private/future/order/otoco"

    # HTTP isteğinden alınan tüm başlıklar
    headers = {
        "Host": "www.bydfi.com",
        "Cookie": "agent=false; agent=false; vipCode=mZVhKc; user_origin=1; user_origin=1; lang=en; lang=en; _ga=GA1.1.0202025273.5519521945; _cfuvid=.ykfIW4_8ktXHtW_FXYq5OxFyBqivWFlTLBV2XszcaM-1756551984099-0.0.1.1-604800000; cf_clearance=mh8Wx9Ry9VdAmPwV_5uefOufkPEXtOMS6KuJByFKDNE-1756553235-1.2.1.1-Xo8p3oYVAZ6BrCZSzHAvNdHn3TM7GiCRcBEo6iGlQPSvlhi.m4O9Yy2W.gbVHZjBJS8fLSmyChTQpnpKX2GgUcsSHp7p8pfuIPP3ylnojxppuOooOgXOdeD8Wd8DWjFHhjH0N9_MacvkaS7y77cC2jJ4QYDjY7jQp.oI09L4q38C20bBlnQuZ95JsROTZs; JSESSIONID=6744CB7F534B4AEAB60922CC13991986; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%221159195216110198785%22%2C%22first_id%22%3A%22198432b871f774-0220cc84e196ca6-26011151-2073600-198432b8720b81%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTk4NDMyYjg3MWY3NzQtMDIyMGNjODRlMTk2Y2E2LTI2MDExMTUxLTIwNzM2MDAtMTk4NDMyYjg3MjBiODEiLCIkaWRlbnRpdHlfbG9naW5faWQiOiIxMTU5MTk1MjE2MTEwMTk4Nzg1In0%3D%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%24identity_login_id%22%2C%22value%22%3A%221159195216110198785%22%7D%7D; TOKEN=d4a8920b-a8ef-437a-b98f-87fd37353691; __cf_bm=OcYflDHcdXGKXom10MhUi89ltQwBpyFBDhjoAHxP4dI-1756553894-1.0.1.1-D1UJ6xJRltt1F8BSn11OQc_SWT0u1TlW9n_QeYjKm66vIeBZqm2U.bEtQZv6n1ExbctVtmczVY9FD_P3tYqyInrgHV.JKMDwzPd9SqPk8hU; _ga_7ZEWNTGRR0=GS2.1.s1756553236$o27$g1$t1756554052$j60$l0$h0",
        "Content-Length": "96",
        "Sec-Ch-Ua-Full-Version-List": '"Not;A=Brand";v="99.0.0.0", "Google Chrome";v="139.0.7258.139", "Chromium";v="139.0.7258.139"',
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Accept-Language": "en-US",
        "Sec-Ch-Ua": '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
        "Sec-Ch-Ua-Bitness": '"64"',
        "Ppw": "W001",
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Model": '""',
        "Sec-Ch-Ua-Arch": '"x86"',
        "Sec-Ch-Ua-Full-Version": '"139.0.7258.139"',
        "Accept": "application/json, text/plain, */*",
        "Device-Info": "eyJkZXZpY2VfaWQiOiIiLCJkZXZpY2VfbmFtZSI6ImNocm9tZSIsIm1vZGVsIjoid2ViIiwic3lzdGVtX2xhbmciOiJlbi1VUyIsInN5c3RlbV92ZXJzaW9uIjoiMTM5LjAiLCJ0aW1lem9uZSI6IkdNVCszIiwidXNlcl9hZ2VudCI6Ik1vemlsbGEvNS4wIChXaW5kb3dzIE5UIDEwLjA7IFdpbjY0OyB4NjQpIEFwcGxlV2ViS2l0LzUzNy4zNiAoS0hUTUwsIGxpa2UgR2Vja28pIENocm9tZS8xMzkuMC4wLjAgU2FmYXJpLzUzNy4zNiIsInBsYXRmb3JtIjoiV2luZG93cyIsImxhdGxuZyI6IiIsImZpbmdlcnByaW50IjoiRlBDX001MlZOZDd1MGthajZ0TFp2dmV1IiwicmVxdWVzdElkIjoiRlBDX0RkTDE5MVV5b2doYzhNRzRkYzA0In0=",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
        "Sec-Ch-Ua-Platform-Version": '"10.0.0"',
        "Origin": "https://www.bydfi.com",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://www.bydfi.com/en/swap/demo?id=sxrp-susdt",
        "Accept-Encoding": "gzip, deflate, br",
        "Priority": "u=1, i"
    }

    # HTTP isteğinden alınan JSON payload
    data = {
        "symbol": "sxrp-susdt",
        "orderQty": 16,
        "future": 0,
        "price": "3.0670",
        "side": 2,
        "type": "1",
        "source": 1
    }

    print("API'ye POST isteği gönderiliyor...")
    try:
        # requests.post ile isteği gönder
        response = requests.post(url, headers=headers, data=json.dumps(data))

        # Hatalı HTTP durum kodları için hata fırlat
        response.raise_for_status()

        print("Sipariş başarıyla verildi!")
        print("Yanıt Durum Kodu:", response.status_code)
        print("Yanıt İçeriği:", response.json())
        
    except requests.exceptions.RequestException as e:
        print(f"İstek sırasında bir hata oluştu: {e}")
        if 'response' in locals() and response.status_code:
            print("Yanıt Durum Kodu:", response.status_code)
            print("Yanıt İçeriği:", response.text)
    




def edit_bydfi_order(id,side,symbol,oQty,price):
    """
    Simulates an API request to edit an existing futures order on ByDFi.
    
    This code uses the provided headers and payload.
    NOTE: The 'Cookie' and 'TOKEN' values must be up-to-date.
    """
    url = "https://www.bydfi.com/testnet/private/future/order/edit_order"

    # The headers from your HTTP request
    headers = {
        "Host": "www.bydfi.com",
        "Cookie": "agent=false; agent=false; vipCode=mZVhKc; user_origin=1; user_origin=1; lang=en; lang=en; _ga=GA1.1.0202025273.5519521945; _cfuvid=.ykfIW4_8ktXHtW_FXYq5OxFyBqivWFlTLBV2XszcaM-1756551984099-0.0.1.1-604800000; __cf_bm=ye7tgHlNYE3RNQrGF.BXybz9T7FtrCcKFKa0btU.bKA-1756552959-1.0.1.1-3tz_myh80hi9srv03qfcoFD4Z1y_lehhQg6fXeYKA9_FGmPsB2jJFVXyBmO6oiKEUsCGlwQl1Keb_zebuZv7zTtVfFDXL9xmI2rj5UE39Po; cf_clearance=mh8Wx9Ry9VdAmPwV_5uefOufkPEXtOMS6KuJByFKDNE-1756553235-1.2.1.1-Xo8p3oYVAZ6BrCZSzHAvNdHn3TM7GiCRcBEo6iGlQPSvlhi.m4O9Yy2W.gbVHZjBJS8fLSmyChTQpnpKX2GgUcsSHp7p8pfuIPP3ylnojxppuOooOgXOdeD8Wd8DWjFHhjH0N9_MacvkaS7y77cC2jJ4QYDjY7jFQPX33tkVYzOAUHewZkmq2i5klXtltMKbFJSQ00moF3f6pK.oI09L4q38C20bBlnQuZ95JsROTZs; JSESSIONID=6744CB7F534B4AEAB60922CC13991986; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%221159195216110198785%22%2C%22first_id%22%3A%22198432b871f774-0220cc84e196ca6-26011151-2073600-198432b8720b81%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTk4NDMyYjg3MWY3NzQtMDIyMGNjODRlMTk2Y2E2LTI2MDExMTUxLTIwNzM2MDAtMTk4NDMyYjg3MjBiODEiLCIkaWRlbnRpdHlfbG9naW5faWQiOiIxMTU5MTk1MjE2MTEwMTk4Nzg1In0%3D%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%24identity_login_id%22%2C%22value%22%3A%221159195216110198785%22%7D%7D; TOKEN=d4a8920b-a8ef-437a-b98f-87fd37353691; _ga_7ZEWNTGRR0=GS2.1.s1756553236$o27$g1$t1756553273$j23$l0$h0",
        "Content-Length": "176",
        "Sec-Ch-Ua-Full-Version-List": '"Not;A=Brand";v="99.0.0.0", "Google Chrome";v="139.0.7258.139", "Chromium";v="139.0.7258.139"',
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Accept-Language": "en-US",
        "Sec-Ch-Ua": '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
        "Sec-Ch-Ua-Bitness": '"64"',
        "Ppw": "W001",
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Model": '""',
        "Sec-Ch-Ua-Arch": '"x86"',
        "Sec-Ch-Ua-Full-Version": '"139.0.7258.139"',
        "Accept": "application/json, text/plain, */*",
        "Device-Info": "eyJkZXZpY2VfaWQiOiIiLCJkZXZpY2VfbmFtZSI6ImNocm9tZSIsIm1vZGVsIjoid2ViIiwic3lzdGVtX2xhbmciOiJlbi1VUyIsInN5c3RlbV92ZXJzaW9uIjoiMTM5LjAiLCJ0aW1lem9uZSI6IkdNVCszIiwidXNlcl9hZ2VudCI6Ik1vemlsbGEvNS4wIChXaW5kb3dzIE5UIDEwLjA7IFdpbjY0OyB4NjQpIEFwcGxlV2ViS2l0LzUzNy4zNiAoS0hUTUwsIGxpa2UgR2Vja28pIENocm9tZS8xMzkuMC4wLjAgU2FmYXJpLzUzNy4zNiIsInBsYXRmb3JtIjoiV2luZG93cyIsImxhdGxuZyI6IiIsImZpbmdlcnByaW50IjoiRlBDX001MlZOZDd1MGthajZ0TFp2dmV1IiwicmVxdWVzdElkIjoiRlBDX0RkTDE5MVV5b2doYzhNRzRkYzA0In0=",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
        "Sec-Ch-Ua-Platform-Version": '"10.0.0"',
        "Origin": "https://www.bydfi.com",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://www.bydfi.com/en/swap/demo?id=sbtc-susdt",
        "Accept-Encoding": "gzip, deflate, br",
        "Priority": "u=1, i"
    }

    # The JSON payload from your HTTP request
    data = {
        "side": side,
        "source": 1,
        "subWallet": "W001",
        "symbol": symbol,
        "type": type,
        "originalOrderId": id,
        "orderQty": oQty,
        "price": price,
        "reduceOnly": None,
        "version": "2.0"
    }

    print("Sending POST request to edit order...")
    try:
        # Use requests.post to send the request
        response = requests.post(url, headers=headers, data=json.dumps(data))

        # Check the status code and response
        response.raise_for_status()
        
        print("Order edit request sent successfully!")
        print("Response Status Code:", response.status_code)
        print("Response Body:", response.json())

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        if 'response' in locals():
            print("Response Status Code:", response.status_code)
            print("Response Body:", response.text)


def parse_positions(json_data):
    """
    Gelen JSON verisindeki pozisyon bilgilerini ayrıştırır ve yazdırır.

    Args:
        json_data (str): JSON formatındaki pozisyon verisi.
    """
    try:
        # JSON string'ini Python sözlüğüne dönüştür
        data = json.loads(json_data)

        # "data" anahtarının altında bir liste olup olmadığını kontrol et
        if "data" in data and isinstance(data["data"], list):
            positions = data["data"]
            
            # Her bir pozisyonu döngü ile gez
            for i, position in enumerate(positions):
                print(f"--- Pozisyon #{i+1} için Veriler ---")
                
                # Her bir değişkeni yazdır
                print(f"Pozisyon ID: {position.get('positionId')}")
                print(f"Sembol: {position.get('symbol')}")
                print(f"Mevcut Pozisyon: {position.get('currentPosition')}")
                print(f"Maliyet Fiyatı: {position.get('avgCostPrice')}")
                print(f"İşaret Fiyatı (Mark Price): {position.get('markPrice')}")
                print(f"Gerçekleşmiş K/Z: {position.get('realizedPnl')}")
                print(f"Likidasyon Fiyatı: {position.get('liquidationPrice')}")
                print(f"Marjin: {position.get('margin')}")
                print(f"Yön (Side): {position.get('side')}") # 1: Long, 2: Short
                print(f"Kaldıraç (Leverage): {position.get('leverage')}")
                
                print("-" * 30)
                
        else:
            print("JSON verisinde 'data' anahtarı veya liste formatı bulunamadı.")

    except json.JSONDecodeError as e:
        print(f"JSON verisi çözülürken hata oluştu: {e}")


def parse_orders(json_data):
    """
    Gelen JSON verisindeki sipariş bilgilerini ayrıştırır ve yazdırır.

    Args:
        json_data (str): JSON formatındaki sipariş verisi.
    """
    try:
        # JSON string'ini Python sözlüğüne dönüştür
        data = json.loads(json_data)

        # "data" anahtarının altında bir liste olup olmadığını kontrol et
        if "data" in data and isinstance(data["data"], list):
            orders = data["data"]
            
            # Her bir siparişi döngü ile gez
            for i, order in enumerate(orders):
                print(f"--- Sipariş #{i+1} için Veriler ---")
                
                # Her bir değişkeni güvenli bir şekilde al ve yazdır
                order_id = order.get('orderId')
                symbol = order.get('symbol')
                volume = order.get('volume')
                price = order.get('price')
                side = order.get('side')
                status = order.get('status')
                
                print(f"Sipariş ID: {order_id}")
                print(f"Sembol: {symbol}")
                print(f"Hacim: {volume}")
                print(f"Fiyat: {price}")
                print(f"Yön (1: Alış, 2: Satış): {side}")
                print(f"Durum (1: Beklemede, 2: Kısmen Dolu, 3: Tamamen Dolu): {status}")
                
                print("-" * 30)
                
        else:
            print("JSON verisinde 'data' anahtarı veya liste formatı bulunamadı.")

    except json.JSONDecodeError as e:
        print(f"JSON verisi çözülürken hata oluştu: {e}")