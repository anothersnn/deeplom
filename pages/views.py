from django.shortcuts import get_object_or_404, redirect, render
from product.models import *
from django.db.models import Q
from django.db.models import Max, Sum
from django.http import JsonResponse 
from django.conf import settings
import braintree
import numpy as np
import re
import os
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.preprocessing.text import Tokenizer
import pickle
from .forms import UserRegistrationForm 

def home_page_view(request, *args, **kwargs):
    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer)
        cartTotal = order.orderitem_set.all().aggregate(sum=Sum('quantity'))['sum']
        if cartTotal is None:
            cartTotal = ''
    else:
        cartTotal = ''
    context = {'cartTotal': cartTotal}
    return render(request, "home.html", context)

def help_page_view(request, *args, **kwargs):
    return render(request, "help.html")

def cheapest_price_view(request, *args, **kwargs):
    braintree.Configuration.configure(
        braintree.Environment.Sandbox,
        merchant_id=settings.BRAINTREE_MERCHANT_ID,
        public_key=settings.BRAINTREE_PUBLIC_KEY,
        private_key=settings.BRAINTREE_PRIVATE_KEY,
    )

    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer)
        items = order.orderitem_set.all()
        cart_total_quantity = order.orderitem_set.aggregate(sum=Sum('quantity'))['sum'] or 0
    else:
        items = []
        cart_total_quantity = 0

    total_price = sum(item.get_total for item in items) if items else 0

    if request.method == 'POST' and total_price >= 0.50:
        nonce_from_the_client = request.POST.get('payment_method_nonce')
        store = request.POST.get('store')

        if store == 'tesco':
            total_price = order.get_total_price_tesco
        elif store == 'morrisons':
            total_price = order.get_total_price_morrisons
        elif store == 'waitrose':
            total_price = order.get_total_price_waitrose
        elif store == 'sainsburys':
            total_price = order.get_total_price_sainsburys

        result = braintree.Transaction.sale({
            "amount": str(total_price),
            "payment_method_nonce": nonce_from_the_client,
            "options": {
                "submit_for_settlement": True
            }
        })

        if result.is_success:
            print(f"Transaction ID: {result.transaction.id}")
            return redirect('payment_success')
        else:
            print(f"Transaction failed: {result.message}")
            return render(request, "error.html", {"message": result.message})

    client_token = braintree.ClientToken.generate()

    context = {
        'items': items,
        'cartTotal': cart_total_quantity,
        'order': order,
        'total_price': total_price,
        'client_token': client_token,
    }

    return render(request, "cheapest_price.html", context)

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            Customer.objects.create(user=new_user, name=new_user.username)
            return redirect('login')
    else:
        form = UserRegistrationForm()
    
    context = {'form': form}
    return render(request, 'register.html', context)

def basket_page_view(request, *args, **kwargs):
    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer)
        items = order.orderitem_set.all()
        cart_total_quantity = order.orderitem_set.aggregate(sum=Sum('quantity'))['sum'] or 0
    else:
        items = []
        cart_total_quantity = 0

    total_price = sum(item.get_total for item in items) if items else 0

    if items and total_price < 0.50:
        return render(request, "error.html", {"message": "Минимальная сумма заказа должна быть больше 0.50 USD."})

    if request.method == 'POST' and total_price >= 0.50:
        nonce_from_the_client = request.POST.get('payment_method_nonce')
        
        result = braintree.Transaction.sale({
            "amount": str(total_price),
            "payment_method_nonce": nonce_from_the_client,
            "options": {
                "submit_for_settlement": True
            }
        })

        if result.is_success:
            return redirect('payment_success')
        else:
            return render(request, "error.html", {"message": result.message})

    client_token = braintree.ClientToken.generate()

    context = {
        'items': items,
        'cartTotal': cart_total_quantity,
        'total_price': total_price,
        'client_token': client_token,
    }

    return render(request, "basket.html", context)

def payment_success(request):
    return render(request, "success.html")

def payment_cancel(request):
    return render(request, "cancel.html")

def contents_page_view(request,*args, **kwargs):
   
    if 'q' in request.GET:
        q = request.GET['q']
        products = Product.objects.filter(Q(name__icontains=q) | Q(store__icontains=q) | Q(category__icontains=q) |Q(description__icontains=q))
    else:
        products = Product.objects.all()

    if 'min_price' in request.GET or 'max_price' in request.GET:
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')

        if min_price == '':
            min_price = 0
        if max_price == '':
            max_price = Product.objects.all().aggregate(Max('price'))
            max_price = max_price.get('price__max')

        products = products.filter(price__range=(min_price, max_price))

    tesco = request.GET.get('Tesco')
    morrisons = request.GET.get('Morrisons')
    waitrose = request.GET.get('Waitrose')
    sainsburys = request.GET.get("Sainsburys")
    stores_to_display = set()

    if tesco:
        stores_to_display.add('Tesco')
    if morrisons:
        stores_to_display.add('Morrisons')
    if sainsburys:
        stores_to_display.add('Sainsburys')
    if waitrose:
        stores_to_display.add('Waitrose')

    if not stores_to_display:
        pass
    else:
        products = products.filter(store__in=stores_to_display)

    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer)
        items = dict(order.orderitem_set.all().values_list('product_id', 'quantity'))
        cartTotal = order.orderitem_set.all().aggregate(sum=Sum('quantity'))['sum']
        if cartTotal is None:
            cartTotal = ''
    else:
        items = []
        cartTotal = ''
    
    context ={'products' : products.order_by('name', 'price'), 'items' : items, 'cartTotal' : cartTotal}
    
    return render(request, "contents.html", context)


 
# with open('tokenizer.pickle', 'rb') as handle:
#     tokenizer = pickle.load(handle)

tokenizer = Tokenizer()

 
# graph = tf.Graph()

 
def predict_sentiment(text):
    # Преобразование текста в последовательность чисел с использованием Tokenizer
    tw = tokenizer.texts_to_sequences([text])
    # Добавление дополнительных нулей в начало или обрезка до максимальной длины последовательности
    tw = pad_sequences(tw, maxlen=200)
    
    # Загрузка модели анализа настроений
    model = load_model('sentiment_analysis.h5')
    
    # Предсказание вероятности и определение настроения
    probability = model.predict(tw)[0][0]
    prediction = int(model.predict(tw).round().item())

    if prediction < 0.5:
        sentiment = 'Негативный'
    else:
        sentiment = 'Положительный'

    return sentiment, probability

def product_detail_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = Review.objects.filter(item=product)

    if request.method == 'POST':
        text = request.POST.get('text')
        rating = request.POST.get('rating')
        user = request.user

        # Предсказание настроения отзыва
        sentiment, score = predict_sentiment(text)

        # Создание нового отзыва
        new_review = Review.objects.create(text=text, rating=rating, user=user, item=product, sentiment=sentiment)
         
        return redirect('product_detail', product_id=product.id)

    context = {'product': product, 'reviews': reviews}
    return render(request, 'product_detail.html', context)

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def all_products(request, *args, **kwargs):
    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer)
        cartTotal = order.orderitem_set.all().aggregate(sum=Sum('quantity'))['sum']
        if cartTotal is None:
            cartTotal = ''
    else:
        cartTotal = ''

    all_products = Product.objects.all()

    paginator = Paginator(all_products, 16) 

    page_number = request.GET.get('page')
    try:
        products = paginator.page(page_number)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    context = {'cartTotal': cartTotal, 'products': products}
    return render(request, "all_products.html", context)

def success_view(request):
    return render(request, "success.html")   

def cancel_view(request):
    return render(request, "cancel.html")   

def get_client_token(request):
    client_token = braintree.ClientToken.generate()
    return JsonResponse({'client_token': client_token})

def process_payment(request):
    if request.method == 'POST':
        nonce_from_the_client = request.POST.get('payment_method_nonce')
        amount = request.POST.get('amount')

        result = braintree.Transaction.sale({
            "amount": amount,
            "payment_method_nonce": nonce_from_the_client,
            "options": {
                "submit_for_settlement": True
            }
        })

        if result.is_success:
            return JsonResponse({'success': True, 'transaction_id': result.transaction.id})
        else:
            return JsonResponse({'success': False, 'error': result.message})

    return render(request, 'process_payment.html')