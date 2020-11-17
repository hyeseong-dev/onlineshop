"""
컨텍스트 프로세서란 모든 템플릿을 해석할 떄 항상 처리해야하는 정보가 있을 떄 담당하는 기능을 말합니다.
일반적으로 상단 메뉴의 장바구니 정보가 장바구니로 이동했을 때는 보이지만 그 외 다른 페이지 일 떄느 ㄴ보이지 않는 치명적 단점이 있어요. 
이를 컨텍스트 프로세서로 해결할 수 있습니다.

사용법은 settings.py의 TEMPLATES변수에 context_precessors에 등록만 하면 되요.
"""

from .cart import Cart

def cart(request):
    cart = Cart(request)
    return {'cart':cart}