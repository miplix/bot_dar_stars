"""
Модуль для работы с сантрами
Создание и анализ сантр на основе команд и даров
"""
import random
from src.commands import get_commands_by_position, get_command_info
from src.gifts_knowledge import get_all_gifts, get_gift_info


def normalize_gift_name(gift_name: str) -> str:
    """
    Нормализация имени дара для поиска
    Убирает "дар", "старший дар", пробелы, дефисы и приводит к нижнему регистру
    
    Args:
        gift_name: Имя дара (например, "дар Ма-На", "старший дар - Ми-Ра" или "мана")
    
    Returns:
        Нормализованное имя (например, "мана" или "мира")
    """
    # Убираем "старший дар", "дар", пробелы, дефисы, приводим к нижнему регистру
    normalized = gift_name.lower()
    normalized = normalized.replace("старший дар", "")
    normalized = normalized.replace("старшийдар", "")
    normalized = normalized.replace("дар", "")
    normalized = normalized.replace(" ", "")
    normalized = normalized.replace("-", "")
    normalized = normalized.strip()
    return normalized


def find_gift_by_name(gift_name: str) -> dict:
    """
    Поиск дара по имени (с учетом нормализации)
    
    Args:
        gift_name: Имя дара для поиска
    
    Returns:
        Словарь с информацией о даре или пустой словарь
    """
    normalized_search = normalize_gift_name(gift_name)
    all_gifts = get_all_gifts()
    
    # Ищем по нормализованному имени в названиях даров
    for gift_code, gift_data in all_gifts.items():
        gift_name_in_db = gift_data.get("name", "")
        normalized_db_name = normalize_gift_name(gift_name_in_db)
        
        if normalized_search == normalized_db_name:
            result = gift_data.copy()
            result["code"] = gift_code
            return result
    
    return {}


def create_mantra_random(num_gifts: int = 1, include_end: bool = False) -> dict:
    """
    Создание случайной сантры
    
    Args:
        num_gifts: Количество даров в сантре (1 или 2)
        include_end: Включать ли команду "конец" в сантру
    
    Returns:
        Словарь с информацией о сантре:
        {
            "mantra": "Ши Ду Ма-На",
            "structure": ["начало", "между", "дар", ...],
            "elements": [
                {"type": "команда", "name": "Ши", "description": "..."},
                {"type": "команда", "name": "Ду", "description": "..."},
                {"type": "дар", "name": "дар Ма-На", "description": "..."}
            ]
        }
    """
    if num_gifts not in [1, 2]:
        num_gifts = 1
    
    # Получаем команды по позициям
    start_commands = get_commands_by_position("начало")
    between_commands = get_commands_by_position("между")
    end_commands = get_commands_by_position("конец")
    
    # Получаем все дары
    all_gifts = get_all_gifts()
    gift_list = list(all_gifts.items())
    
    if not start_commands or not between_commands or not gift_list:
        return {"error": "Недостаточно данных для создания сантры"}
    
    # Выбираем случайные элементы
    start_cmd = random.choice(start_commands)
    mantra_parts = [start_cmd["имя"]]
    elements = [{
        "type": "команда",
        "name": start_cmd["имя"],
        "description": start_cmd["описание"],
        "position": "начало"
    }]
    
    # Добавляем дары с командами "между"
    for i in range(num_gifts):
        # Команда "между" перед даром
        between_cmd = random.choice(between_commands)
        mantra_parts.append(between_cmd["имя"])
        elements.append({
            "type": "команда",
            "name": between_cmd["имя"],
            "description": between_cmd["описание"],
            "position": "между"
        })
        
        # Дар
        gift_code, gift_data = random.choice(gift_list)
        gift_name = gift_data.get("name", "")
        # Убираем префиксы "дар " и "старший дар - "
        clean_name = gift_name
        if "старший дар - " in clean_name:
            clean_name = clean_name.replace("старший дар - ", "")
        elif "дар " in clean_name:
            clean_name = clean_name.replace("дар ", "")
        mantra_parts.append(clean_name)
        elements.append({
            "type": "дар",
            "name": gift_name,
            "code": gift_code,
            "description": gift_data.get("description", ""),
            "ma_ji_kun": gift_data.get("ma_ji_kun", "")
        })
    
    # Если нужно добавить "конец"
    if include_end and end_commands:
        # Команда "между" перед "конец"
        between_cmd = random.choice(between_commands)
        mantra_parts.append(between_cmd["имя"])
        elements.append({
            "type": "команда",
            "name": between_cmd["имя"],
            "description": between_cmd["описание"],
            "position": "между"
        })
        
        # Команда "конец"
        end_cmd = random.choice(end_commands)
        mantra_parts.append(end_cmd["имя"])
        elements.append({
            "type": "команда",
            "name": end_cmd["имя"],
            "description": end_cmd["описание"],
            "position": "конец"
        })
    
    mantra_text = " ".join(mantra_parts)
    
    return {
        "mantra": mantra_text,
        "structure": [elem["type"] for elem in elements],
        "elements": elements
    }


def create_mantra_by_request(user_question: str, num_gifts: int = 1, include_end: bool = False) -> dict:
    """
    Создание сантры на основе запроса пользователя
    (В будущем можно использовать ИИ для выбора подходящих элементов)
    
    Args:
        user_question: Вопрос/запрос пользователя
        num_gifts: Количество даров в сантре (1 или 2)
        include_end: Включать ли команду "конец"
    
    Returns:
        Словарь с информацией о сантре (пока использует случайный выбор)
    """
    # Пока используем случайный выбор, но можно добавить логику на основе вопроса
    return create_mantra_random(num_gifts, include_end)


def parse_mantra(mantra_text: str) -> dict:
    """
    Парсинг сантры из текста пользователя
    
    Args:
        mantra_text: Текст сантры (например, "Ши ду мана")
    
    Returns:
        Словарь с распарсенными элементами:
        {
            "mantra": "Ши Ду Ма-На",
            "elements": [...],
            "errors": []  # Список ошибок, если элементы не найдены
        }
    """
    # Разбиваем на слова
    parts = mantra_text.strip().split()
    
    elements = []
    errors = []
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # Пытаемся найти команду
        cmd_info = get_command_info(part)
        if cmd_info:
            elements.append({
                "type": "команда",
                "name": cmd_info["имя"],
                "description": cmd_info["описание"],
                "position": cmd_info["позиция"][0] if cmd_info["позиция"] else "неизвестно"
            })
            continue
        
        # Пытаемся найти дар
        gift_info = find_gift_by_name(part)
        if gift_info:
            elements.append({
                "type": "дар",
                "name": gift_info.get("name", ""),
                "code": gift_info.get("code", ""),
                "description": gift_info.get("description", ""),
                "ma_ji_kun": gift_info.get("ma_ji_kun", "")
            })
            continue
        
        # Если не найдено ни команды, ни дара
        errors.append(f"Элемент '{part}' не найден в базе данных")
        elements.append({
            "type": "неизвестно",
            "name": part,
            "description": "Не найден в базе данных"
        })
    
    return {
        "mantra": mantra_text,
        "elements": elements,
        "errors": errors
    }

