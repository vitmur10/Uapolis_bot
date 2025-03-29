from django.db import models
from collections import defaultdict

from django.forms import IntegerField


class CustomUser(models.Model):
    """Модель користувача"""
    username = models.CharField(max_length=150, unique=True)  # Юзернейм користувача
    telegram_id = models.CharField(max_length=50, unique=True, null=True, blank=True)

    def __str__(self):
        return self.username


class ShippingAddress(models.Model):
    """Модель для адреси відправки з необхідними параметрами"""
    city_sender = models.CharField(max_length=36, verbose_name="CitySender")  # ID міста відправки
    sender_address = models.CharField(max_length=36, verbose_name="SenderAddress")  # ID адреси відправника
    name = models.CharField(max_length=255, verbose_name="Назва адреси")  # Назва адреси

    def __str__(self):
        return f" {self.name}"

    class Meta:
        verbose_name = "Адреса відправки"
        verbose_name_plural = "Адреси відправки"


class Category(models.Model):
    """Модель для категорій і підкатегорій"""
    GROUP_CHOICES = [
        ('Продукти', 'Продукти'),
        ('Інше', 'Інше'),
    ]

    name = models.CharField(max_length=255)  # Назва категорії
    group = models.CharField(max_length=10, choices=GROUP_CHOICES)  # Група категорії
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='subcategories'
    )  # Зв'язок з батьківською категорією
    is_visible = models.BooleanField(default=True)  # Галочка "Відображати категорію чи ні"

    def __str__(self):
        if self.parent:
            return f"{self.parent} > {self.name}"
        return self.name

    class Meta:
        verbose_name = "Категорія"
        verbose_name_plural = "Категорії"


class Product(models.Model):
    """Модель для продуктів"""
    name = models.CharField(max_length=255)  # Назва продукту
    shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.SET_NULL, null=True,
                                         blank=True)  # Вибір адреси відправки
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')  # Категорія
    photo = models.ImageField(upload_to='products/')  # Фото продукту
    price = models.DecimalField(max_digits=10, decimal_places=2, )  # Ціна продукту
    description = models.TextField(verbose_name="Опис Продукту")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Продукти"
        verbose_name_plural = "Продукт"


class Cart(models.Model):
    """Модель кошика"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # Користувач, який має цей кошик
    created_at = models.DateTimeField(auto_now_add=True)  # Час створення кошика

    def __str__(self):
        return f"Кошик користувача {self.user.username}"

    def total_price(self):
        """Підсумкова ціна всіх товарів у кошику"""
        total = sum(item.total_price() for item in self.cartitems.all())
        return total

    class Meta:
        verbose_name = "Кошик"
        verbose_name_plural = "Кошик"


class CartItem(models.Model):
    """Модель товару в кошику"""
    cart = models.ForeignKey(Cart, related_name='cartitems', on_delete=models.CASCADE)  # Кошик
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Товар
    quantity = models.PositiveIntegerField(default=1)  # Кількість товару

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def total_price(self):
        """Підсумкова ціна для цього товару (ціна * кількість)"""
        return self.product.price * self.quantity


class Order(models.Model):
    STATUS_CHOICES = [
        ('Очікує підтвердження', 'Очікує підтвердження'),
        ('Очікується', 'Очікується'),
        ('Оплачено', 'Оплачено'),
        ('Відправлено', 'Відправлено'),
        ('Доставлено', 'Доставлено'),
        ('Скасовано', 'Скасовано'),
    ]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Очікується')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    address = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    warehouse = models.CharField(max_length=255)
    tracking_number = models.CharField(max_length=50, default="Очікується")

    def __str__(self):
        return f"Замовлення {self.id} - {self.user.username}"

    class Meta:
        verbose_name = "Замовлення"
        verbose_name_plural = "Замовлення"

    def get_items_grouped_by_address(self):
        grouped_items = defaultdict(list)
        for item in self.items.all():
            if item.shipping_address:
                grouped_items[item.shipping_address.id].append(item)
        return dict(grouped_items)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.SET_NULL, null=True, blank=True)  # # змінено на ForeignKey

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Адреса: {self.shipping_address}) в замовленні {self.order.id}"



class Invoice(models.Model):
    number = models.IntegerField(unique=True)  # Номер накладної
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # Користувач, якому належить накладна
    order = models.ForeignKey(Order, on_delete=models.CASCADE,
                              related_name="invoices")  # Замовлення, до якого належить накладна
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Ціна товару

    # Адреси
    shipping_address = models.ForeignKey(ShippingAddress, related_name="shipping_invoices", on_delete=models.CASCADE,
                                         null=True,
                                         blank=True)  # Адреса відправлення
    delivery_address = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Накладна #{self.number} для {self.user.username}"  # Строкове представлення накладної


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def total_price(self):
        return self.quantity * self.price
