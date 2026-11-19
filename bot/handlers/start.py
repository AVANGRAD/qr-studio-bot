from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from ..i18n import SUPPORTED_LANGS, language_label, t, use_lang
from ..keyboards import help_kb, language_kb, welcome_kb
from ..services import set_menu_button
from ..states import Flow
from .common import clear_flow, get_draft, send_preview

router = Router(name="start")


async def _send_home(target: Message, state: FSMContext, bot: Bot | None = None) -> None:
    data = await state.get_data()
    lang = data.get("lang")
    if bot is not None:
        await set_menu_button(bot, lang if lang in SUPPORTED_LANGS else None, target.chat.id)
    if lang not in SUPPORTED_LANGS:
        await state.clear()
        await target.answer(t("choose_language"), reply_markup=language_kb())
        return
    await clear_flow(state)
    await target.answer(t("welcome"), reply_markup=welcome_kb())


@router.message(CommandStart())
async def start(message: Message, state: FSMContext, bot: Bot | None = None) -> None:
    await _send_home(message, state, bot)


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    await message.answer(t("help"), reply_markup=help_kb())


@router.message(Command("language"))
async def language_command(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await message.answer(t("choose_language"), reply_markup=language_kb(data.get("lang")))


@router.callback_query(F.data == "menu:home")
async def menu_home(callback: CallbackQuery, state: FSMContext, bot: Bot | None = None) -> None:
    await callback.answer()
    await _send_home(callback.message, state, bot)


@router.callback_query(F.data == "menu:help")
async def menu_help(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(t("help"), reply_markup=help_kb())


@router.callback_query(F.data.in_({"menu:new", "draft:new"}))
async def menu_new(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(Flow.content)
    await callback.message.answer(t("content_prompt"))


@router.callback_query(F.data == "lang:menu")
async def language_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    await callback.message.answer(t("choose_language"), reply_markup=language_kb(data.get("lang")))


@router.callback_query(F.data.startswith("lang:set:"))
async def language_set(callback: CallbackQuery, state: FSMContext, bot: Bot | None = None) -> None:
    lang = (callback.data or "").split(":")[-1]
    if lang not in SUPPORTED_LANGS:
        await callback.answer(t("unknown_language"), show_alert=True)
        return
    data = await state.get_data()
    data["lang"] = lang
    await state.set_data(data)
    if bot is not None and callback.message is not None:
        await set_menu_button(bot, lang, callback.message.chat.id)
    await callback.answer(language_label(lang))
    draft = get_draft(data)
    with use_lang(lang):
        if draft is not None:
            await send_preview(callback.message, state, draft)
            return
        try:
            await callback.message.edit_text(t("welcome"), reply_markup=welcome_kb())
        except TelegramBadRequest:
            await callback.message.answer(t("welcome"), reply_markup=welcome_kb())
