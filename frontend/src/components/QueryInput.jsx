import { useState } from "react"
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import { ArrowUp } from "lucide-react"

export default function QueryInput({ onSubmit, disabled, value: controlledValue, onValueChange }) {
  const [internalValue, setInternalValue] = useState("")
  const isControlled = controlledValue !== undefined
  const value = isControlled ? controlledValue : internalValue
  const setValue = isControlled ? onValueChange : setInternalValue

  function handleSubmit() {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSubmit(trimmed)
    setValue("")
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="bg-background px-4 pt-2 pb-4 shrink-0">
      <div className="max-w-3xl mx-auto">
        <div className="flex items-end gap-1.5 rounded-4xl border border-input bg-transparent px-4 py-2 transition-colors focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/50 dark:bg-input/30">
          <Textarea
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about Islam…"
            disabled={disabled}
            autoFocus
            rows={1}
            className="resize-none min-h-9 max-h-[120px] overflow-y-auto flex-1 border-0 bg-transparent px-1.5 py-1.5 text-base shadow-none outline-none focus-visible:border-0 focus-visible:ring-0 disabled:bg-transparent dark:bg-transparent dark:disabled:bg-transparent sm:text-sm"
          />
          <Button
            onClick={handleSubmit}
            disabled={!value.trim() || disabled}
            size="icon"
            className="shrink-0 h-9 w-9 rounded-4xl"
          >
            <ArrowUp className="w-4 h-4" />
          </Button>
        </div>
        <p className="text-center text-xs text-muted-foreground mt-2">
          Answers are AI-generated summaries of IslamQA Q&As. Always verify with a qualified scholar.
        </p>
      </div>
    </div>
  )
}
