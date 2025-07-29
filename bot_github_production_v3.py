#!/usr/bin/env python3
"""
Todo Bot GitHub Actions Production v3.0 - Стабільна версія з виправленими функціями
Based on main.py with GitHub Actions optimizations and embedded data
"""
import os
import json
import logging
import time
import signal
import sys
import asyncio
from typing import Dict, List, Optional
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

class TodoItem:
    """Клас для представлення окремого завдання."""
    
    def __init__(self, text: str, item_id: int, section: str = "закупівля"):
        self.text = text
        self.item_id = item_id
        self.crossed_out = False
        self.section = section

class TodoManager:
    """Менеджер списків завдань з JSON персистентністю та embedded backup."""
    
    def __init__(self, storage_file: str = "todos_data.json"):
        self.storage_file = storage_file
        self.user_todos: Dict[int, List[TodoItem]] = {}
        self.next_ids: Dict[int, int] = {}
        self.backups: Dict[int, List[TodoItem]] = {}
        self._load_data()
    
    def _load_data(self):
        """Завантаження даних з JSON або embedded backup."""
        # Спочатку завжди завантажуємо embedded дані
        self._load_embedded_data()
        
        # Потім перевіряємо чи є збережений файл для оновлення
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Підтримка обох форматів: v2.5 (todos) та v3.0 (users)
                users_data = data.get('users', {}) or data.get('todos', {})
                
                if users_data:  # Тільки якщо є реальні дані
                    self.user_todos.clear()
                    self.next_ids.clear()
                    
                    for user_id_str, user_data in users_data.items():
                        user_id = int(user_id_str)
                        self.user_todos[user_id] = []
                        
                        # v3.0 формат має todos всередині user_data
                        todos_list = user_data.get('todos', user_data) if isinstance(user_data, dict) else user_data
                        
                        for item_data in todos_list:
                            item_id = item_data.get('id') or item_data.get('item_id')
                            section = item_data.get('section', 'закупівля')
                            # Якщо section - це число, конвертуємо
                            if isinstance(section, int):
                                section_map = {0: 'закупівля', 1: 'гараж', 2: 'волинка', 3: 'виконано'}
                                section = section_map.get(section, 'закупівля')
                            
                            todo = TodoItem(item_data['text'], item_id, section)
                            todo.crossed_out = item_data.get('crossed_out', False)
                            self.user_todos[user_id].append(todo)
                    
                    # Завантаження next_ids з різних форматів
                    if 'next_ids' in data:
                        for user_id_str, next_id in data['next_ids'].items():
                            self.next_ids[int(user_id_str)] = next_id
                    else:
                        # Для v3.0 формату next_id знаходиться всередині user_data
                        for user_id_str, user_data in users_data.items():
                            if isinstance(user_data, dict) and 'next_id' in user_data:
                                self.next_ids[int(user_id_str)] = user_data['next_id']
                    
                    logger.info(f"Оновлено даними з файлу: {len(self.user_todos)} користувачів")
                else:
                    logger.info("Файл даних порожній, використовуємо embedded дані")
                    
            except Exception as e:
                logger.error(f"Помилка завантаження збереженого файлу: {e}, використовуємо embedded дані")
    
    def _load_embedded_data(self):
        """Завантаження вбудованих даних для GitHub Actions."""
        logger.info("Завантаження вбудованих початкових даних")
        embedded_data = {
            -1002138020601: [
                {"id": 1, "text": "Кокосове згущене молоко 0.200 Кокосове згущене молоко 0.320", "section": "закупівля", "crossed_out": False},
                {"id": 3, "text": "Средство для мытья посуды, остаток: 4шт. Болотова 13шт у базі", "section": "закупівля", "crossed_out": False},
                {"id": 8, "text": "Жмых конопля", "section": "закупівля", "crossed_out": False},
                {"id": 13, "text": "Чернобривці", "section": "закупівля", "crossed_out": False},
                {"id": 25, "text": "Семечка подсолнух", "section": "волинка", "crossed_out": False},
                {"id": 33, "text": "Салатна суміш", "section": "закупівля", "crossed_out": False},
                {"id": 37, "text": "чиа,", "section": "закупівля", "crossed_out": False},
                {"id": 38, "text": "мак,", "section": "закупівля", "crossed_out": False},
                {"id": 41, "text": "подсолнечное ост7 бутылок на ветрине,", "section": "закупівля", "crossed_out": False},
                {"id": 49, "text": "Полынь", "section": "закупівля", "crossed_out": False},
                {"id": 52, "text": "Наклейки :сорный кмин(есть 2).,лиано для капсул.,лиано порошок.,сода1000(есть 8)", "section": "закупівля", "crossed_out": False},
                {"id": 54, "text": "Дай пак-18/28.,13/20", "section": "закупівля", "crossed_out": False},
                {"id": 55, "text": "Наклейки. Сода 0.150", "section": "закупівля", "crossed_out": False},
                {"id": 56, "text": "Зубная паста", "section": "закупівля", "crossed_out": False},
                {"id": 58, "text": "Касторова олія", "section": "закупівля", "crossed_out": False},
                {"id": 62, "text": "Нут", "section": "волинка", "crossed_out": False},
                {"id": 69, "text": "Сода", "section": "закупівля", "crossed_out": False},
                {"id": 71, "text": "Горіх волоський", "section": "волинка", "crossed_out": False}
            ],
            -1002581954453: [
                {"id": 39, "text": "металевий блін для Павлика", "section": "закупівля", "crossed_out": False}
            ]
        }
        
        for user_id, todos_data in embedded_data.items():
            self.user_todos[user_id] = []
            for todo_data in todos_data:
                todo = TodoItem(todo_data['text'], todo_data['id'], todo_data['section'])
                todo.crossed_out = todo_data['crossed_out']
                self.user_todos[user_id].append(todo)
            
            # Встановлення next_id
            if todos_data:
                max_id = max(item['id'] for item in todos_data)
                self.next_ids[user_id] = max_id + 1
            else:
                self.next_ids[user_id] = 1
        
        self._save_data()
        logger.info(f"Створено початкові дані для {len(embedded_data)} користувачів")
    
    def _save_data(self):
        """Збереження даних у JSON."""
        try:
            data = {
                'todos': {},
                'next_ids': self.next_ids
            }
            
            for user_id, todos in self.user_todos.items():
                data['todos'][str(user_id)] = [
                    {
                        'id': todo.item_id,
                        'text': todo.text,
                        'crossed_out': todo.crossed_out,
                        'section': todo.section
                    } for todo in todos
                ]
            
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Помилка збереження даних: {e}")
    
    def add_todo(self, user_id: int, text: str) -> TodoItem:
        """Додавання нового завдання."""
        if user_id not in self.user_todos:
            self.user_todos[user_id] = []
            self.next_ids[user_id] = 1
        
        # Визначення секції за префіксами
        section = "закупівля"
        if text.startswith("!!"):
            section = "волинка"
            text = text[2:].strip()
        elif text.startswith("!"):
            section = "гараж"
            text = text[1:].strip()
        
        todo = TodoItem(text, self.next_ids[user_id], section)
        self.user_todos[user_id].append(todo)
        self.next_ids[user_id] += 1
        self._save_data()
        return todo
    
    def get_formatted_list(self, user_id: int) -> str:
        """Отримання відформатованого списку завдань."""
        if user_id not in self.user_todos or not self.user_todos[user_id]:
            return "📝 Список завдань порожній"
        
        todos = self.user_todos[user_id]
        sections = {
            "закупівля": "🛒 Закупівля",
            "гараж": "🔧 Гараж", 
            "волинка": "🎯 Волинка",
            "виконано": "✅ Виконано"
        }
        
        result = []
        display_num = 1
        
        # Показуємо активні секції
        for section_key in ["закупівля", "гараж", "волинка"]:
            section_todos = [t for t in todos if t.section == section_key and not t.crossed_out]
            if section_todos:
                result.append(f"\n{sections[section_key]}")
                for todo in section_todos:
                    result.append(f"{display_num}. {todo.text}")
                    display_num += 1
        
        # Показуємо виконані завдання
        completed_todos = [t for t in todos if t.crossed_out or t.section == "виконано"]
        if completed_todos:
            result.append(f"\n{sections['виконано']}")
            for todo in completed_todos:
                crossed_text = ''.join(char + '\u0336' for char in todo.text)
                result.append(f"{display_num}. {crossed_text}")
                display_num += 1
        
        return '\n'.join(result)
    
    def get_todo_by_display_number(self, user_id: int, display_num: int) -> Optional[TodoItem]:
        """Отримання завдання за відображуваним номером."""
        if user_id not in self.user_todos:
            return None
        
        todos = self.user_todos[user_id]
        ordered = []
        
        # Порядок: активні секції, потім виконані
        for section in ["закупівля", "гараж", "волинка"]:
            ordered.extend([t for t in todos if t.section == section and not t.crossed_out])
        
        ordered.extend([t for t in todos if t.crossed_out or t.section == "виконано"])
        
        if 1 <= display_num <= len(ordered):
            return ordered[display_num - 1]
        return None
    
    def remove_todo(self, user_id: int, display_num: int) -> bool:
        """Видалення завдання за відображуваним номером."""
        todo = self.get_todo_by_display_number(user_id, display_num)
        if todo and user_id in self.user_todos:
            self.user_todos[user_id].remove(todo)
            self._save_data()
            return True
        return False
    
    def toggle_todo(self, user_id: int, display_num: int) -> bool:
        """Перемикання стану перекреслення завдання."""
        todo = self.get_todo_by_display_number(user_id, display_num)
        if todo:
            todo.crossed_out = not todo.crossed_out
            # Переміщення між секціями
            if todo.crossed_out:
                todo.section = "виконано"
            else:
                todo.section = "закупівля"
            self._save_data()
            return True
        return False
    
    def move_todo_to_section(self, user_id: int, display_num: int, target_section: str) -> bool:
        """Переміщення завдання в іншу секцію."""
        todo = self.get_todo_by_display_number(user_id, display_num)
        if todo:
            todo.section = target_section
            if target_section == "виконано":
                todo.crossed_out = True
            else:
                todo.crossed_out = False
            self._save_data()
            return True
        return False
    
    def merge_todos(self, user_id: int, first_num: int, second_num: int) -> bool:
        """Об'єднання двох завдань."""
        first_todo = self.get_todo_by_display_number(user_id, first_num)
        second_todo = self.get_todo_by_display_number(user_id, second_num)
        
        if first_todo and second_todo and first_todo != second_todo:
            first_todo.text = f"{first_todo.text} {second_todo.text}"
            self.user_todos[user_id].remove(second_todo)
            self._save_data()
            return True
        return False
    
    def clear_todos(self, user_id: int) -> int:
        """Очищення всіх завдань з резервним копіюванням."""
        if user_id in self.user_todos:
            count = len(self.user_todos[user_id])
            if count > 0:
                self.backups[user_id] = self.user_todos[user_id].copy()
            self.user_todos[user_id] = []
            self._save_data()
            return count
        return 0
    
    def restore_backup(self, user_id: int) -> int:
        """Відновлення резервної копії завдань."""
        if user_id in self.backups and self.backups[user_id]:
            self.user_todos[user_id] = self.backups[user_id].copy()
            count = len(self.backups[user_id])
            self.backups[user_id] = []
            self._save_data()
            return count
        return 0
    
    def continue_list(self, user_id: int) -> int:
        """Видалення виконаних завдань."""
        if user_id not in self.user_todos:
            return 0
        
        completed = [t for t in self.user_todos[user_id] if t.crossed_out or t.section == "виконано"]
        if completed:
            self.backups[user_id] = completed.copy()
            self.user_todos[user_id] = [t for t in self.user_todos[user_id] 
                                       if not t.crossed_out and t.section != "виконано"]
            self._save_data()
            return len(completed)
        return 0

class CleanTodoBot:
    """Чистий, оптимізований todo бот для GitHub Actions."""
    
    def __init__(self):
        self.manager = TodoManager()
        self.running = True
        
        # Обробка сигналів
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        # Оптимізація: кешування клавіатур
        self._main_keyboard = None
        self._commands_keyboard = None
    
    def signal_handler(self, signum, frame):
        logger.info(f"Отримано сигнал {signum}, завершуємо роботу...")
        self.running = False
        sys.exit(0)
    
    def get_main_keyboard(self):
        """Кешована основна клавіатура."""
        if not self._main_keyboard:
            self._main_keyboard = ReplyKeyboardMarkup(
                [[KeyboardButton("📋 Меню")]],
                resize_keyboard=True,
                one_time_keyboard=False
            )
        return self._main_keyboard
    
    def get_commands_keyboard(self):
        """Кешована клавіатура з командами."""
        if not self._commands_keyboard:
            self._commands_keyboard = ReplyKeyboardMarkup([
                ["📝 Список", "🆕 Новий"],
                ["↩️ Відновити", "🔄 Продовжити"],
                ["⚙️ Налаштування", "❓ Допомога"],
                ["🔙 Назад"]
            ], resize_keyboard=True)
        return self._commands_keyboard
    
    async def _send_isolated_message(self, context, chat_id: int, text: str, keyboard=None):
        """Відправка ізольованого повідомлення без reply зв'язку."""
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=keyboard,
                disable_notification=True,
                allow_sending_without_reply=True
            )
        except Exception as e:
            # Fallback без markdown
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=keyboard,
                    disable_notification=True
                )
            except Exception as e2:
                logger.error(f"Помилка відправки повідомлення: {e2}")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обробник команди /start."""
        if not update.effective_chat or not update.effective_user:
            return
        
        try:
            if update.message:
                await update.message.delete()
                await asyncio.sleep(0.02)
        except:
            pass
        
        text = "🎯 Todo Bot v3.0 готовий до роботи!\n\nВикористовуйте меню для керування завданнями."
        await self._send_isolated_message(context, update.effective_chat.id, text, self.get_main_keyboard())
    
    async def list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обробник команди /list."""
        if not update.effective_chat:
            return
        
        try:
            if update.message:
                await update.message.delete()
                await asyncio.sleep(0.02)
        except:
            pass
        
        chat_id = update.effective_chat.id
        todo_list = self.manager.get_formatted_list(chat_id)
        await self._send_isolated_message(context, chat_id, todo_list, self.get_main_keyboard())
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обробник текстових повідомлень."""
        if not update.effective_chat or not update.message or not update.message.text:
            return
        
        chat_id = update.effective_chat.id
        text = update.message.text.strip()
        
        try:
            if update.message:
                await update.message.delete()
                await asyncio.sleep(0.02)
        except:
            pass
        
        # Обробка команд меню
        if text == "📋 Меню":
            await self._send_isolated_message(context, chat_id, "Виберіть дію:", self.get_commands_keyboard())
            return
        elif text == "🔙 Назад":
            await self._send_isolated_message(context, chat_id, "Головне меню:", self.get_main_keyboard())
            return
        elif text in ["📝 Список", "Список"]:
            todo_list = self.manager.get_formatted_list(chat_id)
            await self._send_isolated_message(context, chat_id, todo_list, self.get_main_keyboard())
            return
        elif text in ["🆕 Новий", "новий список"]:
            count = self.manager.clear_todos(chat_id)
            response = f"Список очищено ({count} завдань збережено в резерв)" if count > 0 else "Створено новий список"
            await self._send_isolated_message(context, chat_id, response, self.get_main_keyboard())
            return
        elif text in ["↩️ Відновити", "відновити"]:
            count = self.manager.restore_backup(chat_id)
            response = f"Відновлено {count} завдань" if count > 0 else "Немає даних для відновлення"
            await self._send_isolated_message(context, chat_id, response, self.get_main_keyboard())
            return
        elif text in ["🔄 Продовжити", "продовжити"]:
            count = self.manager.continue_list(chat_id)
            if count > 0:
                todo_list = self.manager.get_formatted_list(chat_id)
                response = f"Видалено {count} виконаних завдань\n\n{todo_list}"
            else:
                response = "Немає виконаних завдань для видалення"
            await self._send_isolated_message(context, chat_id, response, self.get_main_keyboard())
            return
        
        # Обробка команд з номерами
        await self._handle_number_commands(update, context, chat_id, text)
    
    async def _handle_number_commands(self, update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str):
        """Обробка команд з номерами завдань."""
        
        # Видалення завдання (команда "-число")
        if text.startswith("-") and text[1:].isdigit():
            num = int(text[1:])
            if self.manager.remove_todo(chat_id, num):
                todo_list = self.manager.get_formatted_list(chat_id)
                await self._send_isolated_message(context, chat_id, todo_list, self.get_main_keyboard())
            return
        
        # Перемикання стану завдання (команда "число")
        if text.isdigit():
            num = int(text)
            if self.manager.toggle_todo(chat_id, num):
                todo_list = self.manager.get_formatted_list(chat_id)
                await self._send_isolated_message(context, chat_id, todo_list, self.get_main_keyboard())
            return
        
        # Переміщення в секції (команда "числог", "числов", "числоз")
        if len(text) > 1 and text[:-1].isdigit():
            num = int(text[:-1])
            suffix = text[-1]
            target_section = None
            if suffix == "г":
                target_section = "гараж"
            elif suffix == "в":
                target_section = "волинка" 
            elif suffix == "з":
                target_section = "закупівля"
            
            if target_section and self.manager.move_todo_to_section(chat_id, num, target_section):
                todo_list = self.manager.get_formatted_list(chat_id)
                await self._send_isolated_message(context, chat_id, todo_list, self.get_main_keyboard())
            return
        
        # Об'єднання завдань (команда "число+число")
        if "+" in text:
            parts = text.split("+")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                first_num, second_num = int(parts[0]), int(parts[1])
                if self.manager.merge_todos(chat_id, first_num, second_num):
                    todo_list = self.manager.get_formatted_list(chat_id)
                    await self._send_isolated_message(context, chat_id, todo_list, self.get_main_keyboard())
                return
        
        # Обробка багаторядкових повідомлень
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if len(lines) > 1:
            for line in lines:
                if line:
                    self.manager.add_todo(chat_id, line)
        else:
            # Додавання нового завдання
            self.manager.add_todo(chat_id, text)
        
        todo_list = self.manager.get_formatted_list(chat_id)
        await self._send_isolated_message(context, chat_id, todo_list, self.get_main_keyboard())

def main():
    """Основна функція запуску бота."""
    try:
        token = os.getenv('TELEGRAM_BOT_TOKEN_PRODUCTION')
        if not token:
            logger.error("TELEGRAM_BOT_TOKEN_PRODUCTION не встановлено")
            sys.exit(1)
        
        logger.info("Запуск Todo бота GitHub Production v3.0...")
        
        bot = CleanTodoBot()
        application = Application.builder().token(token).build()
        
        # Реєстрація обробників
        application.add_handler(CommandHandler("start", bot.start_command))
        application.add_handler(CommandHandler("list", bot.list_command))
        application.add_handler(CommandHandler("help", bot.start_command))
        application.add_handler(CommandHandler("menu", bot.start_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
        
        logger.info("GitHub Production Bot v3.0 успішно запущено")
        
        # Запуск у GitHub Actions - polling для стабільності
        application.run_polling(
            poll_interval=2.0,
            timeout=10,
            drop_pending_updates=True
        )
        
    except Exception as e:
        logger.error(f"Критична помилка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()