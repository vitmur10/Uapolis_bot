import asyncio
import logging
import os
from datetime import timedelta
import aiogram
from aiogram import types, Bot
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile, InputFile
from asgiref.sync import sync_to_async
from django.core.wsgi import get_wsgi_application
from django.db.models.fields.files import ImageFieldFile
from django.utils import timezone
from keyboard import *

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shop.settings")
application = get_wsgi_application()
from aiogram.fsm.storage.memory import MemoryStorage

from orders.models import *
from Const import *

8
router = aiogram.Router()

logging.basicConfig(level=logging.INFO)

dp.include_router(router)


def generate_keyboard():
    # Генерація клавіатури з використанням генератора списку
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=group_name) for group_name, _ in Category.GROUP_CHOICES],
            [KeyboardButton(text="Кошик")],
        ], resize_keyboard=True)


@router.message(CommandStart())
async def send_product_categories(message: types.Message):
    keyboard = generate_keyboard()
    oferty = "https://docs.google.com/document/d/1kB2ImYMpkT27CoGFwWc4iN8RiaHVkA6j/edit?usp=drive_link&ouid=104641872811576473426&rtpof=true&sd=true"
    pol = "https://docs.google.com/document/d/1rtdO74ls75eoXeJI2jSuYJlD-d-4R3GX/edit?usp=drive_link&ouid=104641872811576473426&rtpof=true&sd=true"
    pyblic_dogovir = "https://docs.google.com/document/d/14JoVCWfNzlRtA-BnxYAOJdDtNPq8ZhG2/edit?usp=drive_link&ouid=104641872811576473426&rtpof=true&sd=true"
    await bot.send_photo(
        chat_id=message.chat.id,
        photo=FSInputFile("photo_2025-02-19_00-31-25.jpg"),
        caption=f"""<b>Привіт!</b> 🫙 Ви в <b>Digital Jar</b> – цифровому маркетплейсі, де кожен товар в кількох кліках. 
        <i>Пошук, покупка, оплата – все інтуїтивно зрозуміло.</i> Якщо потрібна допомога – пишіть, ми на зв'язку. 🤝
        <b>Задіджаримо разом!</b> 

        📜 <b>Договір оферти та інформація щодо повернення:</b> 
        <a href="{oferty}">Перейти до договору оферти</a>

        🔒 <b>Політика конфіденційності:</b> 
        <a href="{pol}">Перейти до політики</a>

        📃 <b>ПУБЛІЧНИЙ ДОГОВІР КОМІСІЇ:</b>
        <a href="{pyblic_dogovir}">Перейти до договору</a>""",
        parse_mode='HTML'  # Use HTML parsing mode for formatting
    )

    await message.answer("Оберіть категорію продуктів:", reply_markup=keyboard)


@router.callback_query(lambda call: call.data.startswith('product_'))
async def handle_product_selection(call: types.CallbackQuery):
    product_id = int(call.data.split("_")[-1])
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Додати до кошика 🛒", callback_data=f"add_to_cart_{product_id}")
            ]
        ]
    )
    # Fetch product using sync_to_async
    logger = logging.getLogger(__name__)

    try:
        product = await sync_to_async(Product.objects.get, thread_sensitive=True)(id=product_id)
    except Product.DoesNotExist:
        logger.error(f"Продукт із ID {product_id} не знайдено.")
        await bot.send_message(call.message.chat.id, "Продукт не знайдено. Будь ласка, оберіть інший.")
        return
    # Відправляємо деталі продукту
    await bot.send_photo(chat_id=call.message.chat.id, photo=FSInputFile(product.photo.path),
                         caption=f"Ціна: {product.price} грн\nТовар: {product.name}\n {product.description}",
                         reply_markup=keyboard)


@router.callback_query(lambda call: call.data.startswith('category_'))
async def productv(call: types.CallbackQuery):
    category = call.data.split("_")[-1]
    products = await sync_to_async(list)(Product.objects.filter(category_id=category))

    if not products:
        return

    # Створюємо клавіатуру для вибору продуктів
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=product.name, callback_data=f"product_{product.id}")]
        for product in products
    ])
    await bot.send_message(call.message.chat.id, "Оберіть продукт:", reply_markup=keyboard)


@router.callback_query(lambda call: call.data.startswith("add_to_cart_"))
async def handle_add_to_cart(call: types.CallbackQuery):
    try:
        # Отримуємо ID продукту
        product_id = int(call.data.split("_")[-1])
        user_id = call.from_user.id

        # Отримуємо продукт з бази даних
        product = await sync_to_async(Product.objects.get, thread_sensitive=True)(id=product_id)

        # Отримуємо кошик користувача або створюємо новий
        try:
            user = await sync_to_async(CustomUser.objects.get, thread_sensitive=True)(telegram_id=user_id,
                                                                                      username=call.from_user.username)
        except CustomUser.DoesNotExist:
            user = await sync_to_async(CustomUser.objects.create, thread_sensitive=True)(telegram_id=user_id,
                                                                                         username=call.from_user.username)
        cart, created = await sync_to_async(Cart.objects.get_or_create, thread_sensitive=True)(user=user)

        # Перевіряємо, чи продукт вже є в кошику
        cart_item, item_created = await sync_to_async(CartItem.objects.get_or_create, thread_sensitive=True)(
            cart=cart,
            product=product
        )

        if not item_created:
            # Якщо продукт вже є, збільшуємо кількість
            cart_item.quantity += 1
            await sync_to_async(cart_item.save, thread_sensitive=True)()

        await call.answer(f"Продукт '{product.name}' додано до кошика!", show_alert=True)

    except Product.DoesNotExist:
        await call.answer("Продукт з таким ID не знайдено.")


@router.callback_query(lambda call: call.data.startswith("remove_"))
async def remove_item_from_cart(call: types.CallbackQuery):
    # Отримуємо ID товару з callback data
    cart_item_id = int(call.data.split("_")[1])

    # Видаляємо товар із кошика
    await sync_to_async(CartItem.objects.filter(id=cart_item_id).delete)()

    await call.answer("Товар видалено з кошика!")
    await show_cart(call.message)  # Оновлюємо кошик


@router.callback_query(lambda call: call.data == "clear_cart")
async def clear_cart(call: types.CallbackQuery):
    user_id = call.from_user.id
    user_cart = await sync_to_async(Cart.objects.filter(user__telegram_id=user_id).first)()

    if user_cart:
        await sync_to_async(user_cart.cartitems.all().delete)()
        await call.answer("Кошик очищено!")
        await call.message.edit_text("Ваш кошик порожній.")
    else:
        await call.answer("Ваш кошик вже порожній!")


@router.callback_query(lambda call: call.data == "checkout")
async def checkout_cart(call: types.CallbackQuery):
    user_id = call.from_user.id
    user_cart = await sync_to_async(
        Cart.objects.prefetch_related('cartitems__product').filter(user__telegram_id=user_id).first)()

    if not user_cart or not user_cart.cartitems.exists():
        await call.answer("Ваш кошик порожній!")
        return

    # Логіка оформлення замовлення
    total_sum = user_cart.total_price()
    await call.message.edit_text(f"Замовлення оформлено!\nЗагальна сума: {total_sum} грн")

    # Очищення кошика після оформлення
    await sync_to_async(user_cart.cartitems.all().delete)()


# Обробка натискання на кнопку "Перейти до кошика"
@router.message(lambda message: message.text == "Кошик")
async def show_cart(message: aiogram.types.Message):
    user_id = message.from_user.id  # отримуємо ID користувача
    # Отримуємо кошик користувача
    user_id = message.from_user.id
    user_cart = await sync_to_async(
        Cart.objects.prefetch_related('cartitems__product').filter(user__telegram_id=user_id).first)()

    if not user_cart or not user_cart.cartitems.exists():
        await message.answer("Ваш кошик порожній.")
        return

    # Формуємо текст для відображення кошика
    cart_text = "Ваш кошик:\n"

    for item in user_cart.cartitems.all():
        cart_text += f"{item.product.name} - {item.quantity} x {item.product.price} грн = {item.total_price()} грн\n"
        # Додаємо кнопку для видалення товару
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text=f"Видалити {item.product.name}",
                    callback_data=f"remove_{item.id}"
                )], [
                    InlineKeyboardButton(text="Оформити замовлення", callback_data="checkout")
                    , InlineKeyboardButton(text="Очистити кошик", callback_data="clear_cart")]
            ]
        )

    cart_text += f"\nЗагальна сума: {user_cart.total_price()} грн"

    # Додаємо кнопки для оформлення замовлення або очищення кошика
    await message.answer(cart_text, reply_markup=keyboard)


@router.message(lambda message: message.text in ["Продукти", "Інше"])
async def menu(message: types.Message):
    category = message.text

    # Фільтруємо лише видимі категорії
    visible_categories = await sync_to_async(list)(
        Category.objects.filter(group=category, is_visible=True)
    )

    if visible_categories:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text=cat.name, callback_data=f"category_{cat.id}")
                ] for cat in visible_categories
            ]
        )
        await message.answer("Ось доступні категорії:", reply_markup=keyboard)
    else:
        await message.answer("Немає доступних категорій.")



@router.message(lambda message: message.text == "Оферта продажу")
async def ofert(message: types.Message):
    document_path = "documents/offer.docx"  # Шлях до вашого документа
    try:
        document = FSInputFile(document_path)
        await bot.send_document(chat_id=message.chat.id, document=document)
    except FileNotFoundError:
        await message.reply("Документ оферти наразі недоступний. Спробуйте пізніше.")


async def main():
    # Запускаємо функцію перевірки підписок у фоновому режимі

    # Запускаємо бота
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
