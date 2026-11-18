from aiogram.fsm.state import State, StatesGroup


class Flow(StatesGroup):
    content = State()
    logo = State()
    monogram = State()
