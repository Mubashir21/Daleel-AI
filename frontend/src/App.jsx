import { useState, useRef } from "react"
import { SidebarProvider, SidebarInset, SidebarTrigger } from "@/components/ui/sidebar"
import AppSidebar from "./components/AppSidebar"
import ChatWindow from "./components/ChatWindow"
import QueryInput from "./components/QueryInput"
import DesktopLanding from "./components/DesktopLanding"
import { streamChat } from "./lib/api"

export default function App() {
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const sessionIdRef = useRef(null)

  function handleHome() {
    setMessages([])
    setLoading(false)
    sessionIdRef.current = null
  }

  function handleSubmit(question) {
    const userMsg = { id: Date.now(), role: "user", text: question }
    const placeholderId = Date.now() + 1
    const placeholder = {
      id: placeholderId,
      role: "assistant",
      text: "",
      sources: [],
      loading: true,
      status: "Thinking...",
      done: false,
    }

    setMessages((prev) => [...prev, userMsg, placeholder])
    setLoading(true)

    let sourceTitles = {}

    streamChat(
      question,
      sessionIdRef.current,

      // onSessionId — store session ID for future messages
      (id) => {
        sessionIdRef.current = id
      },

      // onStatus — update the status line in the placeholder
      (msg) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === placeholderId ? { ...m, status: msg } : m
          )
        )
      },

      // onChunk — replace with cleaned answer-so-far, clear status once answer starts flowing
      (textSoFar) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === placeholderId
              ? { ...m, text: textSoFar, loading: false, status: null }
              : m
          )
        )
      },

      // onSourceTitles — capture the backend's {number: title} map for this turn
      (titles) => {
        sourceTitles = titles
      },

      // onDone — replace placeholder with final parsed answer + sources
      ({ answer, sources }) => {
        const enrichedSources = sources.map((s) => ({ ...s, title: sourceTitles[s.number] }))
        setMessages((prev) =>
          prev.map((m) =>
            m.id === placeholderId
              ? { ...m, text: answer, sources: enrichedSources, loading: false, status: null, done: true }
              : m
          )
        )
        setLoading(false)
      },

      // onError
      (err) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === placeholderId
              ? { ...m, text: `Something went wrong: ${err.message}`, sources: [], loading: false, status: null, done: true }
              : m
          )
        )
        setLoading(false)
      }
    )
  }

  return (
    <SidebarProvider className="h-svh">
      <AppSidebar onHome={handleHome} />
      <SidebarInset className="overflow-hidden">
        <header className="flex h-16 items-center gap-2 px-4 shrink-0">
          <SidebarTrigger className="-ml-1" />
        </header>
        {messages.length === 0 ? (
          <>
            <div className="flex flex-col flex-1 min-h-0 md:hidden">
              <ChatWindow messages={messages} onExampleSelect={handleSubmit} />
              <QueryInput onSubmit={handleSubmit} disabled={loading} />
            </div>
            <div className="hidden md:flex flex-1 min-h-0 items-center justify-center pb-[18vh]">
              <DesktopLanding onSubmit={handleSubmit} disabled={loading} />
            </div>
          </>
        ) : (
          <>
            <ChatWindow messages={messages} onExampleSelect={handleSubmit} />
            <QueryInput onSubmit={handleSubmit} disabled={loading} />
          </>
        )}
      </SidebarInset>
    </SidebarProvider>
  )
}
