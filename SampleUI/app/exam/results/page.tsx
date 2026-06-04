"use client"

import { useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ScrollArea } from "@/components/ui/scroll-area"
import { 
  GraduationCap, 
  CheckCircle2, 
  XCircle, 
  MinusCircle,
  Trophy,
  BarChart3,
  FileText,
  Home,
  Download,
  ChevronDown,
  ChevronUp
} from "lucide-react"

// Mock score data
const mockScoreData = {
  sessionId: "sess-123",
  score: 42,
  maxScore: 50,
  correctCount: 42,
  incorrectCount: 6,
  unattemptedCount: 2,
  submittedAt: "2026-06-03T11:30:00Z",
  duration: "1h 23m",
}

// Mock review data
const mockReviewData = Array.from({ length: 50 }, (_, i) => {
  const isCorrect = i < 42
  const isUnattempted = i >= 48
  return {
    position: i + 1,
    questionText: `Question ${i + 1}: ${getQuestionText(i)}`,
    options: [
      { key: "A", text: getOptionText(i, 0) },
      { key: "B", text: getOptionText(i, 1) },
      { key: "C", text: getOptionText(i, 2) },
      { key: "D", text: getOptionText(i, 3) },
    ],
    selectedOption: isUnattempted ? null : (isCorrect ? "A" : "B") as "A" | "B" | "C" | "D" | null,
    correctOption: "A" as "A" | "B" | "C" | "D",
    isCorrect: isUnattempted ? null : isCorrect,
  }
})

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

export default function ResultsPage() {
  const [activeTab, setActiveTab] = useState("summary")
  const [expandedQuestions, setExpandedQuestions] = useState<Set<number>>(new Set())

  const scorePercentage = (mockScoreData.score / mockScoreData.maxScore) * 100
  
  // Determine performance level
  const getPerformanceLevel = () => {
    if (scorePercentage >= 90) return { label: "Excellent", color: "text-accent" }
    if (scorePercentage >= 75) return { label: "Good", color: "text-primary" }
    if (scorePercentage >= 50) return { label: "Satisfactory", color: "text-warning" }
    return { label: "Needs Improvement", color: "text-destructive" }
  }

  const performance = getPerformanceLevel()

  const toggleQuestion = (position: number) => {
    setExpandedQuestions(prev => {
      const newSet = new Set(prev)
      if (newSet.has(position)) {
        newSet.delete(position)
      } else {
        newSet.add(position)
      }
      return newSet
    })
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
              <GraduationCap className="h-6 w-6 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-foreground">Test Results</h1>
              <p className="text-xs text-muted-foreground">
                Submitted {new Date(mockScoreData.submittedAt).toLocaleDateString()}
              </p>
            </div>
          </div>

          <Link href="/">
            <Button variant="outline">
              <Home className="mr-2 h-4 w-4" />
              Back to Home
            </Button>
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Score Hero Card */}
        <Card className="mb-8 overflow-hidden">
          <div className="bg-gradient-to-r from-primary/10 to-accent/10 p-8">
            <div className="flex flex-col items-center justify-center text-center">
              <div className="mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-card shadow-lg">
                <Trophy className={`h-10 w-10 ${performance.color}`} />
              </div>
              
              <h2 className="text-4xl font-bold text-foreground sm:text-5xl">
                {mockScoreData.score} / {mockScoreData.maxScore}
              </h2>
              
              <p className={`mt-2 text-lg font-medium ${performance.color}`}>
                {performance.label}
              </p>
              
              <div className="mt-6 w-full max-w-md">
                <Progress value={scorePercentage} className="h-3" />
                <p className="mt-2 text-sm text-muted-foreground">
                  {scorePercentage.toFixed(0)}% Score
                </p>
              </div>
            </div>
          </div>
        </Card>

        {/* Stats Grid */}
        <div className="mb-8 grid gap-4 sm:grid-cols-3">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Correct Answers
              </CardTitle>
              <CheckCircle2 className="h-5 w-5 text-accent" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-accent">
                {mockScoreData.correctCount}
              </div>
              <Progress 
                value={(mockScoreData.correctCount / mockScoreData.maxScore) * 100} 
                className="mt-2 h-2 bg-accent/20 [&>div]:bg-accent"
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Incorrect Answers
              </CardTitle>
              <XCircle className="h-5 w-5 text-destructive" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-destructive">
                {mockScoreData.incorrectCount}
              </div>
              <Progress 
                value={(mockScoreData.incorrectCount / mockScoreData.maxScore) * 100} 
                className="mt-2 h-2 bg-destructive/20 [&>div]:bg-destructive"
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Unattempted
              </CardTitle>
              <MinusCircle className="h-5 w-5 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-muted-foreground">
                {mockScoreData.unattemptedCount}
              </div>
              <Progress 
                value={(mockScoreData.unattemptedCount / mockScoreData.maxScore) * 100} 
                className="mt-2 h-2 bg-muted [&>div]:bg-muted-foreground"
              />
            </CardContent>
          </Card>
        </div>

        {/* Tabs for Summary and Review */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <div className="mb-6 flex items-center justify-between">
            <TabsList>
              <TabsTrigger value="summary" className="gap-2">
                <BarChart3 className="h-4 w-4" />
                Summary
              </TabsTrigger>
              <TabsTrigger value="review" className="gap-2">
                <FileText className="h-4 w-4" />
                Review Answers
              </TabsTrigger>
            </TabsList>

            <Button variant="outline" size="sm">
              <Download className="mr-2 h-4 w-4" />
              Export Report
            </Button>
          </div>

          <TabsContent value="summary">
            <Card>
              <CardHeader>
                <CardTitle>Performance Summary</CardTitle>
                <CardDescription>
                  Overview of your test performance
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Visual breakdown */}
                <div className="flex items-center gap-4">
                  <div className="flex h-32 w-32 items-center justify-center">
                    <div className="relative">
                      <svg className="h-32 w-32 -rotate-90 transform">
                        <circle
                          cx="64"
                          cy="64"
                          r="56"
                          stroke="currentColor"
                          strokeWidth="12"
                          fill="none"
                          className="text-muted"
                        />
                        <circle
                          cx="64"
                          cy="64"
                          r="56"
                          stroke="currentColor"
                          strokeWidth="12"
                          fill="none"
                          strokeDasharray={`${(mockScoreData.correctCount / mockScoreData.maxScore) * 351.86} 351.86`}
                          className="text-accent"
                        />
                      </svg>
                      <div className="absolute inset-0 flex items-center justify-center">
                        <span className="text-2xl font-bold text-foreground">
                          {scorePercentage.toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex-1 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="h-3 w-3 rounded-full bg-accent" />
                        <span className="text-sm text-foreground">Correct</span>
                      </div>
                      <span className="font-medium text-foreground">{mockScoreData.correctCount}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="h-3 w-3 rounded-full bg-destructive" />
                        <span className="text-sm text-foreground">Incorrect</span>
                      </div>
                      <span className="font-medium text-foreground">{mockScoreData.incorrectCount}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="h-3 w-3 rounded-full bg-muted-foreground" />
                        <span className="text-sm text-foreground">Skipped</span>
                      </div>
                      <span className="font-medium text-foreground">{mockScoreData.unattemptedCount}</span>
                    </div>
                  </div>
                </div>

                {/* Additional stats */}
                <div className="grid gap-4 border-t border-border pt-6 sm:grid-cols-2">
                  <div className="rounded-lg bg-secondary/50 p-4">
                    <p className="text-sm text-muted-foreground">Test Duration</p>
                    <p className="text-lg font-semibold text-foreground">{mockScoreData.duration}</p>
                  </div>
                  <div className="rounded-lg bg-secondary/50 p-4">
                    <p className="text-sm text-muted-foreground">Submission Time</p>
                    <p className="text-lg font-semibold text-foreground">
                      {new Date(mockScoreData.submittedAt).toLocaleString()}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="review">
            <Card>
              <CardHeader>
                <CardTitle>Answer Review</CardTitle>
                <CardDescription>
                  Review all your answers with correct solutions
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[600px] pr-4">
                  <div className="space-y-4">
                    {mockReviewData.map((item) => (
                      <div 
                        key={item.position}
                        className="rounded-lg border border-border"
                      >
                        <button
                          onClick={() => toggleQuestion(item.position)}
                          className="flex w-full items-center justify-between p-4 text-left hover:bg-secondary/50"
                          aria-expanded={expandedQuestions.has(item.position)}
                        >
                          <div className="flex items-center gap-3">
                            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-secondary text-sm font-medium text-secondary-foreground">
                              {item.position}
                            </span>
                            <div className="flex items-center gap-2">
                              {item.isCorrect === true && (
                                <Badge variant="outline" className="border-accent bg-accent/10 text-accent">
                                  <CheckCircle2 className="mr-1 h-3 w-3" />
                                  Correct
                                </Badge>
                              )}
                              {item.isCorrect === false && (
                                <Badge variant="outline" className="border-destructive bg-destructive/10 text-destructive">
                                  <XCircle className="mr-1 h-3 w-3" />
                                  Incorrect
                                </Badge>
                              )}
                              {item.isCorrect === null && (
                                <Badge variant="outline" className="text-muted-foreground">
                                  <MinusCircle className="mr-1 h-3 w-3" />
                                  Skipped
                                </Badge>
                              )}
                            </div>
                          </div>
                          {expandedQuestions.has(item.position) ? (
                            <ChevronUp className="h-5 w-5 text-muted-foreground" />
                          ) : (
                            <ChevronDown className="h-5 w-5 text-muted-foreground" />
                          )}
                        </button>

                        {expandedQuestions.has(item.position) && (
                          <div className="border-t border-border p-4">
                            <p className="mb-4 font-medium text-foreground">
                              {item.questionText}
                            </p>
                            <div className="space-y-2">
                              {item.options.map((option) => {
                                const isSelected = item.selectedOption === option.key
                                const isCorrect = item.correctOption === option.key
                                
                                return (
                                  <div
                                    key={option.key}
                                    className={`flex items-center gap-3 rounded-lg border-2 p-3 ${
                                      isCorrect
                                        ? "border-accent bg-accent/10"
                                        : isSelected && !isCorrect
                                          ? "border-destructive bg-destructive/10"
                                          : "border-border"
                                    }`}
                                  >
                                    <span className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-semibold ${
                                      isCorrect
                                        ? "bg-accent text-accent-foreground"
                                        : isSelected
                                          ? "bg-destructive text-destructive-foreground"
                                          : "bg-secondary text-secondary-foreground"
                                    }`}>
                                      {option.key}
                                    </span>
                                    <span className="flex-1 text-foreground">{option.text}</span>
                                    {isCorrect && (
                                      <CheckCircle2 className="h-5 w-5 text-accent" />
                                    )}
                                    {isSelected && !isCorrect && (
                                      <XCircle className="h-5 w-5 text-destructive" />
                                    )}
                                  </div>
                                )
                              })}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}
