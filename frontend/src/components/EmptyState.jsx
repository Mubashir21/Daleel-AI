import DaleelIcon from "./DaleelIcon"
import { useRotatingQuestions } from "@/hooks/use-rotating-questions"

const STAGGER = ["delay-0", "delay-100", "delay-200"]

export default function EmptyState({ onSelect }) {
  const { questions, visible } = useRotatingQuestions()

  return (
    <div className="flex flex-col items-center justify-center h-full gap-6 px-4 text-center">
      <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 fill-mode-both">
        <div className="flex items-center justify-center mx-auto mb-3">
          <DaleelIcon size={52} className="text-primary" />
        </div>
        <h2 className="text-xl font-heading font-medium tracking-tight text-foreground">
          Grounded answers, backed by real sources.
        </h2>
      </div>

      <div className="flex flex-col gap-2 w-full max-w-sm h-[200px] overflow-hidden">
        {questions.map((item, i) => (
          <button
            key={item.question}
            onClick={() => onSelect(item.question)}
            className={[
              "text-left text-sm px-4 py-2.5 rounded-xl border border-border bg-card",
              "hover:bg-accent hover:border-primary/30 transition-colors text-muted-foreground hover:text-foreground",
              visible
                ? `animate-in fade-in slide-in-from-bottom-2 duration-500 fill-mode-both ${STAGGER[i]}`
                : `animate-out fade-out slide-out-to-top-2 duration-300 fill-mode-forwards ${STAGGER[i]}`,
            ].join(" ")}
          >
            {item.question}
          </button>
        ))}
      </div>
    </div>
  )
}
