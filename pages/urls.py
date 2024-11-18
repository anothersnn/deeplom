from django.urls import path
from numpy import product
from . import views
import product.views

urlpatterns = [
    path('shops/', views.home_page_view, name = 'home'),
    path('', views.all_products, name = 'all_products'),
    path('success/', views.success_view, name='success'),  
    path('cancel/', views.cancel_view, name='cancel'),     
    path('help/', views.help_page_view , name = 'help'),
    path('basket/', views.basket_page_view, name = 'basket'),
    path('contents/', views.contents_page_view, name = 'contents'),
    path('update_item/', product.views.updateItem, name = "update_item"),
     
    path('cheapest_price/', views.cheapest_price_view, name = 'cheapest_price'),
    path('product/<int:product_id>/', views.product_detail_view, name='product_detail'),
    path('get_client_token/', views.get_client_token, name='get_client_token'),
    path('process_payment/', views.process_payment, name='process_payment'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-cancel/', views.payment_cancel, name='payment_cancel'),
]