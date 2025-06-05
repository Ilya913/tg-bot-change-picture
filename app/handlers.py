from aiogram import F, Router, types, Bot
from aiogram.types import Message, InputFile, ReplyKeyboardRemove, CallbackQuery
from aiogram.filters import CommandStart, Command
from rembg import remove
from PIL import Image
import logging
import io
from aiogram.fsm.context import FSMContext
from g4f.client import Client
import asyncio

import app.keyboards as kb
import app.states as st

router = Router()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.message(Command('help'))
async def cmd_help(message: Message):
    await message.answer('Нажата кнопка помощи')


@router.message(F.text == 'Меня зовут Арсений')
async def pidor_found(message: Message):
    await message.answer('Пошел нахуй')


@router.message(CommandStart())
async def start_bot(message: Message):
    #временно чтобы у всех ушла старая клавиатура
    await message.answer(
        "Приветствую в боте по редактированию и созданию фотографий",
        reply_markup=ReplyKeyboardRemove()
    )
    await message.answer('Главное меню', reply_markup=kb.main)


@router.callback_query(F.data == 'return_mm')
async def return_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    await callback.answer('Возвращение в главное меню')
    await callback.message.answer('Главное меню', reply_markup=kb.main)


@router.message(st.Gen.wait)
async def stop_flood(message: Message):
    await message.answer('Подождите, ваш запрос обрабатывается')


@router.callback_query(F.data == 'remove_bg')
async def remove_background_text(callback: CallbackQuery, state: FSMContext):
    await state.set_state(st.mode.delete_background)

    await callback.answer('Выбран режим удаления заднего фона')
    await callback.message.answer('Отправьте фото или нажмите "Вернуться в главное меню"', reply_markup=kb.return_to_main_menu)


@router.callback_query(F.data == 'generate_image')
async def remove_background_text(callback: CallbackQuery, state: FSMContext):
    await state.set_state(st.mode.generate_image)

    await callback.answer('Выбран режим создания фото')
    await callback.message.answer('Опишите изображение которое хотите сгенерировать или нажмите "Вернуться в главное меню"', reply_markup=kb.return_to_main_menu)


@router.message(st.mode.delete_background)
async def remove_background(message: Message, bot: Bot, state: FSMContext):
    try: 
        await state.set_state(st.Gen.wait)

        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        download_file = await bot.download_file(file_info.file_path)

        input_image = Image.open(io.BytesIO(download_file.read()))
        output_image = remove(input_image)

        output_buffer = io.BytesIO()
        output_image.save(output_buffer, format="PNG", quality=100)
        output_buffer.seek(0)

        result_file = types.BufferedInputFile(
            file=output_buffer.getvalue(),
            filename="no_bg.png"
        )

        await message.reply_photo(result_file)
        logger.info("Фон успешно удален")

        await message.reply_document(
            document=result_file,
            caption="Ваше изображение с удалённым фоном 🖼️"
        )
        await message.answer('Вы можете вернуться в меню или удалить фон с фото, отправив его', reply_markup=kb.return_to_main_menu)
        

    except AttributeError as e:
        if "'NoneType'" in str(e):
            await message.answer('Ошибка: не получено изображение. Отправьте фото')
        else:
            logger.error(f"Ошибка атрибута: {e}")
            await message.reply("Ошибка обработки изображения")
            
    except TypeError as e:
        if "'NoneType'" in str(e):
            await message.answer('Отправьте фото')
        else:
            logger.error(f"Ошибка типа: {e}")
            await message.reply("Ошибка формата данных")
            
    except Exception as e:
        logger.error(f"Неизвестная ошибка: {e}")
        await message.reply("Произошла ошибка удаления фона")

    await state.set_state(st.mode.delete_background)


@router.message(st.mode.generate_image)
async def create_image(message: Message, state: FSMContext):
    try:
        await state.set_state(st.Gen.wait)
        def sync_generate_image():
            client = Client()

            promt_translate = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": f"Ты переводчик и тебе надо на английский перевести вот этот текст: {message.text}. В качестве ответа дай только тот пререведенный текст"}]
            )
            logger.info(promt_translate.choices[0].message.content)
            return client.images.generate(
                model="flux",
                prompt=promt_translate.choices[0].message.content,
                response_format="url"
            )

        response = await asyncio.to_thread(sync_generate_image)
        

        await message.answer(response.data[0].url)
        await message.answer('Опишите изображение которое хотите сгенерировать или нажмите "Вернуться в главное меню"', reply_markup=kb.return_to_main_menu)
        logger.info("Фото сгенерировано")

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await message.answer("Произошла ошибка генерации")

    await state.set_state(st.mode.generate_image)