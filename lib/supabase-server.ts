import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL || ''
// Для серверной части используем service role key, если доступен, иначе anon key
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || 
                    process.env.SUPABASE_API_KEY || 
                    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 
                    ''

if (!supabaseUrl || !supabaseKey) {
  console.warn('⚠️ Supabase URL или ключ не установлены для серверной части')
}

export const supabaseServer = createClient(supabaseUrl, supabaseKey, {
  auth: {
    autoRefreshToken: false,
    persistSession: false
  }
})
