import requests,time

# # start bot
# r=requests.post("http://127.0.0.1:8000/start_stop", json={"action": "start"})

# # #stop bot
# r=requests.post("http://127.0.0.1:5000/start_stop", json={"action": "stop"})


def stop():
    r=requests.post("http://127.0.0.1:8000/start_stop", json={"action": "stop",})
    print(r.status_code)  # 200
    print(r.json())  

def run_withdummy():
    # print(r.status_code)  # 200
    # print(r.json())  
    r=requests.post("http://127.0.0.1:8000/start_stop", json={"action": "start"})
    flag=100
    while flag:
        time.sleep(1)
        print(r.status_code)  # 200
        print(r.json())  
        if r.status_code==200:
            flag=1
            break
        if r.status_code==400:
            flag=0


    config_js={#sxrp-susdt
                "action": "configure",
                "Runner_id":"1",

                
                "amount": "1000",
                "Tr":"0.2" , 
                "margin":"cross",
                "leverage":"20",
                "symbol": "sxrp-susdt",
                "market_type": "Limit",
                
                "Tick_Size":"10" , 
                "order_expiry":"5"
                
                }


    config=requests.post("http://127.0.0.1:8000/configure", json=config_js)
    flag1=100
    while flag1:
        time.sleep(1)
        print(config.status_code)
        print(config.json())
        if config.status_code==200:
            flag1=1
            break
        if config.status_code==400:
            flag1=0

    config_js2={#ssol-susdt
                "action": "configure",
                "Runner_id":"2",

                
                "amount": "1000",
                "Tr":"0.2" , 
                "margin":"isolated",
                "leverage":"10",
                "symbol": "ssol-susdt",
                "market_type": "Limit",
                
                "Tick_Size":"10" , 
                "order_expiry":"5"
                
                }


    config2=requests.post("http://127.0.0.1:8000/configure", json=config_js2)
    flag2=100
    while flag2:
        time.sleep(1)
        print(config2.status_code)
        print(config2.json())
        if config2.status_code==200:
            flag2=1
            break
        if config2.status_code==400:
            flag2=0





