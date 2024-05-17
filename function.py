from aiogram import types
import datetime
from database import db

async def ClientRegistration(message: types.Message):
    try:
        result = await db.fetchone("SELECT * FROM client WHERE id = ?", message.from_user.id)
        if result:
            return True
        else:
            await db.execute("INSERT INTO client (id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
                             message.from_user.id, message.from_user.username, message.from_user.first_name, message.from_user.last_name)
            return False
    except Exception as e:
        print(f"Ошибка в функции ClientRegistration: {e}")

async def PersonalId():
    try:
        result = await db.fetchall("SELECT id FROM client")
        return result
    except Exception as e:
        print(f"Ошибка в функции PersonalId: {e}")

async def historyInfo():
    try:
        result = await db.fetchall("SELECT * FROM history")
        return result
    except Exception as e:
        print(f"Ошибка в функции historyInfo: {e}")

async def CheckName(id):
    try:
        result = await db.fetchone("SELECT * FROM client WHERE id = ?", id)
        return result
    except Exception as e:
        print(f"Ошибка в функции CheckName: {e}")

async def AcceptanceOfApplication(message: types.Message):
    try:
        result = await db.fetchall("SELECT * FROM application WHERE user_id = ?", message.from_user.id)
        if len(result) >= 1:
            return False
        else:
            current_datetime = datetime.datetime.now()
            formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M")
            await db.execute("INSERT INTO application (user_id, text, time) VALUES (?, ?, ?)",
                             message.from_user.id, message.text, formatted_datetime)
            return True
    except Exception as e:
        print(f"Ошибка в функции AcceptanceOfApplication: {e}")

async def CheckDialog(operator_id=None, client_id=None):
    try:
        if operator_id is not None:
            result = await db.fetchone("SELECT * FROM dialog WHERE operator = ?", operator_id)
        elif client_id is not None:
            result = await db.fetchone("SELECT * FROM dialog WHERE client = ?", client_id)
        else:
            return None
        return result if result else None
    except Exception as e:
        print(f"Ошибка в функции CheckDialog: {e}")
