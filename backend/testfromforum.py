# pip install requests
import requests
import time
 
from backend.config import EMAIL,PASSWORD,CAPSOLVER_API_KEY
api_key = CAPSOLVER_API_KEY # TODO: your api key of capsolver
 
 
def capsolver(CPID):
    payload = {
        "clientKey": api_key,
        "task": {
            "type": 'GeeTestTaskProxyLess',
            "websiteURL": "https://www.bydfi.com/tr/login",  # page url of your site
            #"gt": "...",  # v3 is required
            #"challenge":   "...",  # v3 is required
            "captchaId":   CPID,  # v4 is required
        }
    }
    res = requests.post("https://api.capsolver.com/createTask", json=payload)
    resp = res.json()
    task_id = resp.get("taskId")
    if not task_id:
        print("Failed to create task:", res.text)
        return
    print(f"Got taskId: {task_id} / Getting result...")
 
    while True:
        try:

            time.sleep(1)  # delay
            payload = {"clientKey": api_key, "taskId": task_id}
            res = requests.post("https://api.capsolver.com/getTaskResult", json=payload)
            resp = res.json()
            status = resp.get("status")
            if status == "ready":
                time.sleep(1)
                return resp.get("solution")
                
            if status == "failed" or resp.get("errorId"):
                print("Solve failed! response:", res.text)
                return
            print(resp)
            break
        except:
            print("capsolver error")
        time.sleep(1)
