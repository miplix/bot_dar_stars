"""
Модуль для расчета даров по дате рождения
Система Ма-Жи-Кун (Ма - день+месяц, Жи - год, Кун - сумма)
"""
from datetime import datetime
from typing import Dict, Tuple

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

