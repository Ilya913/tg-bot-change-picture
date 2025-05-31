from aiogram import F, Router, types, Bot
from aiogram.types import Message, InputFile
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


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer('Привет, я самый лучший бот Илюша и я помогу тебе в редактировании твоих изображений, выбери режим работы', reply_markup=kb.main)


@router.message(Command('help'))
async def cmd_help(message: Message):
    await message.answer('Нажата кнопка помощи')


@router.message(F.text == 'Меня зовут Арсений')
async def pidor_found(message: Message):
    await message.answer('Пошел нахуй')


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.message(F.text == 'Удаление заднего фона')
async def remove_background_text(message: Message, state: FSMContext):
    await state.set_state(st.mode.delete_background)
    await message.answer('Отправьте фото для удаления фона')


@router.message(F.text == 'Сгенерировать изображение')
async def remove_background_text(message: Message, state: FSMContext):
    await state.set_state(st.mode.generate_image)
    await message.answer('Опишите изображение которое хотите создать')


@router.message(st.mode.delete_background)
async def remove_background(message: Message, bot: Bot, state: FSMContext):
    try: 
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

        await state.clear()

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await message.reply("Произошла ошибка, виноват Николай Баулмосов")


@router.message(st.mode.generate_image)
async def create_image(message: Message, state: FSMContext):
    try:
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
        logger.info("Фото сгенерировано")

        await state.clear()

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await message.answer("Произошла ошибка генерации")