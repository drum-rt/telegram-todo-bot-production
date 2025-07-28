#!/usr/bin/env python3
"""
Todo Bot GitHub Actions Production - Безкоштовний 24/7 хостинг
Based on bot_v3.py with GitHub Actions optimizations
"""
import os
import json
import logging
import time
import signal
import sys
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class TodoBot:
    def __init__(self):
        self.data_file = 'todos_data.json'
        self.users_data = {}
        self.running = True
        self.load_data()
        
        # Обробка сигналів для коректного завершення
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)

    def signal_handler(self, signum, frame):
        logger.info(f"Отримано сигнал {signum}, завершуємо роботу...")
        self.running = False
        self.save_data()
        sys.exit(0)

    def load_data(self):
        """Завантаження даних користувачів"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.users_data = data.get('users', {})
                logger.info(f"Завантажено {len(self.users_data)} користувачів з {self.data_file}")
            else:
                logger.info("Файл даних не знайдено, починаємо з порожнього списку")
        except Exception as e:
            logger.error(f"Помилка завантаження даних: {e}")

    def save_data(self):
        """Збереження даних користувачів"""
        try:
            data = {'users': self.users_data}
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Дані збережено для {len(self.users_data)} користувачів")
        except Exception as e:
            logger.error(f"Помилка збереження даних: {e}")

    def get_user_data(self, user_id):
        """Отримання даних користувача"""
        user_id = str(user_id)
        if user_id not in self.users_data:
            self.users_data[user_id] = {
                'todos': [],
                'next_id': 1,
                'sections': ['Закупівля', 'Гараж', 'Волинка', 'Виконано']
            }
        return self.users_data[user_id]

    def format_todo_list(self, user_data):
        """Форматування списку завдань"""
        if not user_data['todos']:
            return "📝 Список порожній\n\nДодайте завдання надіславши текст або натисніть кнопку."
        
        sections = user_data['sections']
        todos_by_section = [[] for _ in range(4)]
        
        for todo in user_data['todos']:
            section_idx = todo.get('section', 0)
            if 0 <= section_idx < 4:
                todos_by_section[section_idx].append(todo)
        
        result = []
        display_number = 1
        
        for i in range(3):  # Перші 3 секції (активні)
            section_todos = todos_by_section[i]
            if section_todos:
                if i == 0:
                    result.append(f"🛒 {sections[i]}:")
                elif i == 1:
                    result.append(f"🔧 {sections[i]}:")
                elif i == 2:
                    result.append(f"🎵 {sections[i]}:")
                
                for todo in section_todos:
                    text = todo['text']
                    if todo.get('crossed_out', False):
                        text = ''.join(char + '\u0336' for char in text)
                    result.append(f"{display_number}. {text}")
                    display_number += 1
                result.append("")
        
        # Секція "Виконано"
        completed_todos = todos_by_section[3]
        if completed_todos:
            result.append("▼▼▼ Виконано ▼▼▼")
            for todo in completed_todos:
                text = todo['text']
                result.append(f"❌ {display_number}. {text}")
                display_number += 1
            result.append("")
        
        # Статистика
        total = len(user_data['todos'])
        completed = len(completed_todos)
        active = total - completed
        
        result.append(f"Всього: {total} | Активних: {active} | Виконано: {completed}")
        
        return '\n'.join(result)

    def get_main_keyboard(self):
        """Основна клавіатура з кнопкою меню"""
        keyboard = [[KeyboardButton("📋 Меню")]]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

    def get_commands_keyboard(self):
        """Клавіатура з командами"""
        keyboard = [
            [KeyboardButton("📄 Список"), KeyboardButton("🆕 Новий")],
            [KeyboardButton("↩️ Відновити"), KeyboardButton("🔄 Продовжити")],
            [KeyboardButton("⚙️ Налаштування"), KeyboardButton("❓ Допомога")],
            [KeyboardButton("🔙 Назад")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        user_id = update.effective_user.id
        user_data = self.get_user_data(user_id)
        
        welcome_text = (
            "🎯 **Todo Bot v3.0 Production**\n\n"
            "Організовуйте завдання за секціями:\n"
            "🛒 Закупівля\n"
            "🔧 Гараж  \n" 
            "🎵 Волинка\n"
            "❌ Виконано\n\n"
            "📝 Надішліть текст щоб додати завдання\n"
            "🔢 Введіть номер щоб перекреслити\n"
            "➖ Введіть -номер щоб видалити\n"
            "🔀 Введіть номер1+номер2 щоб об'єднати\n\n"
            "Натисніть **📋 Меню** для всіх команд"
        )
        
        await self._send_message(update, welcome_text, self.get_main_keyboard())
        self.save_data()

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help"""
        help_text = (
            "📚 **Довідка Todo Bot v3.0**\n\n"
            "**Базові команди:**\n"
            "• Текст - додати завдання\n"
            "• Номер - перекреслити/розкреслити\n"
            "• -номер - видалити завдання\n"
            "• номер1+номер2 - об'єднати завдання\n\n"
            "**Переміщення між секціями:**\n"
            "• номерз - в Закупівлю\n"
            "• номерг - в Гараж\n"
            "• номерв - в Волинку\n\n"
            "**Префікси при додаванні:**\n"
            "• ! текст - одразу в Гараж\n"
            "• !! текст - одразу в Волинку\n\n"
            "**Кнопки меню:**\n"
            "📄 Список - показати всі завдання\n"
            "🆕 Новий - очистити список\n"
            "↩️ Відновити - повернути останній список\n"
            "🔄 Продовжити - видалити виконані\n"
            "⚙️ Налаштування - налаштувати секції\n\n"
            "🤖 GitHub Actions Production v1.0"
        )
        
        await self._send_message(update, help_text, self.get_main_keyboard())

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обробка текстових повідомлень"""
        if not update.message or not update.message.text:
            return
            
        user_id = update.effective_user.id
        text = update.message.text.strip()
        user_data = self.get_user_data(user_id)
        
        # Видалення повідомлення користувача (якщо можливо)
        try:
            await update.message.delete()
            await context.bot.delete_message(update.effective_chat.id, update.message.message_id)
        except:
            pass
        
        # Обробка кнопок меню
        if text == "📋 Меню":
            await self._send_message(update, "Оберіть дію:", self.get_commands_keyboard())
            return
        elif text == "🔙 Назад":
            await self._send_message(update, "Головне меню:", self.get_main_keyboard())
            return
        elif text == "📄 Список":
            list_text = self.format_todo_list(user_data)
            await self._send_message(update, list_text, self.get_main_keyboard())
            return
        elif text == "🆕 Новий":
            self.create_new_list(user_data)
            await self._send_message(update, "✅ Створено новий список", self.get_main_keyboard())
            self.save_data()
            return
        elif text == "↩️ Відновити":
            self.restore_last_list(user_data)
            list_text = self.format_todo_list(user_data)
            await self._send_message(update, list_text, self.get_main_keyboard())
            self.save_data()
            return
        elif text == "🔄 Продовжити":
            self.continue_list(user_data)
            list_text = self.format_todo_list(user_data)
            await self._send_message(update, list_text, self.get_main_keyboard())
            self.save_data()
            return
        elif text == "❓ Допомога":
            await self.help_command(update, context)
            return
        elif text == "⚙️ Налаштування":
            settings_text = self.get_settings_text(user_data)
            await self._send_message(update, settings_text, self.get_main_keyboard())
            return
        
        # Обробка команд над завданнями
        if self.handle_todo_command(user_data, text):
            list_text = self.format_todo_list(user_data)
            await self._send_message(update, list_text, self.get_main_keyboard())
            self.save_data()
        else:
            # Додавання нового завдання
            self.add_todo_from_text(user_data, text)
            list_text = self.format_todo_list(user_data)
            await self._send_message(update, list_text, self.get_main_keyboard())
            self.save_data()

    def handle_todo_command(self, user_data, text):
        """Обробка команд над завданнями"""
        # Видалення завдання (-номер)
        if text.startswith('-') and text[1:].isdigit():
            todo_num = int(text[1:])
            return self.remove_todo_by_number(user_data, todo_num)
        
        # Перекреслювання (номер)
        if text.isdigit():
            todo_num = int(text)
            return self.toggle_todo_by_number(user_data, todo_num)
        
        # Об'єднання завдань (номер1+номер2)
        if '+' in text:
            parts = text.split('+')
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                num1, num2 = int(parts[0]), int(parts[1])
                return self.merge_todos(user_data, num1, num2)
        
        # Переміщення між секціями
        if text.endswith(('з', 'г', 'в')):
            section_map = {'з': 0, 'г': 1, 'в': 2}
            base_text = text[:-1]
            if base_text.isdigit():
                todo_num = int(base_text)
                section_idx = section_map[text[-1]]
                return self.move_todo_to_section(user_data, todo_num, section_idx)
        
        return False

    def add_todo_from_text(self, user_data, text):
        """Додавання завдання з тексту"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        for line in lines:
            section_idx = 0  # За замовчуванням в Закупівлю
            
            # Визначення секції за префіксом
            if line.startswith('!!'):
                section_idx = 2  # Волинка
                line = line[2:].strip()
            elif line.startswith('!'):
                section_idx = 1  # Гараж
                line = line[1:].strip()
            
            if line:
                todo = {
                    'id': user_data['next_id'],
                    'text': line,
                    'section': section_idx,
                    'crossed_out': False
                }
                user_data['todos'].append(todo)
                user_data['next_id'] += 1

    def remove_todo_by_number(self, user_data, display_number):
        """Видалення завдання за номером"""
        todo = self.get_todo_by_display_number(user_data, display_number)
        if todo:
            user_data['todos'].remove(todo)
            return True
        return False

    def toggle_todo_by_number(self, user_data, display_number):
        """Перекреслювання завдання за номером"""
        todo = self.get_todo_by_display_number(user_data, display_number)
        if todo:
            todo['crossed_out'] = not todo.get('crossed_out', False)
            
            # Автоматичне переміщення при перекресленні
            if todo['crossed_out'] and todo['section'] != 3:
                todo['section'] = 3  # В "Виконано"
            elif not todo['crossed_out'] and todo['section'] == 3:
                todo['section'] = 0  # Назад в "Закупівлю"
            
            return True
        return False

    def merge_todos(self, user_data, num1, num2):
        """Об'єднання двох завдань"""
        todo1 = self.get_todo_by_display_number(user_data, num1)
        todo2 = self.get_todo_by_display_number(user_data, num2)
        
        if todo1 and todo2 and todo1 != todo2:
            todo1['text'] = f"{todo1['text']} {todo2['text']}"
            user_data['todos'].remove(todo2)
            return True
        return False

    def move_todo_to_section(self, user_data, display_number, section_idx):
        """Переміщення завдання в секцію"""
        todo = self.get_todo_by_display_number(user_data, display_number)
        if todo:
            todo['section'] = section_idx
            if section_idx == 3:  # В "Виконано"
                todo['crossed_out'] = True
            else:
                todo['crossed_out'] = False
            return True
        return False

    def get_todo_by_display_number(self, user_data, display_number):
        """Отримання завдання за відображуваним номером"""
        todos_by_section = [[] for _ in range(4)]
        
        for todo in user_data['todos']:
            section_idx = todo.get('section', 0)
            if 0 <= section_idx < 4:
                todos_by_section[section_idx].append(todo)
        
        current_number = 1
        for i in range(4):
            for todo in todos_by_section[i]:
                if current_number == display_number:
                    return todo
                current_number += 1
        
        return None

    def create_new_list(self, user_data):
        """Створення нового списку з бекапом"""
        user_data['backup_todos'] = user_data['todos'].copy()
        user_data['todos'] = []
        user_data['next_id'] = 1

    def restore_last_list(self, user_data):
        """Відновлення останнього списку"""
        if 'backup_todos' in user_data:
            user_data['todos'] = user_data['backup_todos'].copy()
            if user_data['todos']:
                max_id = max(todo['id'] for todo in user_data['todos'])
                user_data['next_id'] = max_id + 1

    def continue_list(self, user_data):
        """Видалення виконаних завдань"""
        user_data['todos'] = [todo for todo in user_data['todos'] if todo.get('section', 0) != 3]

    def get_settings_text(self, user_data):
        """Текст налаштувань"""
        sections = user_data['sections']
        text = "⚙️ **Налаштування секцій**\n\n"
        text += f"🛒 Секція 1: {sections[0]}\n"
        text += f"🔧 Секція 2: {sections[1]}\n"
        text += f"🎵 Секція 3: {sections[2]}\n"
        text += f"❌ Секція 4: {sections[3]}\n\n"
        text += "Для зміни назв секцій - напишіть мені в Telegram"
        return text

    async def _send_message(self, update: Update, text: str, keyboard=None):
        """Відправка повідомлення з обробкою помилок"""
        try:
            await update.effective_chat.send_message(
                text=text,
                reply_markup=keyboard,
                parse_mode=None,
                disable_notification=True
            )
        except Exception as e:
            try:
                # Спроба без форматування
                await update.effective_chat.send_message(
                    text=text.replace('**', '').replace('*', ''),
                    reply_markup=keyboard,
                    disable_notification=True
                )
            except Exception as e2:
                logger.error(f"Помилка відправки повідомлення: {e2}")

def main():
    """Головна функція"""
    # Отримання токена з змінних середовища
    token = os.getenv('TELEGRAM_BOT_TOKEN_PRODUCTION')
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN_PRODUCTION не встановлено!")
        sys.exit(1)
    
    logger.info("🚀 Запуск Todo Bot GitHub Actions Production...")
    
    # Ініціалізація бота
    bot = TodoBot()
    
    # Створення додатку
    application = Application.builder().token(token).build()
    
    # Реєстрація обробників
    application.add_handler(CommandHandler("start", bot.start_command))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    try:
        logger.info("Todo Bot запущено успішно!")
        
        # Запуск в режимі polling з таймаутом
        start_time = time.time()
        
        while bot.running and (time.time() - start_time) < 1500:  # 25 хвилин
            try:
                application.run_polling(
                    timeout=10,
                    poll_interval=2.0,
                    drop_pending_updates=True
                )
            except Exception as e:
                logger.error(f"Помилка в polling: {e}")
                time.sleep(5)
                
        logger.info("✅ Завершуємо роботу після 25 хвилин")
        
    except Exception as e:
        logger.error(f"Критична помилка: {e}")
    finally:
        bot.save_data()
        logger.info("📊 Дані збережено, бот завершив роботу")

if __name__ == '__main__':
    main()