import asyncio

import aiohttp
import json
from datetime import datetime

import requests


async def create_express_invoice(recipient_city_name, recipient_address_name, recipient_name, recipient_phone, cost):
    url = "https://api.novaposhta.ua/v2.0/json/"

    headers = {
        "Content-Type": "application/json",
    }

    data = {
        "apiKey": "62e67e9ea806d8de68a6089d53f8f71e",
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
            "CitySender": "db5c88e0-391c-11dd-90d9-001a92567626",
            "Sender": "2d5eacd8-1c8f-11e8-8b24-005056881c6b",
            "SenderAddress": "6e803ff7-f4ff-11ef-84e0-48df37b921da",
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
                        # Формуємо повідомлення для користувача
                        invoice_number = response_data['data'][0]['IntDocNumber']
                        delivery_cost = response_data['data'][0]['CostOnSite']
                        estimated_delivery_date = response_data['data'][0]['EstimatedDeliveryDate']
                        message = (
                            f"Експрес-накладну створено успішно!\n"
                            f"Номер накладної: {invoice_number}\n"
                            f"Вартість доставки: {delivery_cost}\n"
                            f"Прогнозована дата доставки: {estimated_delivery_date}"
                        )
                        return message
                    else:
                        # Повідомлення у разі помилки
                        errors = response_data.get("errors", "Невідома помилка")
                        return f"Сталася помилка при створенні накладної: {errors}"
                except ValueError:
                    return "Помилка при обробці відповіді JSON."
            else:
                return f"Помилка HTTP запиту: {response.status}"



# Приклад використання


def city_ref(city):
    url = "https://api.novaposhta.ua/v2.0/json/"
    headers = {
        "Content-Type": "application/json",
    }
    data = {
        "apiKey": "62e67e9ea806d8de68a6089d53f8f71e",
        "modelName": "AddressGeneral",
        "calledMethod": "getCities",
        "methodProperties": {
            "FindByString": city
        }
    }

    # Надсилаємо POST запит
    response = requests.post(url, headers=headers, data=json.dumps(data))

    # Перевіряємо, чи запит успішний
    if response.status_code == 200:
        # Парсимо JSON-дані
        response_data = response.json()

        # Перевіряємо, чи є в відповіді місто
        if "data" in response_data and response_data["data"]:
            # Повертаємо Ref першого результату
            ref = response_data["data"][0].get("Ref")
            return ref
        else:
            print("Місто не знайдено")
            return None
    else:
        print(f"Помилка: {response.status_code}")
        return None


async def get_warehouse_ref(city_name: str, warehouse_number: str):
    url = "https://api.novaposhta.ua/v2.0/json/"
    headers = {
        "Content-Type": "application/json",
    }
    data = {
        "apiKey": "62e67e9ea806d8de68a6089d53f8f71e",
        "modelName": "AddressGeneral",
        "calledMethod": "getWarehouses",
        "methodProperties": {
            "CityName": city_name,
            "FindByString": warehouse_number
        }
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=data, headers=headers) as response:
                if response.status == 200:
                    response_data = await response.json()
                    # Перевіряємо, чи є успіх і дані
                    if response_data['success']:
                        # Якщо є відділення, повертаємо Ref першого відділення
                        if response_data['data']:
                            return response_data['data'][0]['Ref']
                        else:
                            return None
                    else:
                        return None
                else:
                    return None
        except Exception as e:
            print(f"Error during API request: {e}")
            return None

