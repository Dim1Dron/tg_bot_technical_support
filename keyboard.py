from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

ikb_application = InlineKeyboardMarkup(resize_keyboard=True,row_width=2)
ikb_application_bn = InlineKeyboardButton(text=f'💬 Откликнуться', callback_data='reply to the request')
ikb_application_bn_2 = InlineKeyboardButton(text=f'❌ Удалить', callback_data='delete application')
ikb_application.add(ikb_application_bn, ikb_application_bn_2)


kb_admin = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
kb_admin_bn_1 = KeyboardButton("📋 Список операторов")
kb_admin_bn_2 = KeyboardButton("📜 История работы операторов")

kb_admin.add(kb_admin_bn_1, kb_admin_bn_2)