"""
Модуль для расчета даров по дате рождения
Система Ма-Жи-Кун (Ма - день+месяц, Жи - год, Кун - сумма)
Поддерживает расчет Ода, Туна, Триа и Чиа
"""
from datetime import datetime
from typing import Dict, Tuple

# Кабалистическая таблица для расчета Чиа
KABBALAH_TABLE = {
    'а': 1, 'и': 1, 'с': 1, 'ъ': 1,
    'б': 2, 'й': 2, 'т': 2, 'ы': 2,
    'в': 3, 'к': 3, 'у': 3, 'ь': 3,
    'г': 4, 'л': 4, 'ф': 4, 'э': 4,
    'д': 5, 'м': 5, 'х': 5, 'ю': 5,
    'е': 6, 'н': 6, 'ц': 6, 'я': 6,
    'ё': 7, 'о': 7, 'ч': 7,
    'ж': 8, 'п': 8, 'ш': 8,
    'з': 9, 'р': 9, 'щ': 9
}

class GiftsCalculator:
    """Класс для расчета даров по дате рождения в системе Ма-Жи-Кун"""
    
    @staticmethod
    def parse_date(date_str: str) -> Tuple[int, int, int]:
        """Парсинг даты в формате DD.MM.YYYY"""
        try:
            date_obj = datetime.strptime(date_str, "%d.%m.%Y")
            return date_obj.day, date_obj.month, date_obj.year
        except ValueError:
            raise ValueError("Неверный формат даты. Используйте DD.MM.YYYY")
    
    @staticmethod
    def parse_time(time_str: str) -> Tuple[int, int]:
        """Парсинг времени в формате ЧЧ:ММ"""
        try:
            time_obj = datetime.strptime(time_str, "%H:%M")
            return time_obj.hour, time_obj.minute
        except ValueError:
            raise ValueError("Неверный формат времени. Используйте ЧЧ:ММ")
    
    @staticmethod
    def sum_digits(number: int) -> int:
        """Сумма цифр числа"""
        return sum(int(digit) for digit in str(number))
    
    @staticmethod
    def reduce_to_single_digit(number: int) -> int:
        """
        Кверсуммирование - приведение числа к однозначному (1-9)
        Если число больше 9, суммируем его цифры до получения однозначного
        """
        while number > 9:
            number = sum(int(digit) for digit in str(number))
        return number if number > 0 else 1
    
    def calculate_ma(self, day: int, month: int) -> int:
        """
        Расчет Ма (первая цифра дара)
        Ма = сумма всех цифр дня и месяца (д+д+м+м)
        С кверсуммированием до однозначного числа
        """
        # Суммируем все цифры дня и месяца
        ma = self.sum_digits(day) + self.sum_digits(month)
        # Приводим к однозначному числу
        return self.reduce_to_single_digit(ma)
    
    def calculate_ji(self, year: int) -> int:
        """
        Расчет Жи (вторая цифра дара)
        Жи = сумма всех цифр года (г+г+г+г)
        С кверсуммированием до однозначного числа
        """
        # Суммируем все цифры года
        ji = self.sum_digits(year)
        # Приводим к однозначному числу
        return self.reduce_to_single_digit(ji)
    
    def calculate_kun(self, ma: int, ji: int) -> int:
        """
        Расчет Кун (третья цифра дара)
        Кун = Ма + Жи
        С кверсуммированием до однозначного числа
        """
        kun = ma + ji
        return self.reduce_to_single_digit(kun)
    
    def calculate_gift(self, birth_date: str) -> Dict:
        """
        Расчет дара по дате рождения
        Возвращает код дара в формате "Ма-Жи-Кун"
        
        Пример:
        Дата: 15.05.1990
        Ма = 1+5+0+5 = 11 → 1+1 = 2
        Жи = 1+9+9+0 = 19 → 1+9 = 10 → 1+0 = 1
        Кун = 2+1 = 3
        Код дара: 2-1-3
        """
        try:
            day, month, year = self.parse_date(birth_date)
            
            # Расчет Ма
            ma = self.calculate_ma(day, month)
            ma_calculation = f"Ма = цифры({day:02d}) + цифры({month:02d}) = {self.sum_digits(day)} + {self.sum_digits(month)} = {self.sum_digits(day) + self.sum_digits(month)}"
            if self.sum_digits(day) + self.sum_digits(month) > 9:
                ma_calculation += f" → {ma}"
            else:
                ma_calculation += f" = {ma}"
            
            # Расчет Жи
            ji = self.calculate_ji(year)
            year_digits_sum = self.sum_digits(year)
            ji_calculation = f"Жи = цифры({year}) = {year_digits_sum}"
            if year_digits_sum > 9:
                ji_calculation += f" → {ji}"
            else:
                ji_calculation += f" = {ji}"
            
            # Расчет Кун
            kun = self.calculate_kun(ma, ji)
            kun_calculation = f"Кун = Ма + Жи = {ma} + {ji} = {ma + ji}"
            if ma + ji > 9:
                kun_calculation += f" → {kun}"
            else:
                kun_calculation += f" = {kun}"
            
            # Формируем код дара
            gift_code = f"{ma}-{ji}-{kun}"
            
            return {
                "birth_date": birth_date,
                "gift_code": gift_code,
                "ma": ma,
                "ji": ji,
                "kun": kun,
                "calculation_details": {
                    "ma": ma_calculation,
                    "ji": ji_calculation,
                    "kun": kun_calculation
                },
                "status": "success"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def calculate_all_gifts(self, birth_date: str) -> Dict:
        """
        Основная функция расчета дара
        Для совместимости со старым API
        """
        return self.calculate_gift(birth_date)
    
    # ============ НОВЫЕ ФУНКЦИИ ДЛЯ КОМПЛЕКСНОГО РАСЧЕТА ============
    
    def calculate_oda(self, birth_date: str) -> Dict:
        """
        Расчет ОДА (основные данные)
        По дате рождения: ДД.ММ.ГГГГ
        Ма = д+д+м+м (≤9)
        Жи = г+г+г+г (≤9)
        Кун = ма+жи (≤9)
        """
        return self.calculate_gift(birth_date)
    
    def calculate_tuna(self, birth_time: str, kun_oda: int) -> Dict:
        """
        Расчет ТУНА (второстепенные данные)
        По времени рождения: ЧЧ:ММ
        Ма = кун от Ода
        Жи = ч+ч+м+м (≤9)
        Кун = ма+жи (≤9)
        """
        try:
            hour, minute = self.parse_time(birth_time)
            
            # Ма = Кун из Ода
            ma = kun_oda
            
            # Жи = сумма цифр часа и минут
            ji_sum = self.sum_digits(hour) + self.sum_digits(minute)
            ji = self.reduce_to_single_digit(ji_sum)
            
            # Кун
            kun = self.calculate_kun(ma, ji)
            
            # Формируем детали расчета
            ji_calculation = f"Жи = цифры({hour:02d}) + цифры({minute:02d}) = {self.sum_digits(hour)} + {self.sum_digits(minute)} = {ji_sum}"
            if ji_sum > 9:
                ji_calculation += f" → {ji}"
            else:
                ji_calculation += f" = {ji}"
            
            gift_code = f"{ma}-{ji}-{kun}"
            
            return {
                "birth_time": birth_time,
                "gift_code": gift_code,
                "ma": ma,
                "ji": ji,
                "kun": kun,
                "calculation_details": {
                    "ma": f"Ма = Кун(Ода) = {ma}",
                    "ji": ji_calculation,
                    "kun": f"Кун = Ма + Жи = {ma} + {ji} = {kun}"
                },
                "status": "success"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def calculate_tria(self, latitude: float, longitude: float) -> Dict:
        """
        Расчет ТРИА
        По координатам рождения (только целые числа градусов)
        Ма = сумма цифр широты (≤9)
        Жи = сумма цифр долготы (≤9)
        Кун = ма+жи (≤9)
        """
        try:
            # Берем только целые части координат
            lat_int = abs(int(latitude))
            lon_int = abs(int(longitude))
            
            # Ма = сумма цифр широты
            ma_sum = self.sum_digits(lat_int)
            ma = self.reduce_to_single_digit(ma_sum)
            
            # Жи = сумма цифр долготы
            ji_sum = self.sum_digits(lon_int)
            ji = self.reduce_to_single_digit(ji_sum)
            
            # Кун
            kun = self.calculate_kun(ma, ji)
            
            # Формируем детали расчета
            ma_calculation = f"Ма = цифры({lat_int}°) = {ma_sum}"
            if ma_sum > 9:
                ma_calculation += f" → {ma}"
            else:
                ma_calculation += f" = {ma}"
                
            ji_calculation = f"Жи = цифры({lon_int}°) = {ji_sum}"
            if ji_sum > 9:
                ji_calculation += f" → {ji}"
            else:
                ji_calculation += f" = {ji}"
            
            gift_code = f"{ma}-{ji}-{kun}"
            
            return {
                "latitude": latitude,
                "longitude": longitude,
                "gift_code": gift_code,
                "ma": ma,
                "ji": ji,
                "kun": kun,
                "calculation_details": {
                    "ma": ma_calculation,
                    "ji": ji_calculation,
                    "kun": f"Кун = Ма + Жи = {ma} + {ji} = {kun}"
                },
                "status": "success"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def calculate_chia(self, first_name: str, last_name: str) -> Dict:
        """
        Расчет ЧИА
        По имени и фамилии (кабалистика)
        Ма = сумма цифр имени (≤9)
        Жи = сумма цифр фамилии (≤9)
        Кун = ма+жи (≤9)
        """
        try:
            # Нормализуем имя и фамилию (убираем пробелы, переводим в нижний регистр)
            first_name = first_name.strip().lower()
            last_name = last_name.strip().lower()
            
            # Рассчитываем Ма (имя)
            ma_sum = 0
            first_name_calc = []
            for char in first_name:
                if char in KABBALAH_TABLE:
                    value = KABBALAH_TABLE[char]
                    ma_sum += value
                    first_name_calc.append(f"{char}={value}")
            
            ma = self.reduce_to_single_digit(ma_sum) if ma_sum > 0 else 1
            
            # Рассчитываем Жи (фамилия)
            ji_sum = 0
            last_name_calc = []
            for char in last_name:
                if char in KABBALAH_TABLE:
                    value = KABBALAH_TABLE[char]
                    ji_sum += value
                    last_name_calc.append(f"{char}={value}")
            
            ji = self.reduce_to_single_digit(ji_sum) if ji_sum > 0 else 1
            
            # Кун
            kun = self.calculate_kun(ma, ji)
            
            # Формируем детали расчета
            ma_calculation = f"Ма = {first_name.upper()} = {'+'.join([str(KABBALAH_TABLE[c]) for c in first_name if c in KABBALAH_TABLE])} = {ma_sum}"
            if ma_sum > 9:
                ma_calculation += f" → {ma}"
            else:
                ma_calculation += f" = {ma}"
            
            ji_calculation = f"Жи = {last_name.upper()} = {'+'.join([str(KABBALAH_TABLE[c]) for c in last_name if c in KABBALAH_TABLE])} = {ji_sum}"
            if ji_sum > 9:
                ji_calculation += f" → {ji}"
            else:
                ji_calculation += f" = {ji}"
            
            gift_code = f"{ma}-{ji}-{kun}"
            
            return {
                "first_name": first_name.capitalize(),
                "last_name": last_name.capitalize(),
                "gift_code": gift_code,
                "ma": ma,
                "ji": ji,
                "kun": kun,
                "calculation_details": {
                    "ma": ma_calculation,
                    "ji": ji_calculation,
                    "kun": f"Кун = Ма + Жи = {ma} + {ji} = {kun}"
                },
                "status": "success"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def calculate_complete_profile(self, birth_date: str, birth_time: str, 
                                   latitude: float, longitude: float,
                                   first_name: str, last_name: str) -> Dict:
        """
        Комплексный расчет всех четырех компонентов профиля
        
        Процесс:
        1. Запрашиваются данные по очереди у пользователя (в src/bot.py)
        2. После сбора всех данных - все считается
        3. Данные пропускаются через базу данных для получения информации о дарах
        4. Затем анализируются через ИИ с учетом данных из базы
        
        Уровни влияния:
        - Ода (основные данные) - главное влияние (100%)
        - Туна (второстепенные данные) - меньшее влияние (70%)
        - Триа (третьестепенные данные) - еще меньшее влияние (40%)
        - Чиа (четверостепенные данные) - самое малое влияние (20%)
        
        Args:
            birth_date: Дата рождения (ДД.ММ.ГГГГ)
            birth_time: Время рождения (ЧЧ:ММ)
            latitude: Широта места рождения
            longitude: Долгота места рождения
            first_name: Имя
            last_name: Фамилия
        
        Returns:
            Словарь со всеми расчетами и информацией из базы данных
        """
        try:
            # Рассчитываем Ода (основные данные - главное влияние)
            oda = self.calculate_oda(birth_date)
            if oda['status'] == 'error':
                return oda
            
            # Рассчитываем Туна (второстепенные данные - меньшее влияние)
            # Ма = Кун из Ода
            tuna = self.calculate_tuna(birth_time, oda['kun'])
            if tuna['status'] == 'error':
                return tuna
            
            # Рассчитываем Триа (третьестепенные данные - еще меньшее влияние)
            tria = self.calculate_tria(latitude, longitude)
            if tria['status'] == 'error':
                return tria
            
            # Рассчитываем Чиа (четверостепенные данные - самое малое влияние)
            chia = self.calculate_chia(first_name, last_name)
            if chia['status'] == 'error':
                return chia
            
            # Пропускаем через базу данных - получаем информацию о дарах
            from src.gifts_knowledge import get_gift_info
            
            # Получаем информацию о каждом даре из базы
            oda_gift_info = get_gift_info(oda.get('gift_code', ''))
            tuna_gift_info = get_gift_info(tuna.get('gift_code', ''))
            tria_gift_info = get_gift_info(tria.get('gift_code', ''))
            chia_gift_info = get_gift_info(chia.get('gift_code', ''))
            
            # Формируем полный результат с данными из базы
            result = {
                "status": "success",
                "oda": {
                    **oda,
                    "gift_info": oda_gift_info,
                    "influence_level": 100  # Главное влияние
                },
                "tuna": {
                    **tuna,
                    "gift_info": tuna_gift_info,
                    "influence_level": 70  # Меньшее влияние
                },
                "tria": {
                    **tria,
                    "gift_info": tria_gift_info,
                    "influence_level": 40  # Еще меньшее влияние
                },
                "chia": {
                    **chia,
                    "gift_info": chia_gift_info,
                    "influence_level": 20  # Самое малое влияние
                },
                "birth_date": birth_date,
                "birth_time": birth_time,
                "location": {"latitude": latitude, "longitude": longitude},
                "name": {"first": first_name.capitalize(), "last": last_name.capitalize()}
            }
            
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    # ============ ДАР ДНЯ ============
    
    def calculate_day_gift(self, date_str: str = None) -> Dict:
        """
        Расчет дара дня по текущей дате
        Ма = д+д+м+м (≤9)
        Жи = г+г+г+г (≤9)
        Кун = ма+жи (≤9)
        
        Args:
            date_str: Дата в формате ДД.ММ.ГГГГ (если None, используется текущая дата)
        
        Returns:
            Словарь с результатами расчета
        """
        try:
            if date_str:
                day, month, year = self.parse_date(date_str)
            else:
                # Используем текущую дату
                now = datetime.now()
                day = now.day
                month = now.month
                year = now.year
                date_str = f"{day:02d}.{month:02d}.{year}"
            
            # Ма = д+д+м+м (сумма всех цифр дня и месяца)
            ma = self.calculate_ma(day, month)
            
            # Жи = г+г+г+г (сумма всех цифр года)
            ji = self.calculate_ji(year)
            
            # Кун = ма+жи
            kun = self.calculate_kun(ma, ji)
            
            # Формируем код дара
            gift_code = f"{ma}-{ji}-{kun}"
            
            # Формируем детали расчета
            ma_calculation = f"Ма = цифры({day:02d}) + цифры({month:02d}) = {self.sum_digits(day)} + {self.sum_digits(month)} = {self.sum_digits(day) + self.sum_digits(month)}"
            if self.sum_digits(day) + self.sum_digits(month) > 9:
                ma_calculation += f" → {ma}"
            else:
                ma_calculation += f" = {ma}"
            
            ji_calculation = f"Жи = цифры({year}) = {self.sum_digits(year)}"
            if self.sum_digits(year) > 9:
                ji_calculation += f" → {ji}"
            else:
                ji_calculation += f" = {ji}"
            
            kun_calculation = f"Кун = Ма + Жи = {ma} + {ji} = {ma + ji}"
            if ma + ji > 9:
                kun_calculation += f" → {kun}"
            else:
                kun_calculation += f" = {kun}"
            
            return {
                "date": date_str,
                "gift_code": gift_code,
                "ma": ma,
                "ji": ji,
                "kun": kun,
                "calculation_details": {
                    "ma": ma_calculation,
                    "ji": ji_calculation,
                    "kun": kun_calculation
                },
                "status": "success"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

