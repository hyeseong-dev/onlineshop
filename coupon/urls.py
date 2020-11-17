from django.urls import path
from .views import add_coupon

app_name='coupon'

urlpatterns = [
    path('add/', add_coupon, name='add'),   # 만약 name = 'add'가 cart앱의 add와 겹치게 될 경우 구분되는 것은 결국 app_name으로 구분하게되는 거임
]