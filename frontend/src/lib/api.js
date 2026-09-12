const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000"

export function parseSources(text) {
  const parts = text.split(/###\s*Sources/i)
  const answer = parts[0].trim()
  const sources = []

  if (parts[1]) {
    const lines = parts[1].trim().split("\n")
    for (const line of lines) {
      const match = line.match(/\[Source\s*(\d+)\]\s*(https?:\/\/\S+)/i)
      if (match) {
        sources.push({ number: parseInt(match[1]), url: match[2].trim() })
      }
    }
  }

  return { answer, sources }
}

export async function streamChat(message, sessionId, onSessionId, onStatus, onChunk, onSourceTitles, onDone, onError) {
  let res

  try {
    res = await fetch(`${API_BASE}/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: sessionId ?? null }),
    })
  } catch (err) {
    onError(err)
    return
  }

  if (!res.ok) {
    onError(new Error(`Server error: ${res.status}`))
    return
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let accumulated = ""
  let buffer = ""

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      // SSE events are separated by double newlines
      const events = buffer.split("\n\n")
      buffer = events.pop() // last chunk may be incomplete

      for (const event of events) {
        if (!event.trim()) continue

        // Parse event type and data from the block
        const lines = event.split("\n")
        let eventType = "message"
        let dataLine = ""

        for (const line of lines) {
          if (line.startsWith("event: ")) eventType = line.slice(7).trim()
          if (line.startsWith("data: ")) dataLine = line.slice(6).trim()
        }

        if (!dataLine) continue

        if (eventType === "session") {
          const { session_id } = JSON.parse(dataLine)
          onSessionId(session_id)
        } else if (eventType === "status") {
          const { message: msg } = JSON.parse(dataLine)
          onStatus(msg)
        } else if (eventType === "token") {
          const { text } = JSON.parse(dataLine)
          accumulated += text
          // Strip a "### Sources" footer as it streams in, not just at the
          // end — otherwise it renders raw (heading + bracket citations)
          // for a moment before onDone replaces it with the parsed answer.
          onChunk(parseSources(accumulated).answer)
        } else if (eventType === "sources") {
          onSourceTitles(JSON.parse(dataLine))
        } else if (eventType === "done") {
          onDone(parseSources(accumulated))
          return
        }
      }
    }
  } catch (err) {
    onError(err)
    return
  }

  onDone(parseSources(accumulated))
}
