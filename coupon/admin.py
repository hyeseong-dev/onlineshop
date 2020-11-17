from django.contrib import admin
from .models import Coupon

class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'use_from','use_to','amount','active']
    list_filter = ['active', 'use_from', 'use_to']
    search_fields = ['code']

admin.site.register(Coupon, CouponAdmin) # 다른 방법으로는 class Coupon~위에 '@admin.register(Coupon)'을 사용할 수 있다.



