import { useState, useEffect } from "react"
import { Footprints, Landmark, Scroll, Building2, Music2, UtensilsCrossed, Plane, Dog, Cake } from "lucide-react"

export const EXAMPLE_QUESTIONS = [
  { label: "Prayer with shoes", question: "What is the ruling on praying with shoes on?", icon: Footprints },
  { label: "Mortgages", question: "Is it permissible to take out a mortgage to buy a house?", icon: Landmark },
  { label: "Marriage contract", question: "What are the conditions for a valid Islamic marriage contract?", icon: Scroll },
  { label: "Banking", question: "What is the Islamic ruling on working in a bank?", icon: Building2 },
  { label: "Music", question: "Is music permissible in Islam?", icon: Music2 },
  { label: "Fasting", question: "What breaks the fast during Ramadan?", icon: UtensilsCrossed },
  { label: "Combining prayers", question: "What is the ruling on combining prayers while travelling?", icon: Plane },
  { label: "Pets", question: "Is it permissible to have a dog as a pet?", icon: Dog },
  { label: "Birthdays", question: "What is the ruling on celebrating birthdays?", icon: Cake },
]

const SETS = [[0, 1, 2], [3, 4, 5], [6, 7, 8]]

export function useRotatingQuestions(intervalMs = 4000) {
  const [setIndex, setSetIndex] = useState(0)
  const [visible, setVisible] = useState(true)

  useEffect(() => {
    const id = setInterval(() => {
      setVisible(false)
      setTimeout(() => {
        setSetIndex((prev) => (prev + 1) % SETS.length)
        setVisible(true)
      }, 400)
    }, intervalMs)
    return () => clearInterval(id)
  }, [intervalMs])

  const questions = SETS[setIndex].map((i) => EXAMPLE_QUESTIONS[i])
  return { questions, visible }
}
