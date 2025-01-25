# core/states.py
from aiogram.fsm.state import State, StatesGroup

class UserState(StatesGroup):
    """
    Состояния пользователя в процессе взаимодействия с ботом.
    
    Attributes:
        initial: Начальное состояние (до нажатия /start)
        unauthorized: Пользователь нажал /start, но не авторизован
        authorized: Пользователь авторизован
        rewrite_resume: Пользователь в процессе рерайта резюме
        final: Пользователь получил услугу
    """
    initial = State()        # Начальное состояние
    unauthorized = State()   # Не авторизован
    authorized = State()     # Авторизован
    rewrite_resume = State() # Рерайт резюме
    final = State()         # Финальное состояние