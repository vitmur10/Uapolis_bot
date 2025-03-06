from django.contrib import admin
from .models import CustomUser, Product, Cart, CartItem, Category

admin.site.register(CustomUser)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Cart)
admin.site.register(CartItem)
