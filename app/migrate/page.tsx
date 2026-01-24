'use client'

import { useState, useEffect } from 'react'

export default function MigratePage() {
  const [sql, setSql] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [applying, setApplying] = useState(false)
  const [applyResult, setApplyResult] = useState<{ success: boolean; message?: string; error?: string; tablesCreated?: string[] } | null>(null)

  useEffect(() => {
    // Загружаем SQL через API
    fetch('/api/migrate')
      .then(res => res.json())
      .then(data => {
        if (data.sql) {
          setSql(data.sql)
        }
        setLoading(false)
      })
      .catch(() => {
        // Если API не работает, показываем инструкции
        setLoading(false)
      })
  }, [])

  const copyToClipboard = () => {
    if (sql) {
      navigator.clipboard.writeText(sql)
      alert('SQL скопирован в буфер обмена!')
    }
  }

  const applyMigration = async () => {
    if (!confirm('Применить миграцию к базе данных? Это создаст все необходимые таблицы.')) {
      return
    }

    setApplying(true)
    setApplyResult(null)

    try {
      const response = await fetch('/api/migrate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      const data = await response.json()

      if (data.success) {
        setApplyResult({
          success: true,
          message: data.message || 'Миграция успешно применена!',
          tablesCreated: data.tablesCreated,
        })
      } else {
        setApplyResult({
          success: false,
          error: data.error || 'Неизвестная ошибка',
        })
      }
    } catch (error) {
      setApplyResult({
        success: false,
        error: error instanceof Error ? error.message : 'Ошибка при применении миграции',
      })
    } finally {
      setApplying(false)
    }
  }

  return (
    <main className="min-h-screen p-8 bg-gray-50">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-6 text-gray-900">
          Применение миграции базы данных
        </h1>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <h2 className="font-semibold text-blue-900 mb-2">📋 Способы применения миграции:</h2>
          <ol className="list-decimal list-inside space-y-2 text-blue-800">
            <li><strong>Автоматически (РЕКОМЕНДУЕТСЯ):</strong> Нажмите кнопку "Применить миграцию" ниже (требуется SUPABASE_DB_URL в .env.local)</li>
            <li><strong>Вручную:</strong> Откройте <a href="https://supabase.com/dashboard" target="_blank" rel="noopener noreferrer" className="underline">Supabase Dashboard</a> → SQL Editor → Скопируйте SQL ниже → Вставьте и нажмите Run</li>
          </ol>
        </div>

        {applyResult && (
          <div className={`mb-6 p-4 rounded-lg border ${
            applyResult.success 
              ? 'bg-green-50 border-green-200' 
              : 'bg-red-50 border-red-200'
          }`}>
            {applyResult.success ? (
              <>
                <h3 className="font-semibold text-green-900 mb-2">✅ {applyResult.message}</h3>
                {applyResult.tablesCreated && applyResult.tablesCreated.length > 0 && (
                  <div className="mt-2">
                    <p className="text-green-800 text-sm font-medium mb-1">Созданные таблицы ({applyResult.tablesCreated.length}):</p>
                    <ul className="list-disc list-inside text-green-700 text-sm">
                      {applyResult.tablesCreated.map(table => (
                        <li key={table}>{table}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            ) : (
              <>
                <h3 className="font-semibold text-red-900 mb-2">❌ Ошибка при применении миграции</h3>
                <p className="text-red-800 text-sm">{applyResult.error}</p>
                <p className="text-red-700 text-sm mt-2">
                  Убедитесь, что <code className="bg-red-100 px-1 rounded">SUPABASE_DB_URL</code> установлен в <code className="bg-red-100 px-1 rounded">.env.local</code>
                </p>
              </>
            )}
          </div>
        )}

        {loading ? (
          <div className="text-center py-8 text-gray-600">
            Загрузка SQL миграции...
          </div>
        ) : sql ? (
          <>
            <div className="bg-white rounded-lg shadow overflow-hidden mb-4">
              <div className="bg-gray-100 px-4 py-2 flex justify-between items-center">
                <span className="text-sm font-medium text-gray-700">
                  migrations/001_create_tables.sql
                </span>
                <div className="flex gap-2">
                  <button
                    onClick={applyMigration}
                    disabled={applying}
                    className="px-4 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                  >
                    {applying ? '⏳ Применение...' : '🚀 Применить миграцию'}
                  </button>
                  <button
                    onClick={copyToClipboard}
                    className="px-4 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
                  >
                    📋 Копировать SQL
                  </button>
                </div>
              </div>
              <pre className="p-4 overflow-x-auto text-sm bg-gray-900 text-gray-100">
                <code>{sql}</code>
              </pre>
            </div>

            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h3 className="font-semibold text-green-900 mb-2">✅ После применения:</h3>
              <p className="text-green-800 text-sm">
                Миграция создаст все необходимые таблицы для работы бота. 
                Вы можете проверить их в Supabase Dashboard → Table Editor.
              </p>
            </div>
          </>
        ) : (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <p className="text-yellow-800">
              Не удалось загрузить SQL. Пожалуйста, откройте файл{' '}
              <code className="bg-yellow-100 px-2 py-1 rounded">migrations/001_create_tables.sql</code>{' '}
              вручную и скопируйте его содержимое.
            </p>
          </div>
        )}

        <div className="mt-6 p-4 bg-gray-100 rounded-lg">
          <h3 className="font-semibold mb-2">💡 Альтернативные способы:</h3>
          <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
            <li>
              <strong>Node.js скрипт:</strong> Добавьте <code>SUPABASE_DB_URL</code> в <code>.env.local</code> и запустите <code>npm run migrate</code>
            </li>
            <li>
              <strong>Python скрипт:</strong> Добавьте <code>SUPABASE_DB_URL</code> в <code>.env</code> и запустите <code>python scripts/apply_migration.py</code>
            </li>
          </ul>
        </div>
      </div>
    </main>
  )
}
