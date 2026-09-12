import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { SidebarMenuButton } from "@/components/ui/sidebar"
import { TriangleAlert } from "lucide-react"

export default function DisclaimerDialog() {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <SidebarMenuButton tooltip="Disclaimer">
          <TriangleAlert />
          <span>Disclaimer</span>
        </SidebarMenuButton>
      </DialogTrigger>
      <DialogContent className="max-w-md max-h-[85dvh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Disclaimer</DialogTitle>
        </DialogHeader>
        <div className="space-y-3 text-sm text-muted-foreground leading-relaxed overflow-y-auto pr-1">
          <p>
            This is an experimental AI tool that answers Islamic questions by
            summarizing content from IslamQA. It is not a substitute for qualified Islamic scholarship.
          </p>
          <p>
            All answers are AI-generated summaries based on Q&amp;A content from{" "}
            <a
              href="https://islamqa.info"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary underline underline-offset-2"
            >
              IslamQA.info
            </a>
            . The tool may misrepresent, omit, or incorrectly attribute rulings.
          </p>
          <p>
            <span className="font-medium text-foreground">
              Always verify with a qualified Islamic scholar
            </span>{" "}
            before acting on any information provided here.
          </p>
          <p>
            I do not bear any responsibility for decisions made based on the
            output of this tool.
          </p>
        </div>
      </DialogContent>
    </Dialog>
  )
}
