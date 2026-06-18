# utils/bot.py
import asyncio
import logging
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ConversationHandler, CallbackQueryHandler, ContextTypes
)
from utils.db_handler import UserDB
from utils.output_handler import OutputHandler

logger = logging.getLogger(__name__)

# Состояния
REGISTER_USERNAME, REGISTER_PASSWORD, REGISTER_EMAIL = range(3)
LOGIN_USERNAME, LOGIN_PASSWORD = range(2)
CHANGE_PASS_OLD, CHANGE_PASS_NEW1, CHANGE_PASS_NEW2 = range(3)


class UPBBot:
    def __init__(self, token: str, request=None):
        self.token = token
        self.request = request
        self.app = None
        self.user_sessions = {}
        self.running = True

    # ============ КОМАНДЫ ============

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/start — приветствие и главное меню"""
        user_id = update.effective_user.id
        if user_id in self.user_sessions:
            token = self.user_sessions[user_id]
            if UserDB.verify_session(token):
                await self._show_main_menu(update, context)
                return

        keyboard = [
            [InlineKeyboardButton("🔐 Register", callback_data="register")],
            [InlineKeyboardButton("🔑 Login", callback_data="login")],
        ]
        await update.message.reply_text(
            "👋 *Welcome to UPB Parser Bot!*\n\n"
            "Please register or login to continue.\n\n"
            "📌 *Commands:*\n"
            "/start - Show this menu\n"
            "/help - Show all commands\n"
            "/menu - Main menu\n"
            "/results - My results\n"
            "/register - Register new account\n"
            "/login - Login to your account\n"
            "/changepass - Change password\n"
            "/logout - Logout\n"
            "/cancel - Cancel current operation",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/help — список всех команд"""
        help_text = """
📌 *Available Commands:*

/start - Show welcome menu
/help - Show this help message
/menu - Open main menu
/results - View your parsing results

🔐 *Authentication:*
/register - Create new account
/login - Login to your account
/logout - Logout from your account
/changepass - Change your password
/cancel - Cancel current operation

📊 *Results:*
After parsing, use /results to see your files.

🤖 *Bot Info:*
This bot stores your parsing results in personal folders.
Each user sees only their own data.

📝 *How to use:*
1. Register with /register
2. Login with /login
3. Run parser with --user='your_username'
4. View results with /results
"""
        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/menu — главное меню"""
        await self._show_main_menu(update, context)

    async def results_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/results — быстрый доступ к результатам"""
        user_id = update.effective_user.id
        token = self.user_sessions.get(user_id)

        db_user_id = UserDB.verify_session(token)
        if not db_user_id:
            await update.message.reply_text("❌ Please login first using /login")
            return

        projects = OutputHandler.get_user_projects(db_user_id)

        if not projects:
            await update.message.reply_text(
                "📊 No results found.\n\n"
                "Run the parser with:\n"
                "`--user='your_username'` in script.txt",
                parse_mode="Markdown"
            )
            return

        keyboard = []
        for project in projects:
            files = OutputHandler.get_user_files(db_user_id, project)
            keyboard.append([InlineKeyboardButton(f"📁 {project} ({len(files)} files)", callback_data=f"project_{project}")])

        keyboard.append([InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")])
        await update.message.reply_text(
            "📂 *Your projects:*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    async def register_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/register — быстрая регистрация"""
        await update.message.reply_text(
            "📝 *Registration*\n\n"
            "Enter username (min 3 chars) or /cancel:",
            parse_mode="Markdown"
        )
        return REGISTER_USERNAME

    async def login_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/login — быстрый логин"""
        await update.message.reply_text(
            "🔑 *Login*\n\n"
            "Enter username or /cancel:",
            parse_mode="Markdown"
        )
        return LOGIN_USERNAME

    async def changepass_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/changepass — смена пароля"""
        user_id = update.effective_user.id
        token = self.user_sessions.get(user_id)

        if not UserDB.verify_session(token):
            await update.message.reply_text("❌ Please login first using /login")
            return ConversationHandler.END

        await update.message.reply_text(
            "🔄 *Change Password*\n\n"
            "Enter current password or /cancel:",
            parse_mode="Markdown"
        )
        return CHANGE_PASS_OLD

    async def logout_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/logout — выход из аккаунта"""
        user_id = update.effective_user.id
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
        await update.message.reply_text("👋 Logged out successfully. Use /login to log back in.")

    # ============ ГЛАВНОЕ МЕНЮ ============

    async def _show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает главное меню с подсказками"""
        keyboard = [
            [InlineKeyboardButton("📊 My Results", callback_data="my_results")],
            [InlineKeyboardButton("🔄 Change Password", callback_data="change_pass")],
            [InlineKeyboardButton("🚪 Logout", callback_data="logout")],
        ]
        msg = (
            "🏠 *Main Menu*\n\n"
            "Type a command or use buttons:\n"
            "/results - View your results\n"
            "/changepass - Change password\n"
            "/logout - Logout\n"
            "/help - Show all commands"
        )
        if update.callback_query:
            await update.callback_query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    # ============ REGISTER ============
    async def register_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "📝 *Registration*\n\nEnter username (min 3 chars) or /cancel:",
            parse_mode="Markdown"
        )
        return REGISTER_USERNAME

    async def register_username(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        username = update.message.text.strip()
        if len(username) < 3:
            await update.message.reply_text(
                "❌ Min 3 chars. Try again or /cancel:",
                parse_mode="Markdown"
            )
            return REGISTER_USERNAME
        context.user_data["reg_username"] = username
        await update.message.reply_text(
            "🔐 Enter password (min 6 chars) or /cancel:",
            parse_mode="Markdown"
        )
        return REGISTER_PASSWORD

    async def register_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        password = update.message.text.strip()
        if len(password) < 6:
            await update.message.reply_text(
                "❌ Min 6 chars. Try again or /cancel:",
                parse_mode="Markdown"
            )
            return REGISTER_PASSWORD
        context.user_data["reg_password"] = password
        await update.message.reply_text(
            "📧 Enter email or /cancel:",
            parse_mode="Markdown"
        )
        return REGISTER_EMAIL

    async def register_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        email = update.message.text.strip()
        if "@" not in email:
            await update.message.reply_text(
                "❌ Invalid email. Try again or /cancel:",
                parse_mode="Markdown"
            )
            return REGISTER_EMAIL

        username = context.user_data["reg_username"]
        password = context.user_data["reg_password"]

        result = UserDB.register(username, password, email)
        if result["success"]:
            await update.message.reply_text(f"✅ Welcome, {username}!")
            login_result = UserDB.login(username, password)
            if login_result["success"]:
                token = UserDB.create_session(login_result["user_id"])
                self.user_sessions[update.effective_user.id] = token
                await self._show_main_menu(update, context)
            return ConversationHandler.END
        else:
            await update.message.reply_text(
                f"❌ {result['error']}\nTry /register again",
                parse_mode="Markdown"
            )
            return ConversationHandler.END

    # ============ LOGIN ============
    async def login_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "🔑 *Login*\n\nEnter username or /cancel:",
            parse_mode="Markdown"
        )
        return LOGIN_USERNAME

    async def login_username(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data["login_username"] = update.message.text.strip()
        await update.message.reply_text(
            "🔐 Enter password or /cancel:",
            parse_mode="Markdown"
        )
        return LOGIN_PASSWORD

    async def login_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        username = context.user_data["login_username"]
        password = update.message.text.strip()

        result = UserDB.login(username, password)
        if result["success"]:
            token = UserDB.create_session(result["user_id"])
            self.user_sessions[update.effective_user.id] = token
            await update.message.reply_text(f"✅ Welcome back, {username}!")
            await self._show_main_menu(update, context)
            return ConversationHandler.END
        else:
            await update.message.reply_text(
                f"❌ {result['error']}\nTry /login again",
                parse_mode="Markdown"
            )
            return ConversationHandler.END

    # ============ CHANGE PASSWORD ============
    async def change_pass_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "🔄 *Change Password*\n\nEnter current password or /cancel:",
            parse_mode="Markdown"
        )
        return CHANGE_PASS_OLD

    async def change_pass_old(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        old_pass = update.message.text.strip()
        user_id = update.effective_user.id
        token = self.user_sessions.get(user_id)

        db_user_id = UserDB.verify_session(token)
        if not db_user_id:
            await update.message.reply_text(
                "❌ Session expired. Use /start",
                parse_mode="Markdown"
            )
            return ConversationHandler.END

        conn = UserDB.get_db()
        user = conn.execute("SELECT username, password_hash FROM users WHERE id = ?", (db_user_id,)).fetchone()
        conn.close()

        if not user or not UserDB.verify_password(old_pass, user["password_hash"]):
            await update.message.reply_text(
                "❌ Wrong password. Try again or /cancel:",
                parse_mode="Markdown"
            )
            return CHANGE_PASS_OLD

        context.user_data["change_username"] = user["username"]
        await update.message.reply_text(
            "✅ Enter NEW password (min 6 chars) or /cancel:",
            parse_mode="Markdown"
        )
        return CHANGE_PASS_NEW1

    async def change_pass_new1(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        new_pass = update.message.text.strip()
        if len(new_pass) < 6:
            await update.message.reply_text(
                "❌ Min 6 chars. Try again or /cancel:",
                parse_mode="Markdown"
            )
            return CHANGE_PASS_NEW1
        context.user_data["change_new_pass"] = new_pass
        await update.message.reply_text(
            "🔄 Confirm new password or /cancel:",
            parse_mode="Markdown"
        )
        return CHANGE_PASS_NEW2

    async def change_pass_new2(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        confirm = update.message.text.strip()
        new_pass = context.user_data["change_new_pass"]

        if new_pass != confirm:
            await update.message.reply_text(
                "❌ Passwords don't match. Try again or /cancel:",
                parse_mode="Markdown"
            )
            return CHANGE_PASS_NEW2

        result = UserDB.update_password(context.user_data["change_username"], new_pass)
        if result["success"]:
            await update.message.reply_text("✅ Password changed!")
        else:
            await update.message.reply_text(f"❌ {result['error']}")
        await self._show_main_menu(update, context)
        return ConversationHandler.END

    # ============ RESULTS ============
    async def my_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.callback_query.answer()

        user_id = update.effective_user.id
        token = self.user_sessions.get(user_id)

        db_user_id = UserDB.verify_session(token)
        if not db_user_id:
            await update.callback_query.edit_message_text("❌ Session expired. /start")
            return

        projects = OutputHandler.get_user_projects(db_user_id)

        if not projects:
            await update.callback_query.edit_message_text(
                "📊 No results found.\n\n"
                "Run the parser with:\n"
                "`--user='your_username'` in script.txt",
                parse_mode="Markdown"
            )
            return

        keyboard = []
        for project in projects:
            files = OutputHandler.get_user_files(db_user_id, project)
            keyboard.append([InlineKeyboardButton(f"📁 {project} ({len(files)} files)", callback_data=f"project_{project}")])

        keyboard.append([InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")])
        await update.callback_query.edit_message_text(
            "📂 *Your projects:*\n\nSelect a project to view files:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    async def select_project(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.callback_query.answer()

        user_id = update.effective_user.id
        token = self.user_sessions.get(user_id)
        db_user_id = UserDB.verify_session(token)

        if not db_user_id:
            await update.callback_query.edit_message_text("❌ Session expired.")
            return

        project = update.callback_query.data.replace("project_", "")
        files = OutputHandler.get_user_files(db_user_id, project)

        if not files:
            await update.callback_query.edit_message_text(f"📁 No files in {project}")
            return

        keyboard = []
        for f in files[:10]:
            size_kb = f["size"] // 1024
            keyboard.append([
                InlineKeyboardButton(
                    f"📄 {f['name']} ({size_kb} KB, {f['records']} records)",
                    callback_data=f"file_{f['id']}"
                )
            ])

        keyboard.append([InlineKeyboardButton("🔙 Back to projects", callback_data="my_results")])
        await update.callback_query.edit_message_text(
            f"📂 *Files in {project}:*\n\nTap a file to download:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    async def download_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.callback_query.answer()

        user_id = update.effective_user.id
        token = self.user_sessions.get(user_id)
        db_user_id = UserDB.verify_session(token)

        if not db_user_id:
            await update.callback_query.edit_message_text("❌ Session expired.")
            return

        result_id = int(update.callback_query.data.replace("file_", ""))
        result = UserDB.get_result_by_id(result_id, db_user_id)

        if not result:
            await update.callback_query.edit_message_text("❌ File not found or access denied")
            return

        file_path = Path(result["file_path"])
        if not file_path.exists():
            await update.callback_query.edit_message_text("❌ File not found on server")
            return

        with open(file_path, "rb") as f:
            await update.callback_query.message.reply_document(
                document=f,
                filename=result["file_name"],
                caption=f"📄 {result['file_name']}\nFrom: {result['project_name']}\nRecords: {result['records']}"
            )

    # ============ LOGOUT ============
    async def logout(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.callback_query.answer()
        user_id = update.effective_user.id
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]

        keyboard = [
            [InlineKeyboardButton("🔐 Register", callback_data="register")],
            [InlineKeyboardButton("🔑 Login", callback_data="login")],
        ]
        await update.callback_query.edit_message_text(
            "👋 Logged out.\n\nUse /login to log back in.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def main_menu_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.callback_query.answer()
        await self._show_main_menu(update, context)

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("❌ Cancelled. Use /menu to return.")
        await self._show_main_menu(update, context)
        return ConversationHandler.END

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений — показывает подсказки"""
        text = update.message.text.strip()

        # Игнорируем команды (они обрабатываются отдельно)
        if text.startswith('/'):
            return

        # Проверяем, есть ли активная сессия
        user_id = update.effective_user.id
        token = self.user_sessions.get(user_id)

        # Если есть сессия — показываем меню с подсказками
        if token and UserDB.verify_session(token):
            keyboard = [
                [InlineKeyboardButton("📊 My Results", callback_data="my_results")],
                [InlineKeyboardButton("🔄 Change Password", callback_data="change_pass")],
                [InlineKeyboardButton("🚪 Logout", callback_data="logout")],
            ]
            await update.message.reply_text(
                "🤔 *Unknown command or text.*\n\n"
                "📌 *Available commands:*\n"
                "/start - Show menu\n"
                "/help - Show all commands\n"
                "/results - My results\n"
                "/changepass - Change password\n"
                "/logout - Logout\n\n"
                "Or use the buttons below:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            # Если нет сессии — показываем команды для входа
            keyboard = [
                [InlineKeyboardButton("🔐 Register", callback_data="register")],
                [InlineKeyboardButton("🔑 Login", callback_data="login")],
            ]
            await update.message.reply_text(
                "🤔 *Unknown command.*\n\n"
                "📌 *Available commands:*\n"
                "/start - Show menu\n"
                "/help - Show all commands\n"
                "/register - Register new account\n"
                "/login - Login to your account\n\n"
                "Or use the buttons below:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )

    async def unknown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик неизвестных команд"""
        await update.message.reply_text(
            "❌ Unknown command.\n\n"
            "Use /help to see all available commands.\n"
            "Or type /start to begin."
        )

    # ============ RUN ============

    async def run(self):
        builder = Application.builder().token(self.token)
        if self.request:
            builder.request(self.request)
        self.app = builder.build()
        
        # ===== Command handlers =====
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("menu", self.menu_command))
        self.app.add_handler(CommandHandler("results", self.results_command))
        self.app.add_handler(CommandHandler("register", self.register_command))
        self.app.add_handler(CommandHandler("login", self.login_command))
        self.app.add_handler(CommandHandler("logout", self.logout_command))
        self.app.add_handler(CommandHandler("changepass", self.changepass_command))
        self.app.add_handler(CommandHandler("cancel", self.cancel))

        # ===== Conversation handlers =====
        # Регистрация
        reg_conv = ConversationHandler(
            entry_points=[
                CommandHandler("register", self.register_command),
                CallbackQueryHandler(self.register_start, pattern="^register$")
            ],
            states={
                REGISTER_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.register_username)],
                REGISTER_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.register_password)],
                REGISTER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.register_email)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )
        self.app.add_handler(reg_conv)

        # Логин
        login_conv = ConversationHandler(
            entry_points=[
                CommandHandler("login", self.login_command),
                CallbackQueryHandler(self.login_start, pattern="^login$")
            ],
            states={
                LOGIN_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.login_username)],
                LOGIN_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.login_password)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )
        self.app.add_handler(login_conv)

        # Смена пароля
        change_conv = ConversationHandler(
            entry_points=[
                CommandHandler("changepass", self.changepass_command),
                CallbackQueryHandler(self.change_pass_start, pattern="^change_pass$")
            ],
            states={
                CHANGE_PASS_OLD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.change_pass_old)],
                CHANGE_PASS_NEW1: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.change_pass_new1)],
                CHANGE_PASS_NEW2: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.change_pass_new2)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )
        self.app.add_handler(change_conv)

        # ===== Callback handlers =====
        self.app.add_handler(CallbackQueryHandler(self.my_results, pattern="^my_results$"))
        self.app.add_handler(CallbackQueryHandler(self.select_project, pattern="^project_"))
        self.app.add_handler(CallbackQueryHandler(self.download_file, pattern="^file_"))
        self.app.add_handler(CallbackQueryHandler(self.main_menu_callback, pattern="^main_menu$"))
        self.app.add_handler(CallbackQueryHandler(self.logout, pattern="^logout$"))

        # ===== Обработчик текстовых сообщений (подсказки) =====
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))

        # ===== Fallback для неизвестных команд =====
        self.app.add_handler(MessageHandler(filters.COMMAND, self.unknown_command))

        logger.info("🤖 Bot started! Commands: /start, /help, /menu, /results, /register, /login, /logout, /changepass, /cancel")
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()

        while self.running:
            await asyncio.sleep(1)