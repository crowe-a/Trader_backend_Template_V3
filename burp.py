1-cross,limit,qty,long
#side=1 long
#side=2 short
#cross-isoalted seçimi manuel yapılacak
# future=0 sadece limit işlemlerde var,
# market== type=2
# limit== type=1

#manuel yapılacaklar, ilk olarak cross ve isolated için birer tab açılıp , ilk ayarlar yapılacak. ardından
# trade isteği tipine göre listedeki işlemlere göre veri eklemesi yapılacak
# symbol,ordrqty,future?,price,side,type,source

req-{"symbol":"sxrp-susdt","orderQty":123,"future":0,"price":"2.9885","side":1,"type":"1","source":1}

res-{"code":200,"message":"","data":{"orderId":"9098147283178031103","hasCancelPopup":false}}

req-POST /testnet/private/future/order/otoco HTTP/2
res-


2-cross,limit,qty,short
req-{"symbol":"sxrp-susdt","orderQty":125,"future":0,"price":"2.9878","side":2,"type":"1","source":1}
res-{"code":200,"message":"","data":{"orderId":"9098147454976722023","hasCancelPopup":false}}

req-POST /testnet/private/future/order/otoco HTTP/2
res-

3-isolated,lim,t,qty,long

req-{"symbol":"sxrp-susdt","orderQty":122,"future":0,"price":"2.9878","side":1,"type":"1","source":1}
res-{"code":200,"message":"","data":{"orderId":"9098147970372802016","hasCancelPopup":false}}

4- isolated,lim,qty,short
req-{"symbol":"sxrp-susdt","orderQty":123,"future":0,"price":"2.9878","side":2,"type":"1","source":1}
res-{"code":200,"message":"","data":{"orderId":"9098148073452018238","hasCancelPopup":false}}



5- cross,market,qty,long
req-{"symbol":"sxrp-susdt","orderQty":1230,"side":1,"type":"2","source":1}
res-{"code":200,"message":"","data":{"orderId":"9098148382689659751","hasCancelPopup":false}}


6- cross,market,qty,short
req-{"symbol":"sxrp-susdt","orderQty":12,"side":2,"type":"2","source":1}
res-{"code":200,"message":"","data":{"orderId":"9098148554488350412","hasCancelPopup":false}}

7-isolated,market,qty,long
req-{"symbol":"sxrp-susdt","orderQty":11,"side":1,"type":"2","source":1}
res-{"code":200,"message":"","data":{"orderId":"9098148657567564475","hasCancelPopup":false}}

8-isolated,market,qty,short

req-{"symbol":"sxrp-susdt","orderQty":11,"side":2,"type":"2","source":1}
res-{"code":200,"message":"","data":{"orderId":"9098148760646780631","hasCancelPopup":false}}

