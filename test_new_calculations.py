"""
Тестовый файл для проверки расчетов по системе Ма-Жи-Кун
"""
from calculations import GiftsCalculator
from gifts_knowledge import get_gift_info, get_gifts_by_kun, format_gift_description

def test_calculation(birth_date: str):
    """Тестирование расчета для конкретной даты"""
    calculator = GiftsCalculator()
    
    print("=" * 60)
    print(f"Дата рождения: {birth_date}")
    print("=" * 60)
    
    result = calculator.calculate_gift(birth_date)
    
    if result['status'] == 'error':
        print(f"❌ Ошибка: {result['error']}")
        return
    
    print(f"\n📊 Результаты расчета:")
    print(f"Ма:  {result['ma']}")
    print(f"Жи:  {result['ji']}")
    print(f"Кун: {result['kun']}")
    print(f"\n🎁 Код дара: {result['gift_code']}")
    
    print(f"\n🔢 Детальный расчет:")
    print(f"{result['calculation_details']['ma']}")
    print(f"{result['calculation_details']['ji']}")
    print(f"{result['calculation_details']['kun']}")
    
    # Проверяем, есть ли дар в базе
    gift_info = get_gift_info(result['gift_code'])
    
    print("\n" + "=" * 60)
    if gift_info:
        print("✅ Дар найден в базе знаний!")
        print("=" * 60)
        print(format_gift_description(result['gift_code']))
    else:
        print("⚠️ Точного дара не найдено в базе")
        print("=" * 60)
        kun_gifts = get_gifts_by_kun(result['kun'])
        if kun_gifts:
            print(f"\n🔍 Найдено {len(kun_gifts)} даров с Кун = {result['kun']}:")
            for i, gift in enumerate(kun_gifts, 1):
                print(f"\n{i}. {gift.get('name', 'Без названия')} ({gift.get('code', '')})")
                desc = gift.get('description', '')
                if len(desc) > 100:
                    desc = desc[:100] + "..."
                print(f"   {desc}")
        else:
            print(f"❌ Даров с Кун = {result['kun']} не найдено")
    
    print("\n")


def main():
    """Основная функция тестирования"""
    print("\n🧪 ТЕСТИРОВАНИЕ СИСТЕМЫ МА-ЖИ-КУН\n")
    
    # Тестовые даты
    test_dates = [
        "15.05.1990",  # Пример из описания: Ма=2, Жи=1, Кун=3 → 2-1-3
        "01.01.2000",  # Простой случай
        "25.12.1985",  # Другая дата
        "10.06.1995",  # Еще один пример
        "31.08.1988",  # Дата с большими числами
    ]
    
    for date in test_dates:
        test_calculation(date)
    
    print("=" * 60)
    print("✅ Тестирование завершено!")
    print("=" * 60)
    
    # Статистика базы знаний
    from gifts_knowledge import get_all_gifts
    all_gifts = get_all_gifts()
    
    print(f"\n📚 В базе знаний {len(all_gifts)} даров:")
    
    # Группируем по Кун
    kun_stats = {}
    for code in all_gifts.keys():
        parts = code.split('-')
        if len(parts) == 3:
            kun = int(parts[2])
            kun_stats[kun] = kun_stats.get(kun, 0) + 1
    
    print("\n📊 Распределение по Кун:")
    for kun in sorted(kun_stats.keys()):
        print(f"Кун {kun}: {kun_stats[kun]} даров")


if __name__ == "__main__":
    main()


