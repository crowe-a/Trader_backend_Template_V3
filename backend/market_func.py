
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
global_otoco_list=[]
# log = logging.getLogger(__name__)
# from backend import market_func
#  #levarege sisemine bağlanıcak
# market_func.getpayload(payload)
# #print("payload:",payload)





def getpayload(payload):
    print("payload ",payload)
    runner_id=payload["runner_id"]

    global global_otoco_list
    json_data=payload["data"]

    # Retrieving data
    identifier = json_data['identifier']
    kind = json_data['kind']
    recalc = json_data['Recalc']

    # 'chart' Retrieving data
    chart_url = json_data['chart']['url']
    chart_interval = json_data['chart']['interval']

    # 'trade' Retrieving data
    trade_id = json_data['trade']['id']
    trade_entry_type = json_data['trade']['entry_type']
    trade_entry_signal = json_data['trade']['entry_signal']
    trade_entry_price = json_data['trade']['entry_price']
    trade_entry_time = json_data['trade']['entry_time']
    trade_position = json_data['trade']['position']

    # 'raw' Retrieving data
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
    #     with db.connect() as conn, conn.cursor() as cur:
    #         rows = db.fetch_all_trades(cur,limit=2000)
    #         #print({"identifier": identifier, "count": len(rows), "rows": rows})
            

    # except:
    #     print(" fetch all trades  db error: ")

    signal_parts = raw_signal.split(',')
    first_part_of_signal = signal_parts[0].strip()

    first_par_posiiton_size = raw_position_size.split(',')[0]

    # to convert float
    first_par_posiiton_size = float(first_par_posiiton_size)

    


        

    target_id = runner_id  # currency_id== signaler runner_id

    try:
        limit: int = 100
        with db.connect() as conn:
            with conn.cursor() as cur:
                configurations = db.fetch_all_configurations(cur, limit)
                # filter matched pairs
                matched = [conf for conf in configurations if conf.get("runner_id") == target_id]

        # print("matched:",matched)  # The matching list contains only rows with the desired currency pair.

    except Exception as e:
        print("Catch configurations db error: %s", e)
    config=None
    try:
        
        config = matched[0]
        if len(matched)==0 or len(matched[0])==0:
            print("check db there is no matched values in configuration or in signal")
        
            
        

    except:
        
        print("matched error")
    print("matched: ",matched)
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

    # all_trad = db.fetch_trade_backup()  # fetch_trade_backup ()returns a tuple, we get it with [0]
    result = db.fetch_trade_backup()  # return tupple
    all_backups = result          # get list in tuple 

    # print(all_trades)
    # #Example: record with runner id=1 and runner_id from signaler=""
    # runner_id = runner_id
    runner_id = runner_id

    filtered = [t for t in all_backups if t["runner_id"] == runner_id and t["runner_id"] == runner_id]
    
    print("filtered:",filtered)
    #Qty=float

    if first_part_of_signal=="Strong Sell":
        signal="Sell"

    if first_part_of_signal=="Strong Buy":
       signal="Buy"
    try:
        new_signal = {
        "tradeid": trade_id,
        "identifier": runner_id,
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

    qty=None
    list_of_trade=[]
    """
    list or trade = 
    
    ssol-susdt
    
    """
    print("order type",order_type)
    if order_type=="Limit":#limit== type=1
        list_of_trade=["",{"symbol":"","orderQty":0,"future":0,"price":"","side":1,"type":"1","source":1}]
        list_of_trade[1]["type"]="1"
        list_of_trade[1]["price"]=str(raw_open_price)# add raw_open_price
    if order_type=="Market":# market== type=2
        list_of_trade=["",{"symbol":"","orderQty":11,"side":2,"type":"2","source":1}]
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
            # An update will be made after the purchase is completed.
            
            if len(filtered)==0:
                trade_data = {
                "runner_id": runner_id,
                "identifier": currency_pair,
                "first_balance": float(starting_balance),#800
                "now_balance": float(starting_balance-starting_balance*tr),
                "buyed_or_selled_coin_qty":float(-starting_balance*tr/float(raw_open_price)),
                "trade_count": 1,
                 "trade_id":trade_id,
                 "order_id":""
            }
                qty=starting_balance*tr/float(raw_open_price)#qty to next trade

                list_of_trade[1]["orderQty"]=int(round(qty,0))*10
                list_of_trade.append(1)
                list_of_trade.append(currency_pair)
                list_of_trade.append(runner_id)
                # ["c",{"symbol":"-susdt","orderQty":0,"future":0,"price":"","side":1,"type":"1","source":1},lvx,1,identifier,runner_id]

                db.upsert_trade_backup(trade_data)
                print("file didint found in db and added")
            else:
                for data in filtered:
                    if data["trade_count"]:
                        trade_data = {
                        "runner_id": runner_id,
                        "identifier": currency_pair,
                        "first_balance": float(starting_balance),#800
                        
                        "now_balance": float(data["now_balance"]-data["now_balance"]*tr),
                        "buyed_or_selled_coin_qty":float(data["buyed_or_selled_coin_qty"]-data["now_balance"]*tr/float(raw_open_price)),
                        "trade_count": data["trade_count"]+1,
                        "trade_id":trade_id,
                        "order_id":""
                    }
                        
                        qty=starting_balance*tr/float(raw_open_price)#qty to next trade
                        
                        list_of_trade[1]["orderQty"]=int(round(qty,0))*10
                        list_of_trade.append(data["trade_count"]+1)
                        list_of_trade.append(currency_pair)
                        list_of_trade.append(runner_id)
                        db.upsert_trade_backup(trade_data)
                        print("file  found in db ")


            
            



            
            
            # print("sell ",record_list[6],record_list[7],"0",record_list[5],raw_open_price,1,"SELL",0,0,0)
            print("g otoc list in market: ",list_of_trade)
            global_otoco_list=list_of_trade
            print("g otoc list in market: ",global_otoco_list)
            buysellLimit(list_of_trade)
        except Exception as e:
            print("sell function error: %s", e)


    if first_part_of_signal=="Strong Buy":
        try:#                   Limit      10           0   sxrp-susdt      2.9060        10 BUY 0 0 0
            
            if  len(filtered)==0:
                
                trade_data = {
                "runner_id": runner_id,
                "identifier": currency_pair,
                "first_balance": float(starting_balance),#800
                "now_balance": float(starting_balance-starting_balance*tr),
                "buyed_or_selled_coin_qty":float(+starting_balance*tr/float(raw_open_price)),
                "trade_count": 1,
                "trade_id":trade_id,
                 "order_id":""
            }
                qty=float(starting_balance)*float(tr)/float(raw_open_price)#qty to next trade

                list_of_trade[1]["orderQty"]=int(round(qty,0))*10
                list_of_trade.append(1)
                list_of_trade.append(currency_pair)
                list_of_trade.append(runner_id)
                db.upsert_trade_backup(trade_data)
                print("file didint found in db and added")
            else:
                print(2)
                for data in filtered:
                    if data["trade_count"]:
                        trade_data = {
                        "runner_id": runner_id,
                        "identifier": currency_pair,
                        "first_balance": float(starting_balance),#800
                        "buyed_or_selled_coin_qty":float(data["buyed_or_selled_coin_qty"]+data["now_balance"]*tr/float(raw_open_price)),
                        "now_balance": float(data["now_balance"]-data["now_balance"]*tr),
                        
                        "trade_count": data["trade_count"]+1,
                        "trade_id":trade_id,
                        "order_id":""
                    }
                        qty=starting_balance*tr/float(raw_open_price)#qty to next trade

                        list_of_trade[1]["orderQty"]=int(round(qty,0))*10
                        list_of_trade.append(data["trade_count"]+1)
                        list_of_trade.append(currency_pair)
                        list_of_trade.append(runner_id)

                        db.upsert_trade_backup(trade_data)
                        print("file  found in db")

           
            

            

            print("g otoc list in market: ",list_of_trade)
            global_otoco_list=list_of_trade
            print("g otoc list in market: ",global_otoco_list)
            # print("buy ",record_list[6],record_list[7],"0",record_list[5],raw_open_price,10,"BUY",0,0,0)
            buysellLimit(list_of_trade)
        except Exception as e:
            print("buy  function error: %s", e)
     

""" Prepare a system that will work in two cases at the end of the open browser: 1. cross 2. isolated"""

#last_price is marketing type , market or limit
def buysellLimit(list_of_trade):
    # ["c",{"symbol":"-susdt","orderQty":0,"future":0,"price":"","side":1,"type":"1","source":1},lvx,1,identifier,runner_id]
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

        # print("matched:",matched)  # The matched list contains only the rows that contain the currency pair you want.
        print("fcl ",first_config_list)
    except Exception as e:
        print("Catch configurations db error: %s", e)


    # all_fetch_list=db.fetch_trade_backup()
    # for i in all_fetch_list:

    # print("all fetch:",all_fetch_list)
    # first_ballance=fetchet_list[2]
    # now_ballance=fetchet_list[3]
    # buyyed_selled_qty=fetchet_list[4]
    try:
        print("fetched list: ",fetchet_list)
        if len(fetchet_list)==1:
            trade_count=fetchet_list[0]["trade_count"]
        print("trade count: ",trade_count)
    except:
        print("trade count didint found")

    
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
            print("lenght trade list",len(trade_list))
            for b in trade_list:
                first_configuration(b[3],b[1],b[2],b[0])


            """ trade transactions"""
            try:

                # ["c",{"symbol":"-susdt","orderQty":0,"future":0,"price":"","side":1,"type":"1","source":1},lvx,1,identifier,runner_id]
                print("type: ",type(list_of_trade[1]["type"]))
                if 1==1:
                    
                    """ click last price"""
                    try:
                        i=0
                        #swap-layout-desktop > div.jsx-1790752364.swap-layout-content > div.jsx-1790752364.swap-layout-right > div.jsx-1790752364.trade-view.bg.card-radius > div:nth-child(4) > div.swap-guide-step-3.trade-view-input-wrap > div.jsx-1147981079.input-view > div:nth-child(1) > div > div.jsx-1147981079.newest
                        for i in range(5):
                            clickGETLASTPRICE = wait.until(EC.element_to_be_clickable((By.XPATH,"//div[text()='Last']")))
                            clickGETLASTPRICE.click()
                            time.sleep(0.1)
                            i+=1


                        
                        input_selector = 'input[aria-label="Price"]'
                        wait = WebDriverWait(driver, 10)
                        
                        input_element = wait.until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, input_selector))
                        )

                        # # `value` niteliğindeki mevcut değeri al
                        mevcut_deger_str = input_element.get_attribute("value")
                        print("price ",mevcut_deger_str)
                    except:
                        print("didnt clicked last price")
                
                    
                        """ Since the order is given by proxy request, price information is not entered."""
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
                        # PRELcount.send_keys("123")# .
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
                        QTY.send_keys(123)

                    except json.JSONDecodeError as e:
                        print(f"didnt writeded Qty value {e}")
                    
            except Exception as e:
                print(f"limit marketing error {e}", )



    print("tl",trade_list)

    if len(trade_list)!=0:

        #If not, check the trade list and execute transactions for the relevant symbol.
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

            # ["c",{"symbol":"-susdt","orderQty":0,"future":0,"price":"","side":1,"type":"1","source":1},lvx,1,identifier,runner_id]
            print("type: ",type(list_of_trade[1]["type"]))
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
                    wait = WebDriverWait(driver, 10)
                    
                    input_element = wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, input_selector))
                    )

                    # # `Get the current value of the `value` attribute
                    mevcut_deger_str = input_element.get_attribute("value")
                    print("price ",mevcut_deger_str)
                except:
                    print("didnt clicked last price")
            
                
                    """ Since the order is given by proxy request, price information is not entered."""
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
                    QTY.send_keys(123)

                except json.JSONDecodeError as e:
                    print(f"didnt writeded Qty value {e}")
                
        except Exception as e:
            print(f"limit marketing error {e}", )
        

        try:

          
            # if list_of_trade[1]["type"]==2:
                
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
                    QTY.send_keys(123)

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

    


def first_configuration(pair,margin,levaregeX,order):
    
    pair=pair+"-susdt"
    driver = open_browser.driver
    driver.execute_script("window.open('');")
    all_tabs = driver.window_handles
    driver.switch_to.window(all_tabs[-1])
    driver.get(f"https://www.bydfi.com/en/swap/demo?id={pair}")#This tab will be the 1st tab where open businesses will be checked. It will be in the 0th index.
    wait = WebDriverWait(driver, 15)


    
    
    """ set leverage and margin"""
       
    try:

        #click x button 
        clickX = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'.trade-toolbar-wrap .swap-guide-step-2 > div > div')))
        clickX.click()
    except json.JSONDecodeError as e:
        print(f"didnt clicked X button {e}")

    try:
        # #select cross or isolated
        if(margin=="c"):                                                    #/html/body/div[2]/div/div[2]/div/div[2]/div[1]/div/div/div[2]/div[1]/div[1]/div[1]
                                                                            #/html/body/div[9]/div/div[2]/div/div[2]/div[1]/div/div/div[2]/div[1]/div[1]/div[1]
            clickCROSS = wait.until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[2]/div/div[2]/div/div[2]/div[1]/div/div/div[2]/div[1]/div[1]/div[1]')))
               
            #clickCROSS = wait.until(EC.element_to_be_clickable((By.XPATH,"//div[text()='Cross']")))
            clickCROSS.click()
        
        if(margin=="i"):
            # clickisolated = wait.until(EC.element_to_be_clickable((By.XPATH,'./html/body/div[8]/div/div[2]/div/div[2]/div[1]/div/div/div[2]/div[1]/div[1]/div[2]')))
            # clickisolated.click()                                         #/html/body/div[9]/div/div[2]/div/div[2]/div[1]/div/div/div[2]/div[1]/div[1]/div[2]
                                                                            #/html/body/div[2]/div/div[2]/div/div[2]/div[1]/div/div/div[2]/div[1]/div[1]/div[2]
            clickisolated = wait.until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[2]/div/div[2]/div/div[2]/div[1]/div/div/div[2]/div[1]/div[1]/div[2]')))
               
            #clickisolated = wait.until(EC.element_to_be_clickable((By.XPATH,"//div[text()='Isolated']")))
            clickisolated.click()
        #"body > div:nth-child(12) > div > div.ant-modal-wrap.ant-modal-centered > div > div.ant-modal-content > div.ant-modal-body > div > div > div.jsx-3434185282.swap-common-modal-content-component.hide-scroll-bar > div.jsx-1884500109.margin-type-modal > div.jsx-1884500109.buttons > div.jsx-1884500109.active"
    except json.JSONDecodeError as e:
        print(f"didnt clicked cross or isolated {e}")

    time.sleep(3)
    """ set limit and market"""
    try:
        print("order: ",order)
        print("order type: ",type(order))
        if order=="l":   
            print("in l")

            try:

                #click market button 
                clicklimit = wait.until(EC.element_to_be_clickable((By.XPATH,'//*[@id="swap-layout-desktop"]/div[3]/div[2]/div[1]/div[2]/div[1]/div[1]')))
                clicklimit.click()
            except json.JSONDecodeError as e:
                print(f"didnt clicked Market button {e}")

            """
            order_type: "Limit" veya "Market"
            """
            # order_type="Limit"
            # wait = WebDriverWait(driver, 10)

            # # Tüm butonları bul
            # options = wait.until(
            #     EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.jsx-196929547.option"))
            # )

            # for opt in options:
            #     if opt.text.strip().lower() == order_type.lower():
            #         opt.click()
            #         print(f"{order_type} clicked ✅")
                    

            
            # click_limit1 = wait.until(EC.element_to_be_clickable((By.XPATH,"//div[text()='Limit']")))
            # click_limit1.click()
            # try:
            #     click_limit = wait.until(EC.element_to_be_clickable((By.XPATH,'//*[@id="swap-layout-desktop"]/div[3]/div[2]/div[1]/div[2]/div[1]/div[1]')))
               
            #     #clickCROSS = wait.until(EC.element_to_be_clickable((By.XPATH,"//div[text()='Cross']")))
            #     click_limit.click()

            # except:
            #     print("ee1")


            
                                                  #//*[@id="swap-layout-desktop"]/div[3]/div[2]/div[1]/div[2]/div[1]/div[1]
                                                                            #//*[@id="swap-layout-desktop"]/div[3]/div[2]/div[1]/div[2]/div[1]/div[1]
            
        
        if order=="m":
            print("in m")

            try:

                #click market button 
                clickmarket = wait.until(EC.element_to_be_clickable((By.XPATH,'//*[@id="swap-layout-desktop"]/div[3]/div[2]/div[1]/div[2]/div[1]/div[2]')))
                clickmarket.click()
            except json.JSONDecodeError as e:
                print(f"didnt clicked Market button {e}")

            # order_type="Market"
            # wait = WebDriverWait(driver, 10)

            # # Tüm butonları bul
            # options = wait.until(
            #     EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.jsx-196929547.option"))
            # )

            # for opt in options:
            #     if opt.text.strip().lower() == order_type.lower():
            #         opt.click()
            #         print(f"{order_type} clicked ✅")

            # click_market1 = wait.until(EC.element_to_be_clickable((By.XPATH,"//div[text()='Market']")))
            # click_market1.click()
            # # clickisolated = wait.until(EC.element_to_be_clickable((By.XPATH,'./html/body/div[8]/div/div[2]/div/div[2]/div[1]/div/div/div[2]/div[1]/div[1]/div[2]')))
            # # clickisolated.click()                                         #//*[@id="swap-layout-desktop"]/div[3]/div[2]/div[1]/div[2]/div[1]/div[2]
            # try:
            #     click_market = wait.until(EC.element_to_be_clickable((By.XPATH,'//*[@id="swap-layout-desktop"]/div[3]/div[2]/div[1]/div[2]/div[1]/div[2]')))
               
            #     #clickisolated = wait.until(EC.element_to_be_clickable((By.XPATH,"//div[text()='Isolated']")))
            #     click_market.click()

            # except:
            #     print("ee")

            

    except:
        print("limit or market didint clicked")

    # #write X size    
    # time.sleep(0)
    try:
        LVX = wait.until(                              #/html/body/div[2]/div/div[2]/div/div[2]/div[1]/div/div/div[2]/div[3]/div/div[1]/input
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
        LVX.send_keys(int(levaregeX))
                                                                        #/html/body/div[2]/div/div[2]/div/div[2]/div[1]/div/div/div[3]/div
        try:
            clickCONFRM = wait.until(EC.element_to_be_clickable((By.XPATH,"//div[text()='Confirm']")))
            clickCONFRM.click()#jsx-3418843714 trade-base-button jsx-3434185282 confirm

        except:
            print("click 1 Confirm error")
            try:
                clickCONFRM = wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[2]/div/div[2]/div/div[2]/div[1]/div/div/div[3]/div")))
                clickCONFRM.click()#jsx-3418843714 trade-base-button jsx-3434185282 confirm
            except:
                print("click 2 Confirm error")
            
        
        
        
    except json.JSONDecodeError as e:
        print(f"didnt sended x value or clicked confirm button {e}")
    
    
    
    
    



def market_reaction():
    """ check orders price function"""
    driver = open_browser.driver

    # all_tabs = driver.window_handles
    # driver.switch_to.window(all_tabs[1])
    driver.get(f"https://www.bydfi.com/en/swap/demo?id=ssol-susdt")
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
    
    """ spare, get price section
    try:


        # List all prices
        # We define the common XPath of price elements
        # This XPath is the most appropriate option according to the HTML structure you provided.
        xpath = "//div[contains(@class, 'edit-order-item')]"#ant-table-cell
        
        # XPath eşleşen tüm elemanları liste halinde bulur.
        price_elements = driver.find_elements(By.XPATH, xpath)
        
        # If no element is found, it informs the user.
        if not price_elements:
            print("No price element was found with the specified XPath.")
            return

        print(f"Toplam {len(price_elements)} Number of price elements found. Prices:")
        all_prices = []
    
        # Gets the text of all elements and adds them to a list
        for element in price_elements:
            price_text = element.text.split('\n')[0].strip()
            all_prices.append(price_text)

        grouped_prices = []
        
        # Processes each element as a group of three
        for i in range(0, len(all_prices), 3):
            # Prevents an error if there is a missing element at the end of the list
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


    # # A general XPath expression to find all table rows
    # try:
    #     rows_xpath = '//*[@id="swap-layout-desktop"]/div[3]/div[1]/div[2]/div/div[3]/div/div[2]/div/div/div/div/div[2]/table/tbody/tr'
    #     try:
    #         wait = WebDriverWait(driver, 10)
            
    #         # find all row elements
    #         all_rows = wait.until(EC.presence_of_all_elements_located((By.XPATH, rows_xpath)))
            
    #         print(f"Toplam {len(all_rows)} number of rows found.")
            
    #         all_table_data = [] # Master list to store all table data
            
    #         # Looping for each row (tr)
    #         for i, row_element in enumerate(all_rows):
    #             row_data = [] # Temporary list to store cell data in this row
                
    #             # Find all td tags 
    #             cell_elements = row_element.find_elements(By.TAG_NAME, 'td')
                
    #             #Add the text content of each cell to the row data list
    #             for cell in cell_elements:
    #                 row_data.append(cell.text.strip())
                
    #             # Add the data in this row to the main list
    #             all_table_data.append(row_data)

    #         #print("all data:",all_table_data)
    #         market_revise(all_table_data)
    #     except Exception as e:
    #         print(f"An error occurred while retrieving table data: {e}")
    #         return None
    # except:
    #     print("didnt getted prices7")
    # # price processing will be done here, the transaction will be made between the price and the live price and the resulting price will be printed below
   
    #market_revise(open_browser.order_main_list)
    




def market_revise(order_list):
    """
   Extracts data from the given list format and assigns it to meaningful variables.

    Args:
    order_list: A list containing cell data retrieved from the table.

    Returns:
    A list of dictionaries and a checklist containing the extracted data for each order.
    """
    # Define price variables but not assign values
    Op, Hp, Lp, Cp = None, None, None, None

    # get price values
    for _ in range(5): # only 5 
        open_price, high_price, low_price, close_price = asyncio.run(swap_open_close_values_From_websocket.receive_bydfi_data_once())
        
        # If a value is received, break the loop
        if open_price is not None or  high_price is not None or  low_price is not None or  close_price is not None:
            Op, Hp, Lp, Cp = open_price, high_price, low_price, close_price
            break
    
    if Cp is None:
        print("Error: Could not get a valid closing price from WebSocket.")
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
            print(f"Error: Invalid price value '{order_details['price']}'. miss this line.")
            order_check_list_main.append([])
            continue
        threshold_small = 0.05
        threshold_medium = 0.10
        threshold_large = 0.20
        if order_details["trade_type"] == "Sell":#The order price must be slightly lower than the market price. S 12, P 11 S->11.5
            price_diff = order_price_float - Cp
            print(price_diff)
            #Sort conditions from largest to smallest
            #   9.98                10     -0.02 transation true
            #   10.2                10      0.02  transation false
            if order_price_float - Cp > threshold_large:
                order_check_list.append(Cp-0.05)# check
                order_check_list.append("--")# check
            elif order_price_float - Cp > threshold_medium:
                order_check_list.append(Cp-0.05)# check
                order_check_list.append("-")# check
            elif order_price_float - Cp > threshold_small:
                order_check_list.append(Cp-0.05)# check
                order_check_list.append("0")# check
            elif order_price_float - Cp<=0:
                order_check_list.append(Cp-0.05)# check
                order_check_list.append("00")# check

        elif order_details["trade_type"] == "Buy":#Order price must be slightly higher than market price.
            price_diff = Cp - order_price_float
            print(price_diff)
            # Sort the conditions from largest to smallest and edit the operator

            #    10.2               10  0.2 transation true 
            #    9.98               10  -0.2 transation false

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
   Clicks the icon in the 6th column of each row of the table at the specified XPath.
    
    Args:
        driver: Selenium WebDriver object.
    """
    try:
        # all table and rows main XPath
                    #//*[@id="swap-layout-desktop"]/div[2]/div[1]/div[2]/div/div[3]/div/div[2]/div/div/div/div/div[2]/table/tbody/tr[3]/td[6]/div/span/svg/path[2]
        rows_xpath = '//*[@id="swap-layout-desktop"]/div[2]/div[1]/div[2]/div/div[3]/div/div[2]/div/div/div/div/div[2]/table/tbody/tr'
        driver = open_browser.driver
        wait = WebDriverWait(driver, 10)
        
        # Tüm satır elementlerini bul
        all_rows = wait.until(EC.presence_of_all_elements_located((By.XPATH, rows_xpath)))
        
        print(f"Toptotal {len(all_rows)} aNumber of rows found. Clicking on the icon in each row...")
        
        # a loob each row
        for i, row_element in enumerate(all_rows):
            # dynamic XPath 
            # tr's index starts at 1, so i+1 is used.
            #  td[6] targets column 6, and div/span/svg/* targets the icon inside.
            icon_xpath = f'//*[@id="swap-layout-desktop"]/div[2]/div[1]/div[2]/div/div[3]/div/div[2]/div/div/div/div/div[2]/table/tbody/tr[{i+1}]/td[6]/div/span/svg/path[2]'
            
            try:
                #Find the icon element and click it
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
                # In case of error, the loop continues, trying all lines.
    except Exception as e:
        print(f"Tablo verileri çekilirken bir hata oluştu: {e}")




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
       Clicks the icon in the 6th column of each row of the table in the specified XPath.

        Args:
        driver: Selenium WebDriver object.
        """
        # print("for i in order_main_list start")
        try:
            #Generic XPath to find all table rows
                        #//*[@id="swap-layout-desktop"]/div[2]/div[1]/div[2]/div/div[3]/div/div[2]/div/div/div/div/div[2]/table/tbody/tr[3]/td[6]/div/span/svg/path[2]
            rows_xpath = '//*[@id="swap-layout-desktop"]/div[2]/div[1]/div[2]/div/div[3]/div/div[2]/div/div/div/div/div[2]/table/tbody/tr'
            driver = open_browser.driver
            wait = WebDriverWait(driver, 10)
            # print("for i in order_main_list")
            range_list=len(open_browser.order_main_list)
            print("range list ",range_list)
            i=0
            print("open broser order main list: ",open_browser.order_main_list)
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
                    print(f"check_price_value function error {e}")

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
                        # 1. find element                                           #//*[@id="swap-layout-desktop"]/div[3]/div[1]/div[2]/div/div[3]/div/div[2]/div/div/div/div/div[2]/table/tbody/tr[2]/td[6]/div/span
                        element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="swap-layout-desktop"]/div[3]/div[1]/div[2]/div/div[3]/div/div[2]/div/div/div/div/div[2]/table/tbody/tr[2]/td[6]/div/span')))
                        
                        # 2. Use JavaScript to bring the element into viewport
                        driver.execute_script("arguments[0].scrollIntoView(true);", element)
                        
                        # 3.Wait again to make sure the element is clickable
                        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="swap-layout-desktop"]/div[3]/div[1]/div[2]/div/div[3]/div/div[2]/div/div/div/div/div[2]/table/tbody/tr[2]/td[6]/div/span')))
                        
                        # 4. click
                        element.click()
                        time.sleep(1)
                    except json.JSONDecodeError as e:
                        print(f"click error1 {e}")

                    # try:
                    #     # 2.Define the XPath of the input field
                    #     input_xpath = '//div[contains(@class, "trade-view-input")]/input'
                        
                    #     # 3.Wait for the element to exist in the DOM (not necessarily clickable)
                    #     price_input = wait.until(EC.presence_of_element_located((By.XPATH, input_xpath)))
                        
                    #     # 4.Enter the value directly using JavaScript
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
                        # print("licked confirim button.")

                    except Exception as e:
                        print(f"An error occurred while entering the price: {e}")    
                    print("price  configired")
            
        except Exception as e:
            print(f"click error2")
    except json.JSONDecodeError as e:
        print("fin row error {e}")
def run_async(coro):
    """
    Helper: Run async coroutine in synchronous context
    """
    try:
        loop = asyncio.get_running_loop()  # if loop already started
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
       # If an event loop is already running,
        # you need to open a new task and wait for the result.
        return asyncio.run_coroutine_threadsafe(coro, loop).result()
    else:
        # 
        return asyncio.run(coro)

def check_price_value(symbol,side,price):
    try:
        try:
            
            for a in range(5): # 5 loob
                
                try:
                    # open_price, high_price, low_price, close_price = run_async(
                    #     swap_open_close_values_From_websocket.receive_bydfi_data_once(symbol)
                    # )
                    open_price, high_price, low_price, close_price = asyncio.run(swap_open_close_values_From_websocket.receive_bydfi_data_once(symbol))
                except:
                    print("getting price error")
                # If a value is received, break the loop
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
                    last_two_val = int(last_two) / 4000  # 2-digit decimal value

                    new_price = Cp - last_two_val
                    return ["flag=1", new_price]
                except json.JSONDecodeError as e:
                    print(f"sell price didint configuret {e}")
                    return ["flag=1", price]
            elif Cp - price > 0:
                print("price under the target")
                return ["flag=0", Cp]  # You can return to Cp or price as fallback
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








def parse_positions(json_data):
    """
    Parses and prints position information in incoming JSON data.

    Args:
    json_data (str): Position data in JSON format.
    """
    try:
        # Convert JSON string to Python dictionary
        data = json.loads(json_data)

        # Check if there is a list under the "data" key
        if "data" in data and isinstance(data["data"], list):
            positions = data["data"]
            
            # Loop through each position
            for i, position in enumerate(positions):
                print(f"--- Pozisyon #{i+1} için Veriler ---")
                
                # Print each variable
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
            print("Key 'data' or list format not found in JSON data.")

    except json.JSONDecodeError as e:
        print(f"Error while parsing JSON data: {e}")


def parse_orders(json_data):
    """
    Parses and prints order information from incoming JSON data.

    Args:
    json_data (str): Order data in JSON format.
    """
    try:
        # Convert JSON string to Python dictionary
        data = json.loads(json_data)

        # Check if there is a list under the "data" key
        if "data" in data and isinstance(data["data"], list):
            orders = data["data"]
            
            # Loop through each order
            for i, order in enumerate(orders):
                print(f"--- Data for Order #{i+1} ---")
                
                # Safely retrieve and print each variable
                order_id = order.get('orderId')
                symbol = order.get('symbol')
                volume = order.get('volume')
                price = order.get('price')
                side = order.get('side')
                status = order.get('status')
                
                print(f"order ID: {order_id}")
                print(f"Sembol: {symbol}")
                print(f"volum: {volume}")
                print(f"price: {price}")
                print(f"Direction (1: Buy, 2: Sell): {side}")
                print(f"Status (1: Pending, 2: Partially Full, 3: Full): {status}")
                
                print("-" * 30)
                
        else:
            print("JSON verisinde 'data' anahtarı veya liste formatı bulunamadı.")

    except json.JSONDecodeError as e:
        print(f"Error while parsing JSON data: {e}")