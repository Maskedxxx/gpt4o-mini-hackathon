# keyboards/reply.py

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from core.text import CREATE_RESUME_BTN, EDIT_RESUME_BTN

def get_initial_keyboard():
    """
    Клавиатура, которая показывается пользователю,
    когда он только зашёл в бота и находится в состоянии initial.
    """
    keyboard = [
        [KeyboardButton(text="/start")]  # Здесь текст кнопки — это команда /start
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_unauthorized_keyboard():
    """
    Клавиатура, которая показывается пользователю,
    когда он нажал /start, но ещё не авторизовался.
    """
    keyboard = [
        [KeyboardButton(text="/start"), KeyboardButton(text="/auth")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_main_keyboard():
    """
    Клавиатура, которая показывается авторизованному пользователю
    (состояние authorized).
    
    Обратите внимание, что вы уже используете похожую функцию, 
    но здесь для примера указываю явный вариант.
    """
    keyboard = [
        [KeyboardButton(text=CREATE_RESUME_BTN), KeyboardButton(text=EDIT_RESUME_BTN)]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
