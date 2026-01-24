import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Bot Dar Stars',
  description: 'Веб-интерфейс для бота Dar Stars',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  )
}
