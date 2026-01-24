/**
 * Скрипт для применения миграции к Supabase через Node.js
 * Поддерживает прямое подключение к PostgreSQL через SUPABASE_DB_URL
 */
const { Client } = require('pg')
const fs = require('fs')
const path = require('path')
// Загружаем переменные из .env (базовые) и .env.local (переопределения)
require('dotenv').config() // Загружает .env
require('dotenv').config({ path: '.env.local' }) // Переопределяет значения из .env.local, если файл существует

async function applyMigration() {
  console.log('🚀 Применение миграции к Supabase/PostgreSQL')
  console.log('='.repeat(60))

  // Проверяем наличие SUPABASE_DB_URL
  const databaseUrl = 
    process.env.SUPABASE_DB_URL || 
    process.env.DATABASE_URL ||
    process.env.POSTGRES_URL ||
    process.env.POSTGRES_PRISMA_URL

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL

  if (!databaseUrl) {
    console.log('\n⚠️  SUPABASE_DB_URL не установлен в .env.local')
    console.log('\n💡 Для применения миграции через скрипт нужен прямой доступ к PostgreSQL')
    console.log('   Получите Connection String из Supabase Dashboard:')
    console.log('   1. Откройте https://supabase.com/dashboard')
    console.log('   2. Выберите ваш проект')
    console.log('   3. Перейдите в Settings → Database')
    console.log('   4. Скопируйте Connection String (URI)')
    console.log('   5. Добавьте в .env.local: SUPABASE_DB_URL=<connection-string>\n')
    
    if (supabaseUrl) {
      console.log('📋 Альтернативный способ (РЕКОМЕНДУЕТСЯ):')
      console.log('   1. Откройте Supabase Dashboard → SQL Editor')
      console.log('   2. Скопируйте содержимое файла: migrations/001_create_tables.sql')
      console.log('   3. Вставьте SQL в редактор и нажмите "Run"\n')
    }
    
    process.exit(1)
  }

  // Читаем SQL миграцию
  const migrationFile = path.join(__dirname, '..', 'migrations', '001_create_tables.sql')
  
  if (!fs.existsSync(migrationFile)) {
    console.error(`❌ Файл миграции ${migrationFile} не найден!`)
    process.exit(1)
  }

  const sql = fs.readFileSync(migrationFile, 'utf-8')

  console.log(`\n🔗 Подключение к базе данных...`)
  if (supabaseUrl) {
    console.log(`   Supabase URL: ${supabaseUrl}`)
  }
  
  // Для Supabase pooler нужно использовать прямой connection string
  // Если URL содержит pooler, заменяем на прямой хост
  let connUrl = databaseUrl
  if (connUrl.includes('pooler.supabase.com')) {
    console.log('   Обнаружен pooler URL, используем прямое подключение...')
    // Заменяем pooler на прямой хост
    connUrl = connUrl.replace('pooler.supabase.com', 'db.supabase.co')
    // Убираем параметры pgbouncer
    if (connUrl.includes('?')) {
      connUrl = connUrl.split('?')[0]
    }
  }
  
  // Скрываем пароль в URL для вывода
  const debugUrl = connUrl.replace(/:[^:@]+@/, ':****@')
  console.log(`   Connection URL: ${debugUrl.substring(0, 80)}...`)

  const client = new Client({
    connectionString: connUrl,
    ssl: {
      rejectUnauthorized: false
    }
  })

  try {
    await client.connect()
    console.log('✅ Подключение установлено\n')

    console.log(`📝 Применение миграции из ${path.basename(migrationFile)}...`)
    
    // Выполняем миграцию
    await client.query(sql)
    
    console.log('✅ Миграция успешно применена!\n')

    // Проверяем созданные таблицы
    console.log('📊 Проверка созданных таблиц...')
    const result = await client.query(`
      SELECT table_name 
      FROM information_schema.tables 
      WHERE table_schema = 'public' 
      AND table_name LIKE 'telegram_%'
      ORDER BY table_name
    `)

    if (result.rows.length > 0) {
      console.log(`\n✅ Найдено таблиц: ${result.rows.length}`)
      result.rows.forEach(row => {
        console.log(`   ✓ ${row.table_name}`)
      })
    } else {
      console.log('\n⚠️  Таблицы не найдены. Возможно, они уже существуют или произошла ошибка.')
    }

    await client.end()
    
    console.log('\n' + '='.repeat(60))
    console.log('✅ Миграция успешно применена! Готово!')

  } catch (error) {
    await client.end()
    
    console.error(`\n❌ Ошибка при применении миграции: ${error.message}`)
    console.log('='.repeat(60))

    if (error.message.includes('getaddrinfo') || error.message.includes('ENOTFOUND')) {
      console.log('\n💡 Проблема с подключением к серверу базы данных')
      console.log('   Возможные причины:')
      console.log('   - Неверный SUPABASE_DB_URL')
      console.log('   - Проблемы с сетью')
      console.log('\n💡 Решение:')
      console.log('   1. Проверьте SUPABASE_DB_URL в .env.local')
      console.log('   2. Убедитесь, что используете правильный Connection String')
      console.log('   3. Или примените миграцию через Supabase Dashboard → SQL Editor')
    } else if (error.message.includes('password') || error.message.includes('authentication')) {
      console.log('\n💡 Неверный пароль базы данных')
      console.log('   Решение:')
      console.log('   1. Откройте Supabase Dashboard → Settings → Database')
      console.log('   2. Проверьте или сбросьте пароль базы данных')
      console.log('   3. Обновите SUPABASE_DB_URL в .env.local')
    } else if (error.message.includes('already exists')) {
      console.log('\n⚠️  Некоторые таблицы уже существуют')
      console.log('   Это нормально, если миграция уже была применена ранее')
      console.log('   SQL использует CREATE TABLE IF NOT EXISTS, поэтому ошибка не критична')
    } else {
      console.log('\n💡 Общие рекомендации:')
      console.log('   1. Проверьте правильность SUPABASE_DB_URL в .env.local')
      console.log('   2. Убедитесь, что пароль правильно закодирован в URL')
      console.log('   3. Попробуйте применить миграцию через Supabase Dashboard:')
      console.log('      - Откройте SQL Editor')
      console.log('      - Скопируйте содержимое: migrations/001_create_tables.sql')
      console.log('      - Вставьте и выполните SQL')
    }

    process.exit(1)
  }
}

applyMigration().catch(error => {
  console.error('❌ Критическая ошибка:', error)
  process.exit(1)
})
