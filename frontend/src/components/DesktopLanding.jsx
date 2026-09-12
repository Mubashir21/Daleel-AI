import { useState } from "react"
import QueryInput from "./QueryInput"
import { useRotatingQuestions } from "@/hooks/use-rotating-questions"

export default function DesktopLanding({ onSubmit, disabled }) {
  const { questions, visible } = useRotatingQuestions()
  const [value, setValue] = useState("")

  return (
    <div className="w-full max-w-2xl px-4 flex flex-col items-center">
      <h2 className="mb-8 text-3xl font-heading font-medium tracking-tight text-foreground text-center animate-in fade-in slide-in-from-bottom-4 duration-500 fill-mode-both">
        Grounded answers, backed by real sources.
      </h2>

      <div className="w-full">
        <QueryInput onSubmit={onSubmit} disabled={disabled} value={value} onValueChange={setValue} />
      </div>

      <div className="mt-2 flex flex-wrap items-center justify-center gap-2 max-w-xl">
        {questions.map((item) => {
          const Icon = item.icon
          return (
            <button
              key={item.question}
              onClick={() => setValue(item.question)}
              className={[
                "flex items-center gap-1.5 text-sm px-3.5 py-1.5 rounded-4xl border border-border bg-card whitespace-nowrap",
                "hover:bg-accent hover:border-primary/30 transition-colors text-muted-foreground hover:text-foreground",
                visible
                  ? "animate-in fade-in slide-in-from-bottom-2 duration-500 fill-mode-both"
                  : "animate-out fade-out slide-out-to-top-2 duration-300 fill-mode-forwards",
              ].join(" ")}
            >
              <Icon className="w-3.5 h-3.5 shrink-0" />
              {item.label}
            </button>
          )
        })}
      </div>
    </div>
  )
}
