"use client"

import { useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { 
  Shield, 
  Plus, 
  Pencil, 
  Trash2, 
  Users, 
  ClipboardList, 
  BarChart3,
  Download,
  Search,
  MoreHorizontal,
  LogOut,
  Eye,
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle
} from "lucide-react"

// Mock data for questions
const mockQuestions = [
  {
    id: "q-1",
    questionText: "What is the capital of France?",
    optionA: "Paris",
    optionB: "London",
    optionC: "Berlin",
    optionD: "Madrid",
    correctOption: "A" as const,
    version: 1,
    createdAt: "2026-06-01T10:00:00Z",
    isDeleted: false,
  },
  {
    id: "q-2",
    questionText: "Which planet is known as the Red Planet?",
    optionA: "Mars",
    optionB: "Venus",
    optionC: "Jupiter",
    optionD: "Saturn",
    correctOption: "A" as const,
    version: 2,
    createdAt: "2026-06-01T10:05:00Z",
    isDeleted: false,
  },
  {
    id: "q-3",
    questionText: "What is the largest mammal in the world?",
    optionA: "Blue Whale",
    optionB: "Elephant",
    optionC: "Giraffe",
    optionD: "Hippopotamus",
    correctOption: "A" as const,
    version: 1,
    createdAt: "2026-06-01T10:10:00Z",
    isDeleted: false,
  },
]

// Mock data for examinee results
const mockResults = [
  {
    sessionId: "sess-1",
    prn: "STU2024001",
    name: "John Doe",
    score: 42,
    correctCount: 42,
    incorrectCount: 6,
    unattemptedCount: 2,
    status: "COMPLETED" as const,
    submittedAt: "2026-06-03T11:30:00Z",
  },
  {
    sessionId: "sess-2",
    prn: "STU2024002",
    name: "Jane Smith",
    score: 48,
    correctCount: 48,
    incorrectCount: 2,
    unattemptedCount: 0,
    status: "COMPLETED" as const,
    submittedAt: "2026-06-03T10:45:00Z",
  },
  {
    sessionId: "sess-3",
    prn: "STU2024003",
    name: "Alice Johnson",
    score: 35,
    correctCount: 35,
    incorrectCount: 10,
    unattemptedCount: 5,
    status: "COMPLETED" as const,
    submittedAt: "2026-06-03T12:00:00Z",
  },
  {
    sessionId: "sess-4",
    prn: "STU2024004",
    name: "Bob Wilson",
    score: null,
    correctCount: null,
    incorrectCount: null,
    unattemptedCount: null,
    status: "ACTIVE" as const,
    submittedAt: null,
  },
]

type Question = typeof mockQuestions[0]
type Result = typeof mockResults[0]

export default function ExaminerDashboard() {
  const [activeTab, setActiveTab] = useState("questions")
  const [questions, setQuestions] = useState(mockQuestions)
  const [results] = useState(mockResults)
  const [searchQuery, setSearchQuery] = useState("")
  const [isAddingQuestion, setIsAddingQuestion] = useState(false)
  const [editingQuestion, setEditingQuestion] = useState<Question | null>(null)

  // Question form state
  const [formData, setFormData] = useState({
    questionText: "",
    optionA: "",
    optionB: "",
    optionC: "",
    optionD: "",
    correctOption: "" as "A" | "B" | "C" | "D" | "",
  })

  const resetForm = () => {
    setFormData({
      questionText: "",
      optionA: "",
      optionB: "",
      optionC: "",
      optionD: "",
      correctOption: "",
    })
  }

  const handleAddQuestion = () => {
    if (!formData.questionText || !formData.optionA || !formData.optionB || 
        !formData.optionC || !formData.optionD || !formData.correctOption) {
      return
    }

    const newQuestion: Question = {
      id: `q-${Date.now()}`,
      questionText: formData.questionText,
      optionA: formData.optionA,
      optionB: formData.optionB,
      optionC: formData.optionC,
      optionD: formData.optionD,
      correctOption: formData.correctOption as "A" | "B" | "C" | "D",
      version: 1,
      createdAt: new Date().toISOString(),
      isDeleted: false,
    }

    setQuestions([...questions, newQuestion])
    resetForm()
    setIsAddingQuestion(false)
  }

  const handleEditQuestion = () => {
    if (!editingQuestion || !formData.questionText || !formData.optionA || 
        !formData.optionB || !formData.optionC || !formData.optionD || !formData.correctOption) {
      return
    }

    setQuestions(questions.map(q => 
      q.id === editingQuestion.id 
        ? {
            ...q,
            questionText: formData.questionText,
            optionA: formData.optionA,
            optionB: formData.optionB,
            optionC: formData.optionC,
            optionD: formData.optionD,
            correctOption: formData.correctOption as "A" | "B" | "C" | "D",
            version: q.version + 1,
          }
        : q
    ))
    resetForm()
    setEditingQuestion(null)
  }

  const handleDeleteQuestion = (questionId: string) => {
    setQuestions(questions.map(q => 
      q.id === questionId ? { ...q, isDeleted: true } : q
    ))
  }

  const openEditDialog = (question: Question) => {
    setFormData({
      questionText: question.questionText,
      optionA: question.optionA,
      optionB: question.optionB,
      optionC: question.optionC,
      optionD: question.optionD,
      correctOption: question.correctOption,
    })
    setEditingQuestion(question)
  }

  const filteredQuestions = questions.filter(q => 
    !q.isDeleted && 
    q.questionText.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const filteredResults = results.filter(r => 
    r.prn.toLowerCase().includes(searchQuery.toLowerCase()) ||
    r.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const activeQuestionCount = questions.filter(q => !q.isDeleted).length

  // Stats
  const completedTests = results.filter(r => r.status === "COMPLETED").length
  const activeTests = results.filter(r => r.status === "ACTIVE").length
  const averageScore = results
    .filter(r => r.score !== null)
    .reduce((acc, r) => acc + (r.score || 0), 0) / completedTests || 0

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-10 border-b border-border bg-card shadow-sm">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
              <Shield className="h-6 w-6 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-foreground">Examiner Dashboard</h1>
              <p className="text-xs text-muted-foreground">Question Bank & Results Management</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <Badge variant="outline" className="hidden sm:flex">
              <Clock className="mr-1 h-3 w-3" />
              Session Active
            </Badge>
            <Link href="/">
              <Button variant="ghost" size="sm">
                <LogOut className="mr-2 h-4 w-4" />
                Logout
              </Button>
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        {/* Stats Cards */}
        <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Total Questions
              </CardTitle>
              <ClipboardList className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">{activeQuestionCount}</div>
              {activeQuestionCount < 50 && (
                <p className="mt-1 flex items-center text-xs text-warning">
                  <AlertTriangle className="mr-1 h-3 w-3" />
                  Need {50 - activeQuestionCount} more for tests
                </p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Completed Tests
              </CardTitle>
              <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">{completedTests}</div>
              <p className="mt-1 text-xs text-muted-foreground">
                {activeTests} currently active
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Average Score
              </CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">
                {averageScore.toFixed(1)} / 50
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                {((averageScore / 50) * 100).toFixed(0)}% average
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Total Examinees
              </CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">{results.length}</div>
              <p className="mt-1 text-xs text-muted-foreground">
                Registered users
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Main Content Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <TabsList>
              <TabsTrigger value="questions" className="gap-2">
                <ClipboardList className="h-4 w-4" />
                Question Bank
              </TabsTrigger>
              <TabsTrigger value="results" className="gap-2">
                <Users className="h-4 w-4" />
                Results
              </TabsTrigger>
            </TabsList>

            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder={activeTab === "questions" ? "Search questions..." : "Search by PRN or name..."}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-64 pl-9"
                />
              </div>

              {activeTab === "questions" && (
                <Dialog open={isAddingQuestion} onOpenChange={setIsAddingQuestion}>
                  <DialogTrigger asChild>
                    <Button onClick={() => { resetForm(); setIsAddingQuestion(true); }}>
                      <Plus className="mr-2 h-4 w-4" />
                      Add Question
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="max-w-2xl">
                    <DialogHeader>
                      <DialogTitle>Add New Question</DialogTitle>
                      <DialogDescription>
                        Create a new multiple choice question for the question bank.
                      </DialogDescription>
                    </DialogHeader>
                    <QuestionForm 
                      formData={formData} 
                      setFormData={setFormData} 
                      onSubmit={handleAddQuestion}
                      submitLabel="Add Question"
                    />
                  </DialogContent>
                </Dialog>
              )}

              {activeTab === "results" && (
                <Button variant="outline">
                  <Download className="mr-2 h-4 w-4" />
                  Export CSV
                </Button>
              )}
            </div>
          </div>

          {/* Questions Tab */}
          <TabsContent value="questions">
            <Card>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">#</TableHead>
                    <TableHead>Question</TableHead>
                    <TableHead className="w-24">Options</TableHead>
                    <TableHead className="w-20">Answer</TableHead>
                    <TableHead className="w-16">Ver.</TableHead>
                    <TableHead className="w-20 text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredQuestions.map((question, index) => (
                    <TableRow key={question.id}>
                      <TableCell className="font-medium">{index + 1}</TableCell>
                      <TableCell>
                        <div className="max-w-md truncate">{question.questionText}</div>
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          {["A", "B", "C", "D"].map((opt) => (
                            <Badge 
                              key={opt} 
                              variant={question.correctOption === opt ? "default" : "outline"}
                              className="h-5 w-5 justify-center p-0 text-xs"
                            >
                              {opt}
                            </Badge>
                          ))}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="default" className="bg-accent text-accent-foreground">
                          {question.correctOption}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        v{question.version}
                      </TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-8 w-8">
                              <MoreHorizontal className="h-4 w-4" />
                              <span className="sr-only">Actions</span>
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => openEditDialog(question)}>
                              <Pencil className="mr-2 h-4 w-4" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <AlertDialog>
                              <AlertDialogTrigger asChild>
                                <DropdownMenuItem 
                                  onSelect={(e) => e.preventDefault()}
                                  className="text-destructive focus:text-destructive"
                                >
                                  <Trash2 className="mr-2 h-4 w-4" />
                                  Delete
                                </DropdownMenuItem>
                              </AlertDialogTrigger>
                              <AlertDialogContent>
                                <AlertDialogHeader>
                                  <AlertDialogTitle>Delete Question?</AlertDialogTitle>
                                  <AlertDialogDescription>
                                    This will remove the question from the active question bank.
                                    {activeQuestionCount <= 50 && (
                                      <span className="mt-2 block text-warning">
                                        <AlertTriangle className="mr-1 inline h-4 w-4" />
                                        Warning: This will bring your question count below 50.
                                      </span>
                                    )}
                                  </AlertDialogDescription>
                                </AlertDialogHeader>
                                <AlertDialogFooter>
                                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                                  <AlertDialogAction 
                                    onClick={() => handleDeleteQuestion(question.id)}
                                    className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                                  >
                                    Delete
                                  </AlertDialogAction>
                                </AlertDialogFooter>
                              </AlertDialogContent>
                            </AlertDialog>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                  {filteredQuestions.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={6} className="h-32 text-center text-muted-foreground">
                        {searchQuery ? "No questions match your search." : "No questions in the bank. Add your first question to get started."}
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </Card>
          </TabsContent>

          {/* Results Tab */}
          <TabsContent value="results">
            <Card>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>PRN</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead className="w-20">Score</TableHead>
                    <TableHead className="w-24">Correct</TableHead>
                    <TableHead className="w-24">Incorrect</TableHead>
                    <TableHead className="w-24">Skipped</TableHead>
                    <TableHead className="w-24">Status</TableHead>
                    <TableHead className="w-40">Submitted</TableHead>
                    <TableHead className="w-20 text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredResults.map((result) => (
                    <TableRow key={result.sessionId}>
                      <TableCell className="font-mono text-sm">{result.prn}</TableCell>
                      <TableCell>{result.name}</TableCell>
                      <TableCell>
                        {result.score !== null ? (
                          <span className="font-semibold">{result.score}/50</span>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {result.correctCount !== null ? (
                          <span className="flex items-center gap-1 text-accent">
                            <CheckCircle2 className="h-3 w-3" />
                            {result.correctCount}
                          </span>
                        ) : "-"}
                      </TableCell>
                      <TableCell>
                        {result.incorrectCount !== null ? (
                          <span className="flex items-center gap-1 text-destructive">
                            <XCircle className="h-3 w-3" />
                            {result.incorrectCount}
                          </span>
                        ) : "-"}
                      </TableCell>
                      <TableCell>
                        {result.unattemptedCount !== null ? (
                          <span className="text-muted-foreground">{result.unattemptedCount}</span>
                        ) : "-"}
                      </TableCell>
                      <TableCell>
                        <Badge variant={result.status === "COMPLETED" ? "default" : "secondary"}>
                          {result.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {result.submittedAt 
                          ? new Date(result.submittedAt).toLocaleString()
                          : "-"
                        }
                      </TableCell>
                      <TableCell className="text-right">
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                          <Eye className="h-4 w-4" />
                          <span className="sr-only">View details</span>
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                  {filteredResults.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={9} className="h-32 text-center text-muted-foreground">
                        {searchQuery ? "No results match your search." : "No test results yet."}
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Edit Question Dialog */}
        <Dialog open={!!editingQuestion} onOpenChange={(open) => !open && setEditingQuestion(null)}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Edit Question</DialogTitle>
              <DialogDescription>
                Modify the question. This will create a new version.
              </DialogDescription>
            </DialogHeader>
            <QuestionForm 
              formData={formData} 
              setFormData={setFormData} 
              onSubmit={handleEditQuestion}
              submitLabel="Save Changes"
            />
          </DialogContent>
        </Dialog>
      </main>
    </div>
  )
}

// Question Form Component
function QuestionForm({
  formData,
  setFormData,
  onSubmit,
  submitLabel,
}: {
  formData: {
    questionText: string
    optionA: string
    optionB: string
    optionC: string
    optionD: string
    correctOption: string
  }
  setFormData: React.Dispatch<React.SetStateAction<typeof formData>>
  onSubmit: () => void
  submitLabel: string
}) {
  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="questionText">Question Text</Label>
        <Textarea
          id="questionText"
          placeholder="Enter your question here..."
          value={formData.questionText}
          onChange={(e) => setFormData({ ...formData, questionText: e.target.value })}
          maxLength={2000}
          rows={3}
        />
        <p className="text-xs text-muted-foreground">
          {formData.questionText.length}/2000 characters
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="optionA">Option A</Label>
          <Input
            id="optionA"
            placeholder="Enter option A"
            value={formData.optionA}
            onChange={(e) => setFormData({ ...formData, optionA: e.target.value })}
            maxLength={500}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="optionB">Option B</Label>
          <Input
            id="optionB"
            placeholder="Enter option B"
            value={formData.optionB}
            onChange={(e) => setFormData({ ...formData, optionB: e.target.value })}
            maxLength={500}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="optionC">Option C</Label>
          <Input
            id="optionC"
            placeholder="Enter option C"
            value={formData.optionC}
            onChange={(e) => setFormData({ ...formData, optionC: e.target.value })}
            maxLength={500}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="optionD">Option D</Label>
          <Input
            id="optionD"
            placeholder="Enter option D"
            value={formData.optionD}
            onChange={(e) => setFormData({ ...formData, optionD: e.target.value })}
            maxLength={500}
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="correctOption">Correct Answer</Label>
        <Select
          value={formData.correctOption}
          onValueChange={(value) => setFormData({ ...formData, correctOption: value })}
        >
          <SelectTrigger id="correctOption">
            <SelectValue placeholder="Select the correct answer" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="A">Option A</SelectItem>
            <SelectItem value="B">Option B</SelectItem>
            <SelectItem value="C">Option C</SelectItem>
            <SelectItem value="D">Option D</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <DialogFooter>
        <Button 
          onClick={onSubmit}
          disabled={!formData.questionText || !formData.optionA || !formData.optionB || 
                   !formData.optionC || !formData.optionD || !formData.correctOption}
        >
          {submitLabel}
        </Button>
      </DialogFooter>
    </div>
  )
}
