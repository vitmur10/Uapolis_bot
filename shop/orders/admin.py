from asgiref.sync import sync_to_async, async_to_sync
from django.contrib import admin
from django.utils.html import format_html
from .models import CustomUser, Category, Product, Cart, CartItem, Order, OrderItem, ShippingAddress, Invoice, \
    InvoiceItem
from .views import create_express_invoice, send_message

admin.site.register(CustomUser)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(OrderItem)
admin.site.register(ShippingAddress)
admin.site.register(Invoice)
admin.site.register(InvoiceItem)


@sync_to_async
def get_items_grouped_by_address(order):
    return order.get_items_grouped_by_address()


# Синхронізація викликів бази даних через sync_to_async
@sync_to_async
def get_order(order_id):
    try:
        return Order.objects.select_related('user').get(id=order_id)
    except Order.DoesNotExist:
        return None


async def confirm_order_async(order_id):
    order = await get_order(order_id)
    if not order:
        return [f"Замовлення з ID {order_id} не знайдено"]

    if order.status != 'Очікує підтвердження':
        return [f"Замовлення {order_id} не потребує підтвердження"]

    order.status = 'Очікується'
    await sync_to_async(order.save)()

    grouped_items = await get_items_grouped_by_address(order)
    invoice_messages = []

    for address_id, items in grouped_items.items():
        shipping_address = await sync_to_async(ShippingAddress.objects.get)(id=address_id)
        CitySender = shipping_address.city_sender
        SenderAddress = shipping_address.sender_address
        for order_item in items:
            invoice_message = await create_express_invoice(
                user=order.user,
                recipient_city_name=order.city,
                recipient_address_name=order.warehouse,
                recipient_name=order.full_name,
                recipient_phone=order.phone_number,
                cost=order_item.price,
                CitySender=CitySender,
                SenderAddress=SenderAddress,
                shipping_address=shipping_address,
                quantity=order_item.quantity,
                order=order,
                order_item=[order_item]  # Передаємо як список
            )
            invoice_messages.append(invoice_message)

    return invoice_messages


# Перетворюємо асинхронну функцію в синхронну за допомогою async_to_sync
def confirm_order(order_id):
    return async_to_sync(confirm_order_async)(order_id)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_price', 'created_at')
    actions = ['confirm_order']

    @admin.action(description="Підтвердити замовлення та створити накладну")
    def confirm_order(self, request, queryset):
        for order in queryset:
            # Викликаємо синхронно асинхронну функцію
            invoice_messages = confirm_order(order.id)
            # Відображаємо повідомлення в адмін панелі
            self.message_user(request, format_html(f"Замовлення {order.id}: {'; '.join(invoice_messages)}"))
            user_telegram_id = order.user.telegram_id  # Замініть на правильне поле з Telegram ID користувача
            message_text = f"Ваше замовлення {order.id} підтверджено! Накладні:\n" + "\n".join(invoice_messages)

            if user_telegram_id:
                send_message(user_telegram_id, message_text)
