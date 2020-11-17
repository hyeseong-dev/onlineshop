from django.shortcuts import redirect
from django.utils import timezone # 사용기한에 대한 평가는 datetime으로 할 경우 각자의 컴퓨터 시간으로 읽을 우려가 있음.(서버에 접속한 사람의 국가에 맞게 적용됨)
from django.views.decorators.http import require_POST

from .models import Coupon
from .forms import AddCouponForm

@require_POST
def add_coupon(request):
    now = timezone.now()
    form = AddCouponForm(request.POST) # 간단하게는 request.POST.get('')으로 할 수 있지만 보안에 취약하고 장고의 권고!로 cleaned_data 이용을 함!
    if form.is_valid():
        code = form.cleaned_data['code']

        try:
            coupon = Coupon.objects.get(code__iexact=code, use_from__lte=now, use_to__gte=now, active=True)
                                        # ieaxact : 대소문가 No 구분 < -> exact : 대소문자 구분함 
                                        # lte(less thatn equal)now보다 작거나 같고 
                                        # gte(greater than equal) now 보다 크거나 같다
                                        # active 사용할 수 있는 상태의 데이터만 가져옴.
            request.session['coupon_id'] = coupon.id
        except Coupon.DoesNotExist:     # get 방식일 경우 발생함
            request.session['coupon_id'] = None
    return redirect('cart:detail')      # 쿠폰에 넣는 행위(유표하든 안하든)를 하면 다시 redirect하게됨
