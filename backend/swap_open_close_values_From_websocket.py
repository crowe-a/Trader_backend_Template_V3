import asyncio
import websockets
import json

async def receive_bydfi_data_once(pair):
    """
    Connects to the WebSocket, gets one set of data (OHLC), and then closes the connection.
    """
    
    uri = "wss://fquote.bydfi.pro/wsquote"
    if pair=="sxrp-susdt":
        pairnew="XRP-USDT"

    elif pair=="ssol-susdt":
        pairnew="SOL-USDT"
    pairnew="SOL-USDT"
    subscription_message = json.dumps({
        "cmid": "4001",
        "symbols": pairnew,
        "r": 1,
        "data": "24"
    })
    #print("trying to getting pair websocker connection")
    try:
        async with websockets.connect(uri) as websocket:
            #print("[fquote WebSocket connected]...")
            await websocket.send(subscription_message)
            #print("Subscription message sent.")
            
            # Wait for a single message from the server
            message = await websocket.recv()
            
            try:
                data = json.loads(message)
                
                if "data" in data and isinstance(data["data"], str):
                    inner_data = json.loads(data["data"])
                    jss = json.dumps(inner_data)
                    
                    try:
                        data = json.loads(jss)
                        price_value = data.get("price")
                        close_value = data.get("c")
                        open_value = data.get("o")
                        high_value = data.get("h")
                        low_value = data.get("l")
                        
                        # Return the values and the function will exit
                        return open_value, high_value, low_value, close_value
                    
                    except json.JSONDecodeError:
                        print("Internal data is not in JSON format.")
            
            except json.JSONDecodeError:
                print("The incoming message is not in JSON format.")
                
    except websockets.exceptions.ConnectionClosed as e:
        print(f"Connection closed. Code: {e.code}, Reason: {e.reason}")
    except Exception as e:
        print(f"An error occurred while connecting: {e}")
        
    return None, None, None, None

# # Run the asynchronous function and get the returned values
# if __name__ == "__main__":
#     open_price, high_price, low_price, close_price = asyncio.run(receive_bydfi_data_once())
    
#     if open_price is not None:
#             print("\n--- Received Data ---")
#             print(f"Opening Price: {open_price}")
#             print(f"Highest Price: {high_price}")
#             print(f"Lowest Price: {low_price}")
#             print(f"Closing Price: {close_price}")
#     else:
#         print("Data could not be retrieved.")