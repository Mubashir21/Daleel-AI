import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { Message, MessageContent } from "@/components/ui/message"
import { Bubble, BubbleContent } from "@/components/ui/bubble"
import { Marker, MarkerContent } from "@/components/ui/marker"
import CopyButton from "./CopyButton"
import CitationPill from "./CitationPill"
import { remarkCitations } from "@/lib/citationPlugin"

function UserBubble({ text }) {
  return (
    <Message align="end">
      <MessageContent>
        <Bubble align="end">
          <BubbleContent className="rounded-br-sm">{text}</BubbleContent>
        </Bubble>
      </MessageContent>
    </Message>
  )
}

function StatusIndicator({ status }) {
  return (
    <Message align="start">
      <MessageContent>
        <Marker>
          <MarkerContent className="shimmer">{status}</MarkerContent>
        </Marker>
      </MessageContent>
    </Message>
  )
}

function AssistantBubble({ text, sources, loading, status, done }) {
  if (loading) {
    return <StatusIndicator status={status} />
  }

  const markdownComponents = {
    "citation-pill": ({ number }) => <CitationPill number={number} sources={sources} />,
    table: ({ children }) => (
      <div className="overflow-x-auto">
        <table>{children}</table>
      </div>
    ),
  }

  return (
    <Message align="start">
      <MessageContent>
        <div
          className="prose prose-sm prose-neutral dark:prose-invert max-w-none text-foreground
          [&_h3]:text-sm [&_h3]:font-semibold [&_h3]:mt-3 [&_h3]:mb-1
          [&_p]:text-sm [&_p]:leading-relaxed [&_p]:mb-2
          [&_ul]:text-sm [&_ul]:pl-4 [&_ul]:mb-2
          [&_li]:mb-0.5
          [&_table]:text-sm [&_th]:font-semibold"
        >
          <ReactMarkdown remarkPlugins={[remarkGfm, remarkCitations]} components={markdownComponents}>
            {text}
          </ReactMarkdown>
        </div>
        {done && (
          <div className="flex justify-start">
            <CopyButton text={text} />
          </div>
        )}
      </MessageContent>
    </Message>
  )
}

export default function MessageBubble({ message }) {
  if (message.role === "user") return <UserBubble text={message.text} />
  return (
    <AssistantBubble
      text={message.text}
      sources={message.sources}
      loading={message.loading}
      status={message.status}
      done={message.done}
    />
  )
}
