"""
Тестовый скрипт для проверки расчетов даров
Запустите этот файл для проверки корректности формул
"""
from calculations import GiftsCalculator

def test_calculations():
    """Тестирование расчетов даров"""
    calculator = GiftsCalculator()
    
    # Тестовые даты рождения
    test_dates = [
        "15.05.1990",
        "01.01.2000",
        "31.12.1985",
        "10.10.1995"
    ]
    
    print("🧪 Тестирование расчетов даров\n")
    print("=" * 60)
    
    for date in test_dates:
        print(f"\n📅 Дата рождения: {date}")
        print("-" * 60)
        
        try:
            results = calculator.calculate_all_gifts(date)
            
            if results['status'] == 'success':
                print(f"✅ Расчет успешен\n")
                
                # Ода
                oda = results['oda']
                print(f"🎁 Ода: {oda['value']}")
                print(f"   Расчет: {oda['calculation']}")
                print(f"   {oda['description']}\n")
                
                # Туна
                tuna = results['tuna']
                print(f"🌙 Туна: {tuna['value']}")
                print(f"   Расчет: {tuna['calculation']}")
                print(f"   {tuna['description']}\n")
                
                # Триа
                tria = results['tria']
                print(f"✨ Триа: {tria['value']}")
                print(f"   Расчет: {tria['calculation']}")
                print(f"   {tria['description']}\n")
                
                # Чиа
                chia = results['chia']
                print(f"💎 Чиа: {chia['value']}")
                print(f"   Расчет: {chia['calculation']}")
                print(f"   {chia['description']}\n")
            else:
                print(f"❌ Ошибка: {results['error']}")
        
        except Exception as e:
            print(f"❌ Исключение: {e}")
        
        print("=" * 60)

def test_individual_calculations():
    """Тестирование отдельных расчетов"""
    calculator = GiftsCalculator()
    test_date = "15.05.1990"
    
    print("\n🔬 Детальное тестирование для даты: 15.05.1990")
    print("=" * 60)
    
    # Проверка парсинга даты
    day, month, year = calculator.parse_date(test_date)
    print(f"\n📊 Парсинг даты:")
    print(f"   День: {day}")
    print(f"   Месяц: {month}")
    print(f"   Год: {year}")
    
    # Проверка приведения к 22
    print(f"\n🔢 Тест приведения к диапазону 1-22:")
    test_numbers = [25, 45, 99, 123, 1, 22]
    for num in test_numbers:
        result = calculator.reduce_to_22(num)
        print(f"   {num} → {result}")
    
    print("\n" + "=" * 60)

def test_edge_cases():
    """Тестирование граничных случаев"""
    calculator = GiftsCalculator()
    
    print("\n⚠️  Тестирование граничных случаев")
    print("=" * 60)
    
    edge_cases = [
        ("01.01.0001", "Минимальная дата"),
        ("31.12.9999", "Максимальная дата"),
        ("29.02.2000", "Високосный год"),
        ("invalid", "Неверный формат"),
        ("32.13.2020", "Несуществующая дата")
    ]
    
    for date, description in edge_cases:
        print(f"\n📝 Тест: {description}")
        print(f"   Дата: {date}")
        
        try:
            results = calculator.calculate_all_gifts(date)
            if results['status'] == 'success':
                print(f"   ✅ Результат: Ода={results['oda']['value']}")
            else:
                print(f"   ❌ Ошибка: {results['error']}")
        except Exception as e:
            print(f"   ❌ Исключение: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    print("\n" + "🎁" * 30)
    print("   ТЕСТИРОВАНИЕ СИСТЕМЫ РАСЧЕТА ДАРОВ")
    print("🎁" * 30 + "\n")
    
    # Запуск тестов
    test_calculations()
    test_individual_calculations()
    test_edge_cases()
    
    print("\n✅ Тестирование завершено!\n")

