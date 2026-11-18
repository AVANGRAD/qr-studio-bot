from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from ..keyboards import help_kb, welcome_kb
from ..states import Flow
from ..texts import CONTENT_PROMPT, HELP, WELCOME

router = Router(name="start")


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(WELCOME, reply_markup=welcome_kb())


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    await message.answer(HELP, reply_markup=help_kb())


@router.callback_query(F.data == "menu:home")
async def menu_home(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    await callback.message.answer(WELCOME, reply_markup=welcome_kb())


@router.callback_query(F.data == "menu:help")
async def menu_help(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(HELP, reply_markup=help_kb())


@router.callback_query(F.data.in_({"menu:new", "draft:new"}))
async def menu_new(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(Flow.content)
    await callback.message.answer(CONTENT_PROMPT)
