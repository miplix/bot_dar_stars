'use client'

import { useEffect, useState } from 'react'
import { supabase, TelegramUser } from '@/lib/supabase'

export default function Home() {
  const [users, setUsers] = useState<TelegramUser[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadUsers()
  }, [])

  const loadUsers = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const { data, error: fetchError } = await supabase
        .from('telegram_users')
        .select('*')
        .limit(10)
        .order('created_at', { ascending: false })

      if (fetchError) {
        // Проверяем, является ли ошибка 404 (таблица не существует)
        // PGRST205 - таблица не найдена в schema cache
        // PGRST116 - таблица не существует
        if (
          fetchError.code === 'PGRST205' || 
          fetchError.code === 'PGRST116' || 
          fetchError.message?.includes('404') || 
          fetchError.message?.includes('relation') || 
          fetchError.message?.includes('does not exist') ||
          fetchError.message?.includes('Could not find the table')
        ) {
          throw new Error('TABLE_NOT_FOUND')
        }
        throw fetchError
      }
      
      setUsers(data || [])
    } catch (err) {
      if (err instanceof Error && err.message === 'TABLE_NOT_FOUND') {
        setError('TABLE_NOT_FOUND')
      } else {
        setError(err instanceof Error ? err.message : 'Неизвестная ошибка')
      }
      console.error('Ошибка загрузки пользователей:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen p-8 bg-gray-50">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-6 text-gray-900">
          Пользователи бота
        </h1>

        {loading && (
          <div className="text-center py-8 text-gray-600">
            Загрузка...
          </div>
        )}

        {error && (
          <div className={`border px-4 py-3 rounded mb-4 ${
            error === 'TABLE_NOT_FOUND' 
              ? 'bg-yellow-50 border-yellow-200 text-yellow-800' 
              : 'bg-red-50 border-red-200 text-red-700'
          }`}>
            {error === 'TABLE_NOT_FOUND' ? (
              <>
                <p className="font-semibold mb-2">⚠️ Таблицы базы данных не найдены</p>
                <p className="mb-3">Миграция базы данных еще не применена. Необходимо создать таблицы.</p>
                <div className="bg-white rounded p-3 mb-3">
                  <p className="font-semibold text-sm mb-2">📋 Как применить миграцию:</p>
                  <ol className="list-decimal list-inside space-y-1 text-sm">
                    <li>Откройте <a href="https://supabase.com/dashboard" target="_blank" rel="noopener noreferrer" className="underline font-medium">Supabase Dashboard</a></li>
                    <li>Выберите ваш проект</li>
                    <li>Перейдите в <strong>SQL Editor</strong> (в боковом меню)</li>
                    <li>Откройте страницу <a href="/migrate" className="underline font-medium">/migrate</a> для копирования SQL</li>
                    <li>Вставьте SQL в редактор и нажмите <strong>Run</strong></li>
                  </ol>
                </div>
                <div className="flex gap-2">
                  <a
                    href="/migrate"
                    className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors text-sm font-medium"
                  >
                    📋 Открыть SQL миграцию
                  </a>
                </div>
              </>
            ) : (
              <>
                <p className="font-semibold">Ошибка:</p>
                <p>{error}</p>
              </>
            )}
          </div>
        )}

        {!loading && !error && (
          <>
            <div className="bg-white rounded-lg shadow overflow-hidden">
              {users.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  Пользователи не найдены
                </div>
              ) : (
                <ul className="divide-y divide-gray-200">
                  {users.map((user) => (
                    <li key={user.user_id} className="p-4 hover:bg-gray-50">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-semibold text-gray-900">
                            {user.first_name || 'Без имени'}
                            {user.last_name && ` ${user.last_name}`}
                          </p>
                          {user.username && (
                            <p className="text-sm text-gray-600">
                              @{user.username}
                            </p>
                          )}
                          <p className="text-xs text-gray-500 mt-1">
                            ID: {user.user_id}
                          </p>
                        </div>
                        <div className="text-right">
                          {user.subscription_type && (
                            <span className="inline-block px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">
                              {user.subscription_type}
                            </span>
                          )}
                          {user.created_at && (
                            <p className="text-xs text-gray-500 mt-1">
                              {new Date(user.created_at).toLocaleDateString('ru-RU')}
                            </p>
                          )}
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="mt-6 text-center">
              <button
                onClick={loadUsers}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
              >
                Обновить список
              </button>
            </div>
          </>
        )}
      </div>
    </main>
  )
}
