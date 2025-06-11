from aiogram import F, Router, types, Bot
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
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
    # временно чтобы у всех ушла старая клавиатура
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


async def download_photo(bot: Bot, photo) -> Image.Image:
    """Скачивает фото и возвращает PIL Image"""
    file_info = await bot.get_file(photo.file_id)
    downloaded = await bot.download_file(file_info.file_path)
    return Image.open(io.BytesIO(downloaded.read()))


async def create_file(image: Image.Image, filename: str) -> types.BufferedInputFile:
    """Создает файл bytes изображения и возвращает вместе с именем файла"""
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return types.BufferedInputFile(file=buf.getvalue(), filename=filename)


@router.callback_query(F.data == 'remove_bg')
async def remove_background_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки для удаления фона"""
    await state.set_state(st.Mode.process_background)
    await state.update_data(mode='remove')
    await callback.answer('Выбран режим удаления фона')
    await callback.message.answer(
        'Отправьте фото для удаления фона',
        reply_markup=kb.return_to_main_menu
    )


@router.callback_query(F.data == 'add_bg')
async def replace_background_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки для замены фона"""
    await state.set_state(st.Mode.process_background)
    await state.update_data(mode='replace')
    await callback.answer('Выбран режим замены фона')
    await callback.message.answer(
        'Отправьте фото объекта (передний план)',
        reply_markup=kb.return_to_main_menu
    )


@router.message(st.Mode.process_background, F.photo)
async def process_photo_background(message: Message, bot: Bot, state: FSMContext):
    """Общий обработчик для работы с фоном
    Режим remove удаляет фон с изображения и отправляет результат
    Режим replace сохраняет изображение и ждёт новый фон"""
    try:
        data = await state.get_data()
        mode = data.get('mode')
        image = await download_photo(bot, message.photo[-1])
        no_bg_img = remove(image)

        if mode == 'remove':
            result_file = await create_file(no_bg_img, "no_bg.png")
            await message.reply_document(
                document=result_file,
                caption="Ваше изображение с удалённым фоном: "
            )
            await message.answer("Отправьте фото для удаления фона",
                                 reply_markup=kb.return_to_main_menu)
            await state.set_state(st.Mode.process_background)

        elif mode == 'replace':
            buf = io.BytesIO()
            no_bg_img.save(buf, format="PNG")
            await state.update_data({
                'foreground': buf.getvalue(),
                'img_size': no_bg_img.size,
                'mode': 'replace'
            })
            await state.set_state(st.Mode.replace_bg_background)
            await message.answer("Задний план удалён! Отправьте новый фон",
                                 reply_markup=kb.return_to_main_menu)

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await message.answer("Произошла ошибка обработки изображения")


@router.message(st.Mode.replace_bg_background, F.photo)
async def process_background_photo(message: Message, bot: Bot, state: FSMContext):
    """Обрабатывает новый фон:
    1. Получает сохраненный передний план
    2. Скачивает новый фон
    3. Совмещает изображения
    4. Отправляет результат"""
    try:
        data = await state.get_data()
        foreground = Image.open(io.BytesIO(data['foreground']))
        background = await download_photo(bot, message.photo[-1])
        background = background.resize(data['img_size']).convert("RGBA")
        foreground = foreground.convert("RGBA")
        result = background.copy()
        result.paste(foreground, (0, 0), foreground.getchannel('A'))
        result_file = await create_file(result, "new_background.jpeg")
        await message.reply_document(
            document=result_file,
            caption="Ваше изображение с новым фоном: "
        )
        await message.answer("Отправьте фото объекта (передний план)",
                             reply_markup=kb.return_to_main_menu)
        await state.set_state(st.Mode.process_background)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await message.answer("Ошибка при замене фона")


@router.callback_query(F.data == 'generate_image')
async def generate_image_text(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки генерации изображения"""
    await state.set_state(st.Mode.generate_image)

    await callback.answer('Выбран режим создания фото')
    await callback.message.answer(
        'Опишите изображение которое хотите сгенерировать или нажмите "Вернуться в главное меню"',
        reply_markup=kb.return_to_main_menu)


@router.message(st.Mode.generate_image)
async def create_image(message: Message, state: FSMContext):
    """ Генерирует изображение по описанию:
    1. Переводит запрос на английский
    2. Генерирует изображение через AI
    3. Отправляет результат"""
    try:
        await state.set_state(st.Gen.wait)

        def sync_generate_image():
            client = Client()

            promt_translate = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user",
                           "content": f"Ты переводчик и тебе надо на английский перевести вот этот текст: {message.text}. В качестве ответа дай только тот пререведенный текст"}]
            )
            logger.info(promt_translate.choices[0].message.content)
            return client.images.generate(
                model="flux",
                prompt=promt_translate.choices[0].message.content,
                response_format="url"
            )
        response = await asyncio.to_thread(sync_generate_image)
        await message.answer(response.data[0].url)
        await message.answer('Опишите изображение которое хотите сгенерировать или нажмите "Вернуться в главное меню"',
                             reply_markup=kb.return_to_main_menu)
        logger.info("Фото сгенерировано")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await message.answer("Произошла ошибка генерации")
    await state.set_state(st.Mode.generate_image)