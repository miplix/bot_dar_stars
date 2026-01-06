"""
Тестирование комплексного расчета всех даров (Ода, Туна, Триа, Чиа)
"""
from calculations import GiftsCalculator

def test_oda():
    """Тест расчета Ода (дата рождения)"""
    print("=" * 50)
    print("ТЕСТ: ОДА (Основные данные)")
    print("=" * 50)
    
    calculator = GiftsCalculator()
    birth_date = "15.05.1990"
    
    result = calculator.calculate_oda(birth_date)
    
    print(f"Дата рождения: {birth_date}")
    print(f"Код дара: {result['gift_code']}")
    print(f"Ма: {result['ma']}")
    print(f"Жи: {result['ji']}")
    print(f"Кун: {result['kun']}")
    print(f"\nДетали расчета:")
    print(f"  {result['calculation_details']['ma']}")
    print(f"  {result['calculation_details']['ji']}")
    print(f"  {result['calculation_details']['kun']}")
    print()

def test_tuna():
    """Тест расчета Туна (время рождения)"""
    print("=" * 50)
    print("ТЕСТ: ТУНА (Второстепенные данные)")
    print("=" * 50)
    
    calculator = GiftsCalculator()
    birth_time = "14:30"
    kun_oda = 3  # Из примера Ода
    
    result = calculator.calculate_tuna(birth_time, kun_oda)
    
    print(f"Время рождения: {birth_time}")
    print(f"Кун от Ода: {kun_oda}")
    print(f"Код дара: {result['gift_code']}")
    print(f"Ма: {result['ma']}")
    print(f"Жи: {result['ji']}")
    print(f"Кун: {result['kun']}")
    print(f"\nДетали расчета:")
    print(f"  {result['calculation_details']['ma']}")
    print(f"  {result['calculation_details']['ji']}")
    print(f"  {result['calculation_details']['kun']}")
    print()

def test_tria():
    """Тест расчета Триа (координаты)"""
    print("=" * 50)
    print("ТЕСТ: ТРИА (Третьестепенные данные)")
    print("=" * 50)
    
    calculator = GiftsCalculator()
    latitude = 49.9904411
    longitude = 36.2439857
    
    result = calculator.calculate_tria(latitude, longitude)
    
    print(f"Координаты: {latitude}, {longitude}")
    print(f"Широта (целая): {int(latitude)}°")
    print(f"Долгота (целая): {int(longitude)}°")
    print(f"Код дара: {result['gift_code']}")
    print(f"Ма: {result['ma']}")
    print(f"Жи: {result['ji']}")
    print(f"Кун: {result['kun']}")
    print(f"\nДетали расчета:")
    print(f"  {result['calculation_details']['ma']}")
    print(f"  {result['calculation_details']['ji']}")
    print(f"  {result['calculation_details']['kun']}")
    print()

def test_chia():
    """Тест расчета Чиа (имя и фамилия)"""
    print("=" * 50)
    print("ТЕСТ: ЧИА (Четверостепенные данные)")
    print("=" * 50)
    
    calculator = GiftsCalculator()
    first_name = "Александр"
    last_name = "Иванов"
    
    result = calculator.calculate_chia(first_name, last_name)
    
    print(f"Имя: {first_name}")
    print(f"Фамилия: {last_name}")
    print(f"Код дара: {result['gift_code']}")
    print(f"Ма: {result['ma']}")
    print(f"Жи: {result['ji']}")
    print(f"Кун: {result['kun']}")
    print(f"\nДетали расчета:")
    print(f"  {result['calculation_details']['ma']}")
    print(f"  {result['calculation_details']['ji']}")
    print(f"  {result['calculation_details']['kun']}")
    print()

def test_complete_profile():
    """Тест комплексного расчета всех даров"""
    print("=" * 50)
    print("ТЕСТ: КОМПЛЕКСНЫЙ РАСЧЕТ ВСЕХ ДАРОВ")
    print("=" * 50)
    
    calculator = GiftsCalculator()
    
    # Входные данные
    birth_date = "15.05.1990"
    birth_time = "14:30"
    latitude = 49.9904411
    longitude = 36.2439857
    first_name = "Александр"
    last_name = "Иванов"
    
    result = calculator.calculate_complete_profile(
        birth_date=birth_date,
        birth_time=birth_time,
        latitude=latitude,
        longitude=longitude,
        first_name=first_name,
        last_name=last_name
    )
    
    if result['status'] == 'error':
        print(f"❌ Ошибка: {result['error']}")
        return
    
    print(f"\n👤 Имя: {result['name']['first']} {result['name']['last']}")
    print(f"📅 Дата: {result['birth_date']}")
    print(f"🕐 Время: {result['birth_time']}")
    print(f"🌍 Координаты: {result['location']['latitude']}, {result['location']['longitude']}")
    print()
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🎁 ОДА (Основа личности)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    oda = result['oda']
    print(f"Код: {oda['gift_code']}")
    print(f"Ма: {oda['ma']}, Жи: {oda['ji']}, Кун: {oda['kun']}")
    print()
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🌙 ТУНА (Временной аспект)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    tuna = result['tuna']
    print(f"Код: {tuna['gift_code']}")
    print(f"Ма: {tuna['ma']}, Жи: {tuna['ji']}, Кун: {tuna['kun']}")
    print()
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🌍 ТРИА (Энергия места)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    tria = result['tria']
    print(f"Код: {tria['gift_code']}")
    print(f"Ма: {tria['ma']}, Жи: {tria['ji']}, Кун: {tria['kun']}")
    print()
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("💫 ЧИА (Имя и судьба)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    chia = result['chia']
    print(f"Код: {chia['gift_code']}")
    print(f"Ма: {chia['ma']}, Жи: {chia['ji']}, Кун: {chia['kun']}")
    print()
    
    print("✅ Комплексный расчет успешно выполнен!")
    print()

def test_kabbalah():
    """Тест кабалистической таблицы"""
    print("=" * 50)
    print("ТЕСТ: КАБАЛИСТИЧЕСКАЯ ТАБЛИЦА")
    print("=" * 50)
    
    calculator = GiftsCalculator()
    
    test_names = [
        ("Александр", "Иванов"),
        ("Мария", "Петрова"),
        ("Иван", "Сидоров"),
        ("Елена", "Смирнова")
    ]
    
    for first, last in test_names:
        result = calculator.calculate_chia(first, last)
        print(f"{first} {last}: {result['gift_code']} (Ма={result['ma']}, Жи={result['ji']}, Кун={result['kun']})")
    
    print()

if __name__ == "__main__":
    print("\n🔮 ТЕСТИРОВАНИЕ КОМПЛЕКСНОГО РАСЧЕТА ДАРОВ\n")
    
    # Запускаем все тесты
    test_oda()
    test_tuna()
    test_tria()
    test_chia()
    test_kabbalah()
    test_complete_profile()
    
    print("=" * 50)
    print("✅ ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ")
    print("=" * 50)

