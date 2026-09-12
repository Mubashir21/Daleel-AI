import { Badge } from "@/components/ui/badge"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"

export default function CitationPill({ number, sources }) {
  const n = typeof number === "string" ? parseInt(number, 10) : number
  const source = sources?.find((s) => s.number === n)

  // Unknown citation number (shouldn't happen against a real answer) — fall
  // back to the plain bracket text rather than rendering a pill that links nowhere.
  if (!source) return `[Source ${n}]`

  const domain = source.url.replace(/^https?:\/\//, "").split("/")[0]
  const tooltipText = source.title || domain

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <a
          href={source.url}
          target="_blank"
          rel="noopener noreferrer"
          className="no-underline"
        >
          <Badge
            variant="outline"
            className="mx-0.5 -translate-y-px border-primary/40 bg-primary/15 font-semibold text-primary transition-colors hover:bg-primary hover:text-primary-foreground"
          >
            {n}
          </Badge>
        </a>
      </TooltipTrigger>
      <TooltipContent>{tooltipText}</TooltipContent>
    </Tooltip>
  )
}
