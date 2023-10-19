from django.urls import path, include
from rest_framework.routers import DefaultRouter

from backend.views import RegisterAccountView, ConfirmAccountView, LoginAccountView, ContactView, \
    AccountDetails, PartnerUpdateURL, PartnerUpdateFILE, PartnerState, CategoryView, ShopView, \
    ProductInfoView, BasketView, OrderView, PartnerOrders

app_name = 'backend'

router = DefaultRouter()

router.register(r'user/contact', ContactView, basename='contact')
urlpatterns = [
    path('user/register', RegisterAccountView.as_view(), name='user-register'),
    path('user/register/confirm', ConfirmAccountView.as_view(), name='user-register-confirm'),
    path('user/login', LoginAccountView.as_view(), name='user-login'),
    path('user/details', AccountDetails.as_view(), name='user-details'),
    path('partner/update/url', PartnerUpdateURL.as_view(), name='partner-update-url'),
    path('partner/update/file', PartnerUpdateFILE.as_view(), name='partner-update-file'),
    path('partner/state/<int:pk>', PartnerState.as_view(), name='partner-state'),
    path('partner/orders', PartnerOrders.as_view(), name='partner-orders'),
    path('categories', CategoryView.as_view(), name='categories'),
    path('shops', ShopView.as_view(), name='shops'),
    path('products', ProductInfoView.as_view(), name='products'),
    path('basket', BasketView.as_view(), name='basket'),
    path('order', OrderView.as_view(), name='order'),
    path('', include(router.urls)),
]
