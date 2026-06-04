"use client"

import { useState, useCallback, useEffect, useRef } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { 
  GraduationCap, 
  ChevronLeft, 
  ChevronRight, 
  Flag, 
  CheckCircle2,
  Circle,
  Clock
} from "lucide-react"

// Mock questions for demonstration
const mockQuestions = Array.from({ length: 50 }, (_, i) => ({
  id: `q-${i + 1}`,
  position: i + 1,
  questionText: `Question ${i + 1}: ${getQuestionText(i)}`,
  options: [
    { key: "A", text: getOptionText(i, 0) },
    { key: "B", text: getOptionText(i, 1) },
    { key: "C", text: getOptionText(i, 2) },
    { key: "D", text: getOptionText(i, 3) },
  ],
}))

function getQuestionText(index: number): string {
  const questions = [
    "What is the capital of France?",
    "Which planet is known as the Red Planet?",
    "What is the largest mammal in the world?",
    "Who wrote 'Romeo and Juliet'?",
    "What is the chemical symbol for gold?",
    "Which ocean is the largest?",
    "What year did World War II end?",
    "What is the smallest prime number?",
    "Which element has the atomic number 1?",
    "What is the speed of light in vacuum?",
  ]
  return questions[index % questions.length]
}

function getOptionText(qIndex: number, optIndex: number): string {
  const options = [
    ["Paris", "London", "Berlin", "Madrid"],
    ["Mars", "Venus", "Jupiter", "Saturn"],
    ["Blue Whale", "Elephant", "Giraffe", "Hippopotamus"],
    ["William Shakespeare", "Charles Dickens", "Jane Austen", "Mark Twain"],
    ["Au", "Ag", "Fe", "Cu"],
    ["Pacific Ocean", "Atlantic Ocean", "Indian Ocean", "Arctic Ocean"],
    ["1945", "1944", "1946", "1943"],
    ["2", "1", "3", "0"],
    ["Hydrogen", "Helium", "Oxygen", "Carbon"],
    ["299,792 km/s", "150,000 km/s", "500,000 km/s", "1,000,000 km/s"],
  ]
  return options[qIndex % options.length][optIndex]
}

type Answer = {
  questionId: string
  selectedOption: "A" | "B" | "C" | "D" | null
}

export default function TestInterface() {
  const router = useRouter()
  const [currentPosition, setCurrentPosition] = useState(1)
  const [answers, setAnswers] = useState<Map<string, Answer>>(() => {
    const initial = new Map<string, Answer>()
    mockQuestions.forEach((q) => {
      initial.set(q.id, { questionId: q.id, selectedOption: null })
    })
    return initial
  })
  const [showNavigator, setShowNavigator] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const questionHeadingRef = useRef<HTMLHeadingElement>(null)

  const currentQuestion = mockQuestions[currentPosition - 1]
  const currentAnswer = answers.get(currentQuestion.id)
  
  const answeredCount = Array.from(answers.values()).filter(
    (a) => a.selectedOption !== null
  ).length

  // Focus management for accessibility
  useEffect(() => {
    questionHeadingRef.current?.focus()
  }, [currentPosition])

  const handleAnswerSelect = useCallback((option: "A" | "B" | "C" | "D") => {
    setAnswers((prev) => {
      const newAnswers = new Map(prev)
      newAnswers.set(currentQuestion.id, {
        questionId: currentQuestion.id,
        selectedOption: option,
      })
      return newAnswers
    })
    // In production, this would auto-save to the server
  }, [currentQuestion.id])

  const handleNavigation = useCallback((direction: "prev" | "next") => {
    if (direction === "prev" && currentPosition > 1) {
      setCurrentPosition(currentPosition - 1)
    } else if (direction === "next" && currentPosition < 50) {
      setCurrentPosition(currentPosition + 1)
    }
  }, [currentPosition])

  const handleSubmit = useCallback(() => {
    setIsSubmitting(true)
    // In production, this would call POST /api/v1/examinee/sessions/{sessionId}/submit
    setTimeout(() => {
      router.push("/exam/results")
    }, 1000)
  }, [router])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === "ArrowLeft" && currentPosition > 1) {
      handleNavigation("prev")
    } else if (e.key === "ArrowRight" && currentPosition < 50) {
      handleNavigation("next")
    }
  }, [currentPosition, handleNavigation])

  return (
    <div className="min-h-screen bg-background" onKeyDown={handleKeyDown}>
      {/* Header */}
      <header className="sticky top-0 z-10 border-b border-border bg-card shadow-sm">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
              <GraduationCap className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="font-semibold text-foreground">MCQ Test</span>
          </div>

          <div className="flex items-center gap-4">
            {/* Progress indicator */}
            <div className="hidden items-center gap-2 sm:flex">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Session Active</span>
            </div>
            
            {/* Answered count */}
            <div className="flex items-center gap-2 rounded-full bg-secondary px-3 py-1">
              <CheckCircle2 className="h-4 w-4 text-primary" />
              <span className="text-sm font-medium text-foreground">
                {answeredCount} / 50
                <span className="sr-only"> questions answered</span>
              </span>
            </div>

            {/* End Test Button */}
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant="destructive" size="sm">
                  <Flag className="mr-2 h-4 w-4" />
                  End Test
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>End Test?</AlertDialogTitle>
                  <AlertDialogDescription>
                    You have answered <strong>{answeredCount} of 50</strong> questions.
                    {answeredCount < 50 && (
                      <span className="block mt-2 text-warning">
                        You still have {50 - answeredCount} unanswered questions.
                      </span>
                    )}
                    <span className="block mt-2">
                      Are you sure you want to submit your test? This action cannot be undone.
                    </span>
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Continue Test</AlertDialogCancel>
                  <AlertDialogAction
                    onClick={handleSubmit}
                    disabled={isSubmitting}
                    className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                  >
                    {isSubmitting ? "Submitting..." : "Submit Test"}
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        </div>

        {/* Progress bar */}
        <div className="mx-auto max-w-7xl px-4 pb-3 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <Progress value={(answeredCount / 50) * 100} className="h-2 flex-1" />
            <span className="text-xs text-muted-foreground whitespace-nowrap">
              {Math.round((answeredCount / 50) * 100)}% Complete
            </span>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-6 lg:flex-row">
          {/* Question Navigator Panel */}
          <aside className={`${showNavigator ? "block" : "hidden"} lg:block lg:w-64 shrink-0`}>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="font-semibold text-foreground">Questions</h2>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowNavigator(false)}
                    className="lg:hidden"
                    aria-label="Hide question navigator"
                  >
                    Hide
                  </Button>
                </div>
                
                <div 
                  className="grid grid-cols-5 gap-2"
                  role="navigation"
                  aria-label="Question navigator"
                >
                  {mockQuestions.map((q) => {
                    const answer = answers.get(q.id)
                    const isAnswered = answer?.selectedOption !== null
                    const isCurrent = q.position === currentPosition
                    
                    return (
                      <button
                        key={q.id}
                        onClick={() => setCurrentPosition(q.position)}
                        className={`
                          relative flex h-9 w-9 items-center justify-center rounded-md text-sm font-medium
                          transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring
                          ${isCurrent 
                            ? "bg-primary text-primary-foreground" 
                            : isAnswered 
                              ? "bg-accent/20 text-accent-foreground border border-accent" 
                              : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
                          }
                        `}
                        aria-label={`Question ${q.position}${isAnswered ? ", answered" : ", not answered"}${isCurrent ? ", current" : ""}`}
                        aria-current={isCurrent ? "true" : undefined}
                      >
                        {q.position}
                        {isAnswered && !isCurrent && (
                          <CheckCircle2 className="absolute -right-1 -top-1 h-3 w-3 text-accent" aria-hidden="true" />
                        )}
                      </button>
                    )
                  })}
                </div>

                {/* Legend */}
                <div className="mt-4 space-y-2 border-t border-border pt-4">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <div className="flex h-4 w-4 items-center justify-center rounded bg-primary">
                      <span className="text-[10px] text-primary-foreground">1</span>
                    </div>
                    <span>Current</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <div className="flex h-4 w-4 items-center justify-center rounded border border-accent bg-accent/20">
                      <CheckCircle2 className="h-2.5 w-2.5 text-accent" />
                    </div>
                    <span>Answered</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <div className="flex h-4 w-4 items-center justify-center rounded bg-secondary">
                      <Circle className="h-2 w-2 text-muted-foreground" />
                    </div>
                    <span>Not answered</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </aside>

          {/* Question Content */}
          <div className="flex-1">
            <Card>
              <CardContent className="p-6 sm:p-8">
                {/* Question Header */}
                <div className="mb-6">
                  <span className="text-sm font-medium text-primary">
                    Question {currentPosition} of 50
                  </span>
                  <h1 
                    ref={questionHeadingRef}
                    tabIndex={-1}
                    className="mt-2 text-xl font-semibold text-foreground sm:text-2xl outline-none"
                  >
                    {currentQuestion.questionText}
                  </h1>
                </div>

                {/* Answer Options */}
                <fieldset className="space-y-4">
                  <legend className="sr-only">
                    Select your answer for question {currentPosition}
                  </legend>
                  
                  <RadioGroup
                    value={currentAnswer?.selectedOption || ""}
                    onValueChange={(value) => handleAnswerSelect(value as "A" | "B" | "C" | "D")}
                    className="space-y-3"
                  >
                    {currentQuestion.options.map((option) => (
                      <div key={option.key}>
                        <Label
                          htmlFor={`option-${option.key}`}
                          className={`
                            flex cursor-pointer items-start gap-4 rounded-lg border-2 p-4
                            transition-colors hover:bg-secondary/50
                            ${currentAnswer?.selectedOption === option.key 
                              ? "border-primary bg-primary/5" 
                              : "border-border"
                            }
                          `}
                        >
                          <RadioGroupItem
                            value={option.key}
                            id={`option-${option.key}`}
                            className="mt-0.5"
                          />
                          <div className="flex-1">
                            <span className="mr-2 inline-flex h-6 w-6 items-center justify-center rounded-full bg-secondary text-xs font-semibold text-secondary-foreground">
                              {option.key}
                            </span>
                            <span className="text-foreground">{option.text}</span>
                          </div>
                        </Label>
                      </div>
                    ))}
                  </RadioGroup>
                </fieldset>

                {/* Navigation Buttons */}
                <div className="mt-8 flex items-center justify-between">
                  <Button
                    variant="outline"
                    onClick={() => handleNavigation("prev")}
                    aria-disabled={currentPosition === 1}
                    className={currentPosition === 1 ? "opacity-50" : ""}
                  >
                    <ChevronLeft className="mr-2 h-4 w-4" />
                    Previous
                  </Button>

                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setShowNavigator(!showNavigator)}
                      className="lg:hidden"
                    >
                      {showNavigator ? "Hide" : "Show"} Navigator
                    </Button>
                  </div>

                  <Button
                    onClick={() => handleNavigation("next")}
                    aria-disabled={currentPosition === 50}
                    className={currentPosition === 50 ? "opacity-50" : ""}
                  >
                    Next
                    <ChevronRight className="ml-2 h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  )
}
