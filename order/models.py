from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from coupon.models import Coupon
class Order(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    address = models.CharField(max_length=250)
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False)

    coupon = models.ForeignKey(Coupon, on_delete=models.PROTECT, related_name='order_coupon', null=True, blank=True)
    discount = models.IntegerField(default=0, validators=[MinValueValidator(0),MaxValueValidator(100000)])

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f'Order {self.id}'

    def get_total_product(self):
        return sum(item.get_item_price() for item in self.items.all()) 
        # 바로 위 self.items는 orderItem 클래스의 멤버 변수의 order의 related_name으로 지정된 명칭임!
        # get_item_price()는 44줄에 작성된 메소드를 가져와서 호출한거임
    def get_total_price(self):
        total_product = self.get_total_product()
        return total_product - self.discount # self.discount는 order 클래스의 전역변수에서 가져온거임


from shop.models import Product
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_products')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return '{}'.format(self.id)

    def get_item_price(self):
        return self.price * self.quantity

import hashlib
from .iamport import payments_prepare, find_transaction # 주문 버튼을 눌렀을때 그 결제에 대한 정보를 DB에 넣어 레코드로 만들어 둠
# 결제전 이미 결제 전이라는 상태값을 DB에 두고 결제를 하게 되면 결제가 된 상태값으로 변경시켜둠 

# order에 관한 결제정보를 품고 있는 OrderTransactionManager, OrderTransaction 클래스 생성을 함.
# 장고에서는 DB에 대한 작업은 메소드로 하기 보단 Manager로 할 것을 권고함!관례적 약속

class OrderTransactionManager(models.Manager): # 새로 트랜젝션을 했을때 정보를 갖게함
    def create_new(self,order,amount,success=None,transaction_status=None): # success 인자값은 결제유무에 대한 것임, 여기서 create_new가 호출되면 order와 amount만 가지고 생성됨
        if not order:
            raise ValueError("주문 정보 오류")

            # hashlib 암호화 시키는 녀석. 그중 sha1이란 녀석을 사용함. 사용이유는 유니크한 주문 정보를 만들기 위함임
        order_hash = hashlib.sha1(str(order.id).encode('utf-8')).hexdigest()
        email_hash = str(order.email).split("@")[0]
        final_hash = hashlib.sha1((order_hash  + email_hash).encode('utf-8')).hexdigest()[:10]
        merchant_order_id = "%s"%(final_hash) # 우항은 f'{final_hash}' or str(final_hash) 로도 가능함.

        payments_prepare(merchant_order_id,amount)

        tranasction = self.model(
            order=order,
            merchant_order_id=merchant_order_id,
            amount=amount
        )

        if success is not None:
            tranasction.success = success
            tranasction.transaction_status = transaction_status

        try:
            tranasction.save()
        except Exception as e:
            print("save error",e)

        return tranasction.merchant_order_id

    def get_transaction(self,merchant_order_id): # 매니저에 메소드가 추가 된 것이므로 objects.이라고 부를수 있는 명칭을 지정함
        result = find_transaction(merchant_order_id)
        if result['status'] == 'paid':
            return result
        else:
            return None


class OrderTransaction(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE) # order 정보가 없으면 결제 정보도 사라져야 하므로 CASCADE로 지정
    merchant_order_id = models.CharField(max_length=120, null=True, blank=True) # 사실상 OrderTransactionManager 클래스의 create_new함수의 findal_hash에서 10글자를 잘라냈기에 10글자 혹은 12글자만 해도 충분함.
    transaction_id = models.CharField(max_length=120, null=True,blank=True)     # 결제회사의(예. iamport) PK라고 생각하면됨. 결제취소 수정하기위해선 이 정보를 전달함.
    amount = models.DecimalField(max_digits=10,decimal_places=2) # 이전 클래스 설계에서 Decimal로 통일했기에 PositiveIntegerField보다는 Decimal을 사용함. 국내에만 사용한다면 사실 Decimal 필드는(X) 소수점 자리는 안받음
    transaction_status = models.CharField(max_length=220, null=True,blank=True)
    type = models.CharField(max_length=120,blank=True)
    created = models.DateTimeField(auto_now_add=True) # auto_now=False 인자를 넣어도 되지만 편의상 빼겠음. 

    objects = OrderTransactionManager()

    def __str__(self):
        return str(self.order.id)

    class Meta:
        ordering = ['-created']


# 결제 정보가 생성된 후에 호출할 함수를 연결해준다. 

# 시그널을 사용한다는 것은 모델의 인스턴스가 생성 되기 전, 후 이런때 목적이 있으면 시그널을 만들게됨
# 장고엔 이미 커스텀 시그널이 있음 
# 예를들어 네이버 로그인 API 작업시, 네이버 로그인 이후 무언갈 할 시그널이 존재함
# 즉, 시그널의 목적은 내가 어떤일을 하기 전! 혹은 끝낸 후 명령 신호를 보내는 것임.
def order_payment_validation(sender, instance, created, *args, **kwargs):
    if instance.transaction_id:
        import_transaction = OrderTransaction.objects.get_transaction(merchant_order_id=instance.merchant_order_id) 
        # 커스텀 매니저에서 만든 get_transaction() 메소드

        merchant_order_id = import_transaction['merchant_order_id']
        imp_id = import_transaction['imp_id']
        amount = import_transaction['amount']

        local_transaction = OrderTransaction.objects.filter(merchant_order_id = merchant_order_id, transaction_id = imp_id,amount = amount).exists()

        if not import_transaction or not local_transaction:
            raise ValueError("비정상 거래입니다.")

#  
from django.db.models.signals import post_save
post_save.connect(order_payment_validation,sender=OrderTransaction) # OrderTransaction의 작업이 있을때만 post_save.connect() 작업을 반복적으로 처리함


