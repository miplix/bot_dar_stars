"""
Flask приложение для работы с Supabase
"""
import os
from flask import Flask, jsonify
from supabase import create_client, Client
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

app = Flask(__name__)

# Получаем настройки Supabase из переменных окружения
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://ouodquakgyyeiyihmoxg.supabase.co')
SUPABASE_API_KEY = os.getenv('SUPABASE_API_KEY', '') or os.getenv('SUPABASE_ANON_KEY', '') or os.getenv('SUPABASE_KEY', '')

# Создаем клиент Supabase
if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL не установлен в переменных окружения!")

if not SUPABASE_API_KEY:
    raise ValueError("SUPABASE_API_KEY, SUPABASE_ANON_KEY или SUPABASE_KEY не установлен в переменных окружения!")

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_API_KEY
)

@app.route('/')
def index():
    """Главная страница - список пользователей"""
    try:
        response = supabase.table('telegram_users').select("*").limit(10).execute()
        users = response.data

        html = '<h1>Пользователи бота</h1><ul>'
        if users:
            for user in users:
                username = user.get('username', 'Без username')
                first_name = user.get('first_name', 'Без имени')
                html += f'<li>{first_name} (@{username}) - ID: {user.get("user_id")}</li>'
        else:
            html += '<li>Пользователи не найдены</li>'
        html += '</ul>'
        
        html += '<p><a href="/api/users">JSON API</a></p>'
        return html
    except Exception as e:
        return f'<h1>Ошибка</h1><p>{str(e)}</p>', 500

@app.route('/api/users')
def api_users():
    """API endpoint для получения списка пользователей"""
    try:
        response = supabase.table('telegram_users').select("*").limit(50).execute()
        return jsonify({
            'success': True,
            'count': len(response.data),
            'data': response.data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health')
def health():
    """Проверка здоровья приложения"""
    return jsonify({
        'status': 'ok',
        'supabase_url': SUPABASE_URL,
        'supabase_configured': bool(SUPABASE_API_KEY)
    })

if __name__ == '__main__':
    print("Запуск Flask приложения")
    print(f"Supabase URL: {SUPABASE_URL}")
    print(f"Supabase API Key: {'установлен' if SUPABASE_API_KEY else 'не установлен'}")
    app.run(debug=True, host='0.0.0.0', port=5000)
