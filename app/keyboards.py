from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Генерация изображения', callback_data='generate_image')],
    [InlineKeyboardButton(text='Удаление заднего фона', callback_data='remove_bg')],
    [InlineKeyboardButton(text='Добавление нового заднего фона', callback_data='add_bg')],
    [InlineKeyboardButton(text='Изменение формата фотографии', callback_data='change_format')],
    [InlineKeyboardButton(text='Создание pdf файла', callback_data='create_pdf')],
    [InlineKeyboardButton(text='Улучшение качества изображения', callback_data='enhance_quality')]
])

return_to_main_menu = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Вернуться в главное меню', callback_data='return_mm')]])