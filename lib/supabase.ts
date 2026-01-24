import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL || ''
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || process.env.SUPABASE_API_KEY || ''

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn('⚠️ Supabase URL или ключ не установлены. Установите NEXT_PUBLIC_SUPABASE_URL и NEXT_PUBLIC_SUPABASE_ANON_KEY')
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

export interface TelegramUser {
  user_id: number
  username: string | null
  first_name: string | null
  last_name?: string | null
  birth_date: string | null
  registration_date: string
  subscription_type: string
  subscription_end_date: string | null
  is_active: boolean
  is_admin: boolean
  created_at: string
  updated_at: string
}
