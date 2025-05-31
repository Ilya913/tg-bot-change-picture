from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Удаление заднего фона'), KeyboardButton(text='Добавление нового заднего фона')],
                                     [KeyboardButton(text='Изменение формата фотографии'), KeyboardButton(text='Создание pdf файла')],
                                     [KeyboardButton(text='Улучшить качество изображения')],
                                     [KeyboardButton(text='Сгенерировать изображение')]], resize_keyboard=True,
                                    input_field_placeholder='Выберите режим работы бота')