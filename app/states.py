from aiogram.fsm.state import State, StatesGroup


class Mode(StatesGroup):
    process_background = State()
    generate_image = State()
    replace_bg_background = State()


class Gen(StatesGroup):
    wait = State()
