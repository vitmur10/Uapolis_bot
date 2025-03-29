import json
from datetime import datetime

import aiohttp
import requests
from asgiref.sync import sync_to_async
from django.db import transaction
from django.http import FileResponse
import os
from dotenv import load_dotenv
from .models import Invoice, InvoiceItem

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TOKEN_NP = os.getenv('TOKEN_NP')


def send_message(chat_id, text):
    """
    Відправляє повідомлення користувачеві в Telegram.

    :param chat_id: Telegram ID користувача
    :param text: Текст повідомлення
    """
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
    }
    TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    response = requests.post(TELEGRAM_API_URL, data=data)

    if response.status_code != 200:
        print(f"Помилка надсилання повідомлення: {response.text}")

    return response.json()


# Create your views here.

def main(request):
    return FileResponse(open("static/main.pdf", "rb"), content_type="application/pdf")


@sync_to_async
def create_invoice(**kwargs):
    with transaction.atomic():  # Гарантує цілісність даних
        return Invoice.objects.create(**kwargs)


async def create_express_invoice(user, recipient_city_name, recipient_address_name, recipient_name, recipient_phone,
                                 cost, CitySender, SenderAddress, shipping_address, quantity, order, order_item):
    url = "https://api.novaposhta.ua/v2.0/json/"

    headers = {
        "Content-Type": "application/json",
    }

    data = {
        "apiKey": TOKEN_NP,
        "modelName": "InternetDocumentGeneral",
        "calledMethod": "save",
        "methodProperties": {
            "PayerType": "Recipient",
            "PaymentMethod": "Cash",
            "DateTime": datetime.now().strftime('%d.%m.%Y'),
            "CargoType": "Cargo",
            "Weight": "0.5",
            "ServiceType": "DoorsWarehouse",
            "SeatsAmount": "2",
            "Description": "Додатковий опис відправлення",
            "Cost": str(cost),
            "CitySender": CitySender,
            "Sender": "2d5eacd8-1c8f-11e8-8b24-005056881c6b",
            "SenderAddress": SenderAddress,
            "ContactSender": "f3b426ab-373a-11e9-9937-005056881c6b",
            "SendersPhone": "380993408130",
            "RecipientsPhone": recipient_phone,
            "NewAddress": "1",
            "RecipientCityName": recipient_city_name,
            "RecipientArea": "",
            "RecipientAreaRegions": "",
            "RecipientAddressName": recipient_address_name,
            "RecipientName": recipient_name,
            "RecipientType": "PrivatePerson",
            "SettlementType": "місто",
            "EDRPOU": "12345678"
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=json.dumps(data)) as response:
            if response.status == 200:
                try:
                    response_data = await response.json()
                    if response_data.get("success"):
                        invoice_number = response_data['data'][0]['IntDocNumber']
                        delivery_cost = response_data['data'][0]['CostOnSite']
                        estimated_delivery_date = response_data['data'][0]['EstimatedDeliveryDate']
                        # Створення запису в Invoice
                        invoice = await create_invoice(
                            number=invoice_number,
                            user=user,
                            order=order,
                            price=cost,
                            shipping_address=shipping_address,
                            delivery_address=recipient_address_name
                        )

                        # Створення запису в InvoiceItem
                        for item in order_item:
                            await sync_to_async(InvoiceItem.objects.create)(
                                invoice=invoice,
                                product=item.product,
                                quantity=item.quantity,
                                price=item.price
                            )

                        message = (
                            f"Номер накладної: {invoice_number}\n"
                            f"Вартість доставки: {delivery_cost}\n"
                            f"Прогнозована дата доставки: {estimated_delivery_date}\n"
                        )
                        return message
                    else:
                        errors = response_data.get("errors", "Невідома помилка")
                        return f"Сталася помилка при створенні накладної: {errors}"
                except ValueError:
                    return "Помилка при обробці відповіді JSON."
            else:
                return f"Помилка HTTP запиту: {response.status}"