import requests

from django.conf import settings                # import API의 key, secret을 가져오기 위함임

# iamport 에서 토큰을 얻어옴
def get_token():
    access_data = {
        'imp_key': settings.IAMPORT_KEY,
        'imp_secret': settings.IAMPORT_SECRET
    }

    url = "https://api.iamport.kr/users/getToken" # import 메뉴얼에 명시되어 있는 주소
    # requests : 특정 서버와 http통신을 하게 해주는 모듈
    req = requests.post(url,data=access_data) # post 메소드를 통해서 서버에 접속하여 데이터를 받아오도록 요청함
    access_res = req.json()                   # requests 객체의 json 메소드 이용 

    if access_res['code'] is 0: # 0 일때는 제대로 응답요청이 왔음을 의미함. 그리고 'code'는 html의 'code'가 아닌 API에서 가져온 'code'임 마치 동명이인임.
        return access_res['response']['access_token']
    else:
        return None

# 결제할 준비를 하는 함수 - iamport 에 주문번호와 금액을 미리 전송
def payments_prepare(order_id,amount,*args,**kwargs):
    access_token = get_token()
    if access_token:
        access_data = {
            'merchant_uid':order_id, #우리가 설정한 것임, 유니크하게 만들 것임
            'amount':amount          # 얼마 주문할 거임?
        }

        url = "https://api.iamport.kr/payments/prepare"
        headers = {
            'Authorization':access_token        # 토큰 없이 접속 하면 401, 402 에로 코드가 발생할 것임
        }
        req = requests.post(url, data=access_data, headers=headers)
        res = req.json()

        if res['code'] is not 0: # 동일한 표현식으로 "if res['code'] != 0:" 사용하기도함
            raise ValueError("API 통신 오류")
    else:
        raise ValueError("토큰 오류")

# 결제가 이루어졌음을 확인해주는 함수 - 실 결제 정보를 iamport에서 가져옴
def find_transaction(order_id, *args, **kwargs):
    access_token = get_token()
    if access_token:
        url = "https://api.iamport.kr/payments/find/"+order_id

        headers = {
            'Authorization':access_token
        }

        req = requests.post(url, headers=headers)
        res = req.json()

        if res['code'] is 0:        # <-- 동일하게 if res['code'] == 0: 로 쓸수 있음
            context = {
                'imp_id':res['response']['imp_uid'],
                'merchant_order_id':res['response']['merchant_uid'],
                'amount':res['response']['amount'],
                'status':res['response']['status'],
                'type':res['response']['pay_method'],
                'receipt_url':res['response']['receipt_url']
            }
            return context
        else:
            return None
    else:
        raise ValueError("토큰 오류")