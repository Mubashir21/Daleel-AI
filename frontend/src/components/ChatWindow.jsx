import {
  MessageScrollerProvider,
  MessageScroller,
  MessageScrollerViewport,
  MessageScrollerContent,
  MessageScrollerItem,
  MessageScrollerButton,
} from "@/components/ui/message-scroller"
import MessageBubble from "./MessageBubble"
import EmptyState from "./EmptyState"

export default function ChatWindow({ messages, onExampleSelect }) {
  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center min-h-0">
        <EmptyState onSelect={onExampleSelect} />
      </div>
    )
  }

  return (
    <MessageScrollerProvider autoScroll defaultScrollPosition="last-anchor" scrollPreviousItemPeek={64}>
      <MessageScroller className="flex-1 min-h-0">
        <MessageScrollerViewport>
          <MessageScrollerContent className="max-w-3xl w-full mx-auto px-4 py-6">
            {messages.map((msg) => (
              <MessageScrollerItem key={msg.id} messageId={msg.id} scrollAnchor={msg.role === "user"}>
                <MessageBubble message={msg} />
              </MessageScrollerItem>
            ))}
          </MessageScrollerContent>
        </MessageScrollerViewport>
        <MessageScrollerButton />
      </MessageScroller>
    </MessageScrollerProvider>
  )
}
