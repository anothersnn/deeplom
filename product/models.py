from django.db import models
from django.contrib.auth.models import User
from django.core.files import File
from forex_python.converter import CurrencyRates
from urllib.request import urlopen
from tempfile import NamedTemporaryFile
from decimal import Decimal

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null = True, blank = True)    
    name = models.CharField(max_length=200, null = True)

    def __str__(self):
         return self.name




from django.db import models
import re
class Product(models.Model):
    name = models.CharField(max_length=150)
    price = models.DecimalField(max_digits=100, decimal_places=2)
    
    store = models.CharField(max_length=30)
    category = models.CharField(max_length=150)
    image = models.ImageField(null=True, blank=True)
    image_url = models.URLField()
    tesco_match = models.IntegerField(null=True, blank=True)
    waitrose_match = models.IntegerField(null=True, blank=True)
    sainsburys_match = models.IntegerField(null=True, blank=True)
    morrisons_match = models.IntegerField(null=True, blank=True)
    in_stock = models.BooleanField(default=True)  
    volume_or_weight = models.CharField(max_length=50, null=True, blank=True)  
    description = models.TextField(max_length=350, null=True, blank=True)  
    

    def save(self, *args, **kwargs):
        print("Save method is called")
        if self.name:
            match = re.search(r'(\d+)\s*(Ml|G|G|Kg)', self.name, re.IGNORECASE)
            if match:
                print("Volume or weight extracted:", f"{match.group(1)} {match.group(2).upper()}")
                self.volume_or_weight = f"{match.group(1)} {match.group(2).upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def imageURL(self):
        try:
            url = self.image.url
        except:
            url = ''
        return url

    def clean(self, *args, **kwargs):
        if self.image_url and not self.image:
            img_temp = NamedTemporaryFile(delete=True)
            img_temp.write(urlopen(self.image_url).read())
            img_temp.flush()
            self.image.save(f"image_{self.pk}.jpg", File(img_temp))
        super(Product, self).save(*args, **kwargs)

    @property
    def tesco_match_id(self):
        return Product.objects.get(pk=self.tesco_match)

    @property
    def waitrose_match_id(self):
        return Product.objects.get(pk=self.waitrose_match)
        
    @property
    def sainsburys_match_id(self):
        return Product.objects.get(pk=self.sainsburys_match)

    @property
    def morrisons_match_id(self):
        return Product.objects.get(pk=self.morrisons_match)

    


 

 
for product in Product.objects.all():
   
    if product.name:
        match = re.search(r'(\d+)\s*(Ml|G|Kg)', product.name, re.IGNORECASE)
        if match:
            
            product.volume_or_weight = f"{match.group(1)} {match.group(2).upper()}"
           
            product.save()

class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete= models.SET_NULL, null= True, blank= True)

    def __str__(self):
        return str(self.id)

    @property
    def get_total_price_tesco(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.get_total_tesco for item in orderitems])
        return total

    @property
    def get_total_price_waitrose(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.get_total_waitrose for item in orderitems])
        return total

    @property
    def get_total_price_sainsburys(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.get_total_sainsburys for item in orderitems])
        return total

    @property
    def get_total_price_morrisons(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.get_total_morrisons for item in orderitems])
        return total

class OrderItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, blank=True, null=True)
    order = models.ForeignKey(Order, on_delete= models.SET_NULL, null = True)
    quantity = models.IntegerField(default=0, null = True, blank = True)

    @property
    def get_total(self):
        total = self.product.price * self.quantity
        return total

    @property
    def get_total_tesco(self):
        total = self.product.price * self.quantity
        if (self.product.tesco_match != -1):
            total = self.product.tesco_match_id.price * self.quantity
        return total

    @property
    def get_total_waitrose(self):
        total = self.product.price * self.quantity
        if (self.product.waitrose_match != -1):
            total = self.product.waitrose_match_id.price * self.quantity
        return total

    @property
    def get_total_sainsburys(self):
        total = self.product.price * self.quantity
        if (self.product.sainsburys_match != -1):
            total = self.product.sainsburys_match_id.price * self.quantity
        return total

    @property
    def get_total_morrisons(self):
        total = self.product.price * self.quantity
        if (self.product.morrisons_match != -1):
            total = self.product.morrisons_match_id.price * self.quantity
        return total
 
 
class Review(models.Model):
    text = models.TextField(verbose_name='Текст отзыва')
    rating = models.PositiveSmallIntegerField(verbose_name='Оценка')
    date_added = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Product, on_delete=models.CASCADE)
    sentiment = models.CharField(max_length=255, blank=True, null=True)

     

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'