from django.db import models


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
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')  # Категорія
    photo = models.ImageField(upload_to='products/')  # Фото продукту
    price = models.DecimalField(max_digits=10, decimal_places=2, )  # Ціна продукту
    description = models.TextField(verbose_name="Опис Продукту")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Продукти"
        verbose_name_plural = "Продукт"


class CustomUser(models.Model):
    """Модель користувача"""
    username = models.CharField(max_length=150, unique=True)  # Юзернейм користувача
    telegram_id = models.CharField(max_length=50, unique=True, null=True, blank=True)

    def __str__(self):
        return self.username


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
