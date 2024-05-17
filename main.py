from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Text
import json
import datetime
import function
import keyboard
from database import db  # Импортируем наш модуль базы данных
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import logging
from aiogram.utils.exceptions import (MessageNotModified,
                                      CantParseEntities, MessageToDeleteNotFound, 
                                      MessageTextIsEmpty)
from openpyxl import Workbook
from io import BytesIO

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def error_handler(func):
    async def wrapper(message: types.Message):
        try:
            await func(message)
        except Exception as e:
            logger.error(f"Произошла ошибка: {e}")
    return wrapper

def readingFile():
    # Открываем файл config.json для чтения
    with open('config.json', 'r', encoding="UTF-8") as file:
        # Загружаем данные из файла JSON в словарь
        config = json.load(file)
        return config

config = readingFile()

id_dict = {}
message_dirt = {}

bot = Bot(config["TOKEN"])
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class MainState(StatesGroup):
    Administrator = State()  # Общее состояние для всех чатов

async def on_startup(_):
    print("The bot is running!")

@dp.message_handler(commands="start")
@error_handler
async def cmdStart(message: types.Message):
    # Проверяем, зарегистрирован ли пользователь
    if await function.ClientRegistration(message):
        # Если пользователь зарегистрирован, отправляем ему сообщение для опытных пользователей
        await message.answer(text=config["TEXT_FOR_EXPERIENCED"])
    else:
        # Если пользователь новый, отправляем ему сообщение для новичков
        await message.answer(text=config["TEXT_FOR_BIGENNERS"])

@dp.message_handler(commands="admin")
@error_handler
async def cmdAdmin(message: types.Message):
    global config
    # Получаем текст команды без "/admin"
    arguments = message.get_args()
    if config["ADMIN_PASSWORD"] == arguments:
        await message.answer(text=config["HELLO_ADMIN"],
                             reply_markup=keyboard.kb_admin)
        id = message.from_user.id
        config["admin_user"] = id
        with open(f'config.json', "w", encoding='utf-8') as file:
            json.dump(config, file, indent=4, ensure_ascii=False)
        config = readingFile()

@dp.message_handler(commands="group", chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP])
@error_handler
async def cmdGroup(message: types.Message):
    global config
    if config["admin_user"] == message.from_user.id:
        id = message.chat.id
        config["chat_id"] = id
        with open(f'config.json', "w", encoding='utf-8') as file:
            json.dump(config, file, indent=4, ensure_ascii=False)
        config = readingFile()
        await bot.send_message(chat_id=message.from_user.id,
                                text="Группа успешно добавлена!")
        

async def is_user_in_group(group_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=group_id, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

@dp.message_handler(Text("📋 Список операторов"))
@error_handler
async def cmdPersonal(message: types.Message):
    if config["admin_user"] == message.from_user.id:
        user_statuses = []
        answer = await function.PersonalId()
        results = [item[0] for item in answer]
        i = 1
        for user_id in results:
            in_group = await is_user_in_group(config["chat_id"], user_id)
            if in_group:
                if user_id != config["admin_user"]: 
                    people = await function.CheckName(user_id)
                    user_statuses.append(f"{i}. {people[2]} {people[3]}")
                    i += 1
        if user_statuses == []:
             await message.answer(text="Операторы не найдены!")
        else:
            await message.answer("Список операторов:\n"+ ''.join(user_statuses), parse_mode="HTML")

@dp.message_handler(Text("📜 История работы операторов"))
@error_handler
async def OperatorList(message: types.Message):
    if config["admin_user"] == message.from_user.id:
        # Получаем историю работы операторов из базы данных
        data = await function.historyInfo()

        if not data:
            await message.answer(text="История пуста!")
            return

        # Создаем новую книгу Excel в асинхронном режиме
        wb = Workbook()

        # Получаем активный лист
        ws = wb.active

        # Добавляем заголовки столбцов
        ws.append(['№', 'Имя', 'Фамилия', 'Действие', 'Дата'])

        # Заполняем книгу данными
        for i, item in enumerate(data, start=1):
            # Получаем имя и фамилию оператора
            people = await function.CheckName(item[1])
            ws.append([i, people[2], people[3], item[2], item[3]])

        # Создаем буфер для сохранения книги
        buffer = BytesIO()

        # Сохраняем книгу в буфер в асинхронном режиме
        await wb.save(buffer)

        # Смещаем указатель буфера в начало
        buffer.seek(0)

        # Отправляем файл пользователю
        file_name = "История работы операторов.xlsx"
        await bot.send_document(chat_id=message.from_user.id, document=(file_name, buffer))

@dp.message_handler(commands=['registration'])
@error_handler
async def register_user(message: types.Message):
    # Получаем аргументы команды
    args = message.get_args()
    
    # Разделяем аргументы на имя и фамилию
    if args:
        # Разделяем аргументы на имя и фамилию
        try:
            first_name, last_name = args.split(maxsplit=1)  # Разделяем аргументы только один раз
            # Проверяем, что имя и фамилия не пустые
            if first_name.strip() and last_name.strip():
                # Обновляем данные клиента в базе данных
                await db.execute("UPDATE client SET first_name = ?, last_name = ? WHERE id = ?", first_name, last_name, message.from_user.id)
                await message.reply("Ваши данные успешно сохранены!")
            else:
                await message.reply("Пожалуйста, укажите имя и фамилию.")
        except ValueError:
            await message.reply("Пожалуйста, укажите имя и фамилию в правильном формате: /registration Имя Фамилия")
    else:
        await message.reply("Пожалуйста, укажите имя и фамилию в формате: /registration Имя Фамилия")

@dp.message_handler(commands="close")
@error_handler
async def cmdClose(message: types.Message):
    # Получаем данные о клиенте и заявке, с которой работает оператор
    data = await function.CheckDialog(operator_id=message.from_user.id)
    # Проверяем, найдены ли данные
    if data == False:
        return
    else:
        # Если данные найдены, получаем id клиента
        id_client = data[2]
        # Отправляем сообщение клиенту о закрытии заявки
        await bot.send_message(chat_id=id_client,
                            text=config["OPERATOR_CLOSE"])
        # Удаляем запись о диалоге и заявке из базы данных
        await db.execute("DELETE FROM dialog WHERE operator = ? AND client = ?", message.from_user.id, id_client)
        # Получаем информацию о последнем сообщении и удаляем соответствующую заявку из базы данных
        text = message_dirt[f"{id_client}"].text
        del message_dirt[f"{id_client}"]
        parts = text.split("\n")
        # Получить текст заявки
        text_part = parts[1].split(": ")[1]
        # Получить дату обращения
        time_part = parts[2].split(": ")[1]
        await db.execute("DELETE FROM application WHERE text = ? AND time = ?", text_part, time_part)
        del id_dict[f"{message.from_user.id}"]
        
        # Записываем действие оператора в историю
        current_datetime = datetime.datetime.now()
        formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M")
        await db.execute("INSERT INTO history (user_id, action, time) VALUES (?, ?, ?)", message.from_user.id, f"Закрыл обращение: {text_part}", formatted_datetime)

@dp.callback_query_handler(text='delete application')
@error_handler
async def deleteApplication(callback: types.CallbackQuery):
    # Получаем текст сообщения callback запроса
    text = callback.message.text
    # Разделяем текст на две части по символу новой строки
    parts = text.split("\n")
    # Получаем id клиента из первой части сообщения
    id_part = parts[0].split(": ")[1]
    # Получаем текст заявки из второй части сообщения
    text_part = parts[1].split(": ")[1]
    # Получаем дату обращения из третьей части сообщения
    time_part = parts[2].split(": ")[1]
    # Удаляем запись о заявке из базы данных
    await db.execute("DELETE FROM application WHERE text = ? AND time = ?", text_part, time_part)
    # Записываем действие оператора в историю
    current_datetime = datetime.datetime.now()
    formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M")
    await db.execute("INSERT INTO history (user_id, action, time) VALUES (?, ?, ?)", callback.from_user.id, f"Удалил обращение: {text_part}", formatted_datetime)
    await bot.send_message(chat_id=id_part, 
                            text=f"Оператор удалил ваше обращение: {text_part}")
    # Удаляем сообщение о заявке из чата
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    
@dp.callback_query_handler(text='reply to the request')
@error_handler
async def responseToApplication(callback: types.CallbackQuery):
    # Получаем данные о диалоге оператора
    data = await function.CheckDialog(operator_id=callback.from_user.id)
    # Если диалог уже существует, отправляем сообщение об отказе
    if data:
        await bot.send_message(chat_id=callback.message.chat.id,
                                text=config["REFUSAL_TO_RESPOND_TO_AN_APPLICATION"])
        return
    # Получаем текст сообщения callback запроса
    text = callback.message.text
    # Разделяем текст на две части по символу новой строки
    parts = text.split("\n")
    # Получаем id клиента из первой части сообщения
    id_part = parts[0].split(": ")[1]
    # Сохраняем id клиента
    id_dict[f"{callback.from_user.id}"] = int(id_part)
    # Получаем текст заявки из второй части сообщения
    text_part = parts[1].split(": ")[1]
    # Добавляем запись о диалоге в базу данных
    await db.execute("INSERT INTO dialog (operator, client) VALUES (?, ?)", callback.from_user.id, id_part)
    # Формируем текст сообщения с уведомлением оператора
    text = config["OPERATOR_NOTIFICATION"] + f"Тема обращения: {text_part}"
    # Отправляем уведомление оператору
    await bot.send_message(chat_id=callback.from_user.id, 
                            text=text)
    await bot.send_message(chat_id=id_part, 
                            text=config["ANSWER"])
    # Удаляем сообщение о заявке из чата
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    return

@dp.message_handler(content_types=types.ContentType.PHOTO)
@error_handler
async def handle_photo(message: types.Message):
    await handle_content_message(message, types.ContentType.PHOTO)


@dp.message_handler(content_types=types.ContentType.AUDIO)
@error_handler
async def handle_audio(message: types.Message):
    await handle_content_message(message, types.ContentType.AUDIO)


@dp.message_handler(content_types=types.ContentType.VIDEO)
@error_handler
async def handle_video(message: types.Message):
    await handle_content_message(message, types.ContentType.VIDEO)


@dp.message_handler(content_types=types.ContentType.VOICE)
@error_handler
async def handle_voice(message: types.Message):
    await handle_content_message(message, types.ContentType.VOICE)


@dp.message_handler(content_types=types.ContentType.DOCUMENT)
@error_handler
async def handle_document(message: types.Message):
    await handle_content_message(message, types.ContentType.DOCUMENT)


@dp.message_handler(content_types=types.ContentType.STICKER)
@error_handler
async def handle_sticker(message: types.Message):
    await handle_content_message(message, types.ContentType.STICKER)


@dp.message_handler(content_types=types.ContentType.VIDEO_NOTE)
@error_handler
async def handle_video_note(message: types.Message):
    await handle_content_message(message, types.ContentType.VIDEO_NOTE)


@dp.message_handler(content_types=types.ContentType.LOCATION)
@error_handler
async def handle_location(message: types.Message):
    await handle_content_message(message, types.ContentType.LOCATION)


@dp.message_handler(content_types=types.ContentType.CONTACT)
@error_handler
async def handle_contact(message: types.Message):
    await handle_content_message(message, types.ContentType.CONTACT)


async def outputInto(id, message, content_type):
    check = await function.CheckDialog(client_id=id)
    if check:
        sender_is_client = message.from_user.id == check[1]
        recipient_id = check[2] if sender_is_client else check[1]
        sender_name = "Клиент:" if sender_is_client else f"Оператор {function.CheckName(check[1])[2]}:"
        if content_type == types.ContentType.PHOTO:
            await bot.send_photo(chat_id=recipient_id, photo=message.photo[-1].file_id, caption=sender_name)
        elif content_type == types.ContentType.AUDIO:
            await bot.send_audio(chat_id=recipient_id, audio=message.audio.file_id, caption=sender_name)
        elif content_type == types.ContentType.VIDEO:
            await bot.send_video(chat_id=recipient_id, video=message.video.file_id, caption=sender_name)
        elif content_type == types.ContentType.VOICE:
            await bot.send_voice(chat_id=recipient_id, voice=message.voice.file_id, caption=sender_name)
        elif content_type == types.ContentType.DOCUMENT:
            await bot.send_document(chat_id=recipient_id, document=message.document.file_id, caption=sender_name)
        elif content_type == types.ContentType.STICKER:
            await bot.send_sticker(chat_id=recipient_id, sticker=message.sticker.file_id)
        elif content_type == types.ContentType.VIDEO_NOTE:
            await bot.send_video_note(chat_id=recipient_id, video_note=message.video_note.file_id)
        elif content_type == types.ContentType.LOCATION:
            await bot.send_location(chat_id=recipient_id, latitude=message.location.latitude, longitude=message.location.longitude)
        elif content_type == types.ContentType.CONTACT:
            await bot.send_contact(chat_id=recipient_id, phone_number=message.contact.phone_number, first_name=message.contact.first_name)

async def handle_content_message(message: types.Message, content_type: str):
    if message.chat.type == types.ChatType.PRIVATE:
        if id_dict.get(f"{message.from_user.id}") is not None:
            id = id_dict[f"{message.from_user.id}"]
            await outputInto(id, message, content_type)
        elif message.from_user.id in id_dict.values():
            id = message.from_user.id
            await outputInto(id, message, content_type)
        elif message.chat.type == types.ChatType.PRIVATE:
            await message.answer(text=config["TEXT_ONLY"])

async def OutputText(id, message):
    # Проверяем статус диалога клиента с оператором
    check = await function.CheckDialog(client_id=id)
    # Если диалог существует и его статус "question"
    if check:
        # Если отправитель сообщения - клиент
        if message.from_user.id == check[1]:
            # Отправляем сообщение оператору
            name = await function.CheckName(check[1])
            await bot.send_message(chat_id=check[2], text=f"Оператор {name[2]}: " + message.text)
        # Если отправитель сообщения - оператор
        else:
            # Отправляем сообщение клиенту
            await bot.send_message(chat_id=check[1], text="Клиент: " + message.text)
    else:
        # Если диалога не существует или его статус не "question", обрабатываем сообщение как обычно
        if message.chat.type == types.ChatType.PRIVATE:
            check = await function.AcceptanceOfApplication(message)
            if check:
                await message.answer(text=config["APPLICATION_ACCEPTED"])
                current_datetime = datetime.datetime.now()
                formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M")
                text = f"👨‍💼Клиент: {message.from_user.id}\n📝 Заявка: {message.text}\n📅 Дата обращения: {formatted_datetime}"
                message_dirt[f"{message.from_user.id}"] = await bot.send_message(chat_id=config["chat_id"], text=text, reply_markup=keyboard.ikb_application)
            else:
                await message.answer(text=config["REFUSAL_OF_APPLICATION"])

@dp.message_handler(content_types=types.ContentType.TEXT)
@error_handler
async def echoAll(message: types.Message):
    # Проверяем, существует ли переменная config.id
    if message.chat.type == types.ChatType.PRIVATE:
        if id_dict.get(f"{message.from_user.id}") is not None:
            id = id_dict[f"{message.from_user.id}"]
            await OutputText(id, message)
        elif message.from_user.id in id_dict.values():
            id = message.from_user.id
            await OutputText(id, message)
        else:
            # Если config.id не существует, обрабатываем сообщение как обычно
            if message.chat.type == types.ChatType.PRIVATE:
                check = await function.AcceptanceOfApplication(message)
                if check:
                    await message.answer(text=config["APPLICATION_ACCEPTED"])
                    current_datetime = datetime.datetime.now()
                    formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M")
                    text = f"👨‍💼Клиент: {message.from_user.id}\n📝 Заявка: {message.text}\n📅 Дата обращения: {formatted_datetime}"
                    message_dirt[f"{message.from_user.id}"] = await bot.send_message(chat_id=config["chat_id"], text=text, reply_markup=keyboard.ikb_application)
                else:
                    await message.answer(text=config["REFUSAL_OF_APPLICATION"])

@dp.errors_handler()
async def global_error_handler(update, exception):
    if isinstance(exception, (MessageNotModified, CantParseEntities, MessageToDeleteNotFound, MessageTextIsEmpty)):
        # Игнорируем эти ошибки
        return True

    logger.exception(f"Обновление: {update} вызвало ошибку: {exception}")

    return True

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)

