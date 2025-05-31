from aiogram.fsm.state import State, StatesGroup

class mode(StatesGroup):
    delete_background = State()
    generate_image = State()