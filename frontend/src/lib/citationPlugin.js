import { visit } from "unist-util-visit"

const CITATION_RE = /\[Source\s*(\d+)\]/g

/**
 * Splits text nodes on "[Source N]" markers and replaces each match with a
 * `citationPill` mdast node, so react-markdown can render it as a component
 * instead of literal text. Runs before react-markdown's own node-to-React
 * conversion, on the parsed markdown tree.
 */
export function remarkCitations() {
  return (tree) => {
    visit(tree, "text", (node, index, parent) => {
      if (!parent || index === null) return
      CITATION_RE.lastIndex = 0
      if (!CITATION_RE.test(node.value)) return

      const children = []
      let lastIndex = 0
      CITATION_RE.lastIndex = 0
      let match
      while ((match = CITATION_RE.exec(node.value))) {
        if (match.index > lastIndex) {
          children.push({ type: "text", value: node.value.slice(lastIndex, match.index) })
        }
        children.push({
          type: "citationPill",
          data: { hName: "citation-pill", hProperties: { number: match[1] } },
        })
        lastIndex = match.index + match[0].length
      }
      if (lastIndex < node.value.length) {
        children.push({ type: "text", value: node.value.slice(lastIndex) })
      }

      parent.children.splice(index, 1, ...children)
      return index + children.length
    })
  }
}
