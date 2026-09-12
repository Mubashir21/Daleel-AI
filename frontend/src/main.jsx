import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import posthog from 'posthog-js'
import { PostHogProvider } from 'posthog-js/react'
import './index.css'
import App from './App.jsx'
import { ThemeProvider } from './components/theme-provider.jsx'
import { TooltipProvider } from './components/ui/tooltip.jsx'

if (import.meta.env.VITE_PUBLIC_POSTHOG_TOKEN) {
  posthog.init(import.meta.env.VITE_PUBLIC_POSTHOG_TOKEN, {
    api_host: import.meta.env.VITE_PUBLIC_POSTHOG_HOST ?? 'https://us.i.posthog.com',
    defaults: '2026-01-30',
    person_profiles: 'identified_only',
  })
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <PostHogProvider client={posthog}>
      <ThemeProvider defaultTheme="system" storageKey="daleel-ai-theme">
        <TooltipProvider>
          <App />
        </TooltipProvider>
      </ThemeProvider>
    </PostHogProvider>
  </StrictMode>,
)
