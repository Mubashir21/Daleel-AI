import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { SidebarMenuButton } from "@/components/ui/sidebar"
import { Info } from "lucide-react"

const steps = [
  {
    title: "Routing",
    body: "Each message is first classified: does it need new Islamic sources, or can it be answered from the conversation so far? Simple follow-ups like 'explain that more simply' skip retrieval entirely.",
  },
  {
    title: "Retrieval",
    body: "When new sources are needed, your question is matched against ~39,000 chunks from ~15,000 IslamQA questions and answers using hybrid search — combining semantic vector search and keyword search so neither vague nor specific queries fall through.",
  },
  {
    title: "Reranking",
    body: "The top 40 candidate chunks are reranked by Cohere's reranking model to surface the 5 most relevant passages.",
  },
  {
    title: "Generation",
    body: "The retrieved passages are passed to a language model with strict instructions to only use the provided sources — no outside knowledge. The answer streams back in real time with inline citations.",
  },
]

export default function HowItWorksDialog() {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <SidebarMenuButton tooltip="How it works">
          <Info />
          <span>How it works</span>
        </SidebarMenuButton>
      </DialogTrigger>
      <DialogContent className="max-w-md max-h-[85dvh] flex flex-col">
        <DialogHeader>
          <DialogTitle>How it works</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 text-sm text-muted-foreground leading-relaxed overflow-y-auto pr-1">
          <div className="space-y-3">
            {steps.map((step, i) => (
              <div key={step.title} className="flex gap-3">
                <div className="w-5 h-5 rounded-full bg-primary/10 text-primary flex items-center justify-center text-xs font-semibold shrink-0 mt-0.5">
                  {i + 1}
                </div>
                <div>
                  <p className="font-medium text-foreground">{step.title}</p>
                  <p className="mt-0.5">{step.body}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="border-t border-border pt-3 space-y-1.5">
            <p className="font-medium text-foreground">Things to know</p>
            <ul className="space-y-1 list-disc list-outside pl-4">
              <li>Conversation context is kept within your session. Closing or refreshing the page starts a fresh conversation.</li>
              <li>Cohere's free tier is used for reranking, which has a rate limit of 10 requests per minute.</li>
              <li>Source content is from IslamQA. All credit for the underlying knowledge goes to them.</li>
              <li>New and updated IslamQA articles are picked up automatically every week, so answers stay current.</li>
            </ul>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
