import { NextResponse } from 'next/server'
import { Client } from 'pg'
import fs from 'fs'
import path from 'path'

/**
 * API Route для применения миграции
 * ВАЖНО: Используйте только в development или защитите этот endpoint!
 */
export async function POST(request: Request) {
  try {
    // Проверка на production (опционально)
    if (process.env.NODE_ENV === 'production') {
      const authHeader = request.headers.get('authorization')
      const secret = process.env.MIGRATION_SECRET
      
      if (!secret || authHeader !== `Bearer ${secret}`) {
        return NextResponse.json(
          { error: 'Unauthorized' },
          { status: 401 }
        )
      }
    }

    // Получаем DATABASE_URL из переменных окружения
    const databaseUrl = 
      process.env.SUPABASE_DB_URL || 
      process.env.DATABASE_URL ||
      process.env.POSTGRES_URL ||
      process.env.POSTGRES_PRISMA_URL

    if (!databaseUrl) {
      return NextResponse.json(
        {
          success: false,
          error: 'SUPABASE_DB_URL не установлен в переменных окружения',
          instructions: [
            '1. Добавьте SUPABASE_DB_URL в .env.local',
            '2. Получите Connection String из Supabase Dashboard → Settings → Database'
          ]
        },
        { status: 400 }
      )
    }

    // Читаем SQL миграцию
    const migrationFile = path.join(process.cwd(), 'migrations', '001_create_tables.sql')
    
    if (!fs.existsSync(migrationFile)) {
      return NextResponse.json(
        { error: 'Migration file not found' },
        { status: 404 }
      )
    }

    const sql = fs.readFileSync(migrationFile, 'utf-8')

    // Подключаемся к базе данных и применяем миграцию
    const client = new Client({
      connectionString: databaseUrl,
      ssl: {
        rejectUnauthorized: false
      }
    })

    try {
      await client.connect()
      
      // Применяем миграцию
      await client.query(sql)
      
      // Проверяем созданные таблицы
      const result = await client.query(`
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE 'telegram_%'
        ORDER BY table_name
      `)

      const tables = result.rows.map(row => row.table_name)

      await client.end()

      return NextResponse.json({
        success: true,
        message: 'Миграция успешно применена!',
        tablesCreated: tables,
        tablesCount: tables.length
      })

    } catch (dbError) {
      await client.end()
      throw dbError
    }

  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error'
    
    return NextResponse.json(
      {
        success: false,
        error: errorMessage,
        ...(errorMessage.includes('already exists') && {
          message: 'Некоторые таблицы уже существуют. Это нормально, если миграция уже была применена ранее.'
        })
      },
      { status: 500 }
    )
  }
}

export async function GET() {
  try {
    // Читаем SQL миграцию
    const migrationFile = path.join(process.cwd(), 'migrations', '001_create_tables.sql')
    
    if (!fs.existsSync(migrationFile)) {
      return NextResponse.json(
        { error: 'Migration file not found' },
        { status: 404 }
      )
    }

    const sql = fs.readFileSync(migrationFile, 'utf-8')

    return NextResponse.json({
      success: true,
      sql: sql,
      instructions: [
        '1. Откройте Supabase Dashboard → SQL Editor',
        '2. Скопируйте SQL из поля "sql"',
        '3. Вставьте в редактор и нажмите "Run"'
      ]
    })
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    )
  }
}
