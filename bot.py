

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg_id = update.effective_user.id
    game = get_game()
    user = users.find_one({"telegram_id": tg_id})
    if not user:
        if game.get("status") == "running" and not is_admin(game, tg_id):
            await update.message.reply_text(
                "Игра уже идет, присоединиться нельзя.",
                reply_markup=START_KEYBOARD,
            )
            return
        is_admin_flag = is_admin(game, tg_id)
        number = None
        if not is_admin_flag:
            player_count = users.count_documents({"isAdmin": {"$ne": True}})
            if player_count >= 9:
                await update.message.reply_text(
                    "Нужное количество игроков уже в игре.",
                    reply_markup=START_KEYBOARD,
                )
                return
            number = player_count + 1
        users.insert_one(
            {
                "telegram_id": tg_id,
                "username": update.effective_user.username,
                "first_name": update.effective_user.first_name,
                "last_name": update.effective_user.last_name,
                "alive": True,
                "discovered_opponent_ids": [],
                "special_button_ids": [],
                "isAdmin": is_admin_flag,
                "number": number,
            }
        )
        user = users.find_one({"telegram_id": tg_id})
        if not is_admin_flag:
            square = number_to_square(number)
            circle = number_to_circle(number)
            buttons.update_one(
                {"number": number, "special": False},
                {
                    "$set": {
                        "taken": True,
                        "blocked": False,
                        "player_id": user["_id"],
                        "code_used": False,
                    }
                },
            )
            for admin_id in game.get("admin_ids", []):
                await context.bot.send_message(
                    admin_id,
                    f"Подключился игрок {get_name(user)} {square}{circle}",
                )
    if not user.get("alive", True):
        await update.message.reply_text(
            "Вас заблокировали 🚫. Игра окончена.", reply_markup=START_KEYBOARD
        )
        return
    if game.get("status") != "running":
        if is_admin(game, tg_id):
            await send_menu(tg_id, user, game, context)
        else:
            await update.message.reply_text(
                "Игра еще не началась.", reply_markup=START_KEYBOARD
            )
        return
    await send_menu(tg_id, user, game, context)











def main() -> None:
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))

    register_admin_handlers(application)

    application.run_polling()


if __name__ == "__main__":
    main()
