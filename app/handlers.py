from aiogram import F, Router, types, Bot
from aiogram.types import Message, InputFile
from aiogram.filters import CommandStart, Command
from rembg import remove
from PIL import Image
import logging
import io

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer('Привет, я самый лучший бот Илюша и я помогу тебе в редактировании твоих изображений')


@router.message(Command('help'))
async def cmd_help(message: Message):
    await message.answer('Нажата кнопка помощи')


@router.message(F.text == 'Меня зовут Арсений')
async def pidor_found(message: Message):
    await message.answer('Пошел нахуй')


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.message(F.photo)
async def remove_background(message: Message, bot: Bot):
    try:
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        download_file = await bot.download_file(file_info.file_path)

        input_image = Image.open(io.BytesIO(download_file.read()))
        output_image = remove(input_image)

        output_buffer = io.BytesIO()
        output_image.save(output_buffer, format="PNG")
        output_buffer.seek(0)

        result_file = types.BufferedInputFile(
            file=output_buffer.getvalue(),
            filename="no_bg.png"
        )

        await message.reply_photo(result_file)
        logger.info("Фон успешно удален")

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await message.reply("Произошла ошибка, виноват Николай Баулмосов")