"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import { GraduationCap, Shield, ClipboardList, Users, ChevronRight, Eye, EyeOff } from "lucide-react"

export default function LandingPage() {
  const router = useRouter()
  const [selectedRole, setSelectedRole] = useState<"examinee" | "examiner" | null>(null)
  const [showPassword, setShowPassword] = useState(false)
  
  // Examinee form state
  const [prn, setPrn] = useState("")
  const [name, setName] = useState("")
  const [privacyAcknowledged, setPrivacyAcknowledged] = useState(false)
  
  // Examiner form state
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  
  // Error states
  const [error, setError] = useState("")

  const handleExamineeEntry = (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    
    // Validation
    if (!prn.match(/^[A-Za-z0-9]{1,20}$/)) {
      setError("PRN must be alphanumeric (max 20 characters)")
      return
    }
    if (!name.trim() || name.length > 100) {
      setError("Name is required (max 100 characters)")
      return
    }
    if (!privacyAcknowledged) {
      setError("Please acknowledge the privacy notice to continue")
      return
    }
    
    // In production, this would call POST /api/v1/auth/examinee/entry
    // For demo, navigate to the test interface
    router.push("/exam/test")
  }

  const handleExaminerLogin = (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    
    if (!username.trim()) {
      setError("Username is required")
      return
    }
    if (!password) {
      setError("Password is required")
      return
    }
    
    // In production, this would call POST /api/v1/auth/examiner/login
    // For demo, navigate to the examiner dashboard
    router.push("/examiner/dashboard")
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
              <h1 className="text-lg font-semibold text-foreground">MCQ Test Platform</h1>
              <p className="text-xs text-muted-foreground">Secure Examination System</p>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="text-center">
          <h2 className="text-balance text-3xl font-bold tracking-tight text-foreground sm:text-4xl lg:text-5xl">
            Online Examination Portal
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-pretty text-lg text-muted-foreground">
            A secure, accessible, and professional platform for conducting multiple-choice examinations.
            Select your role below to get started.
          </p>
        </div>

        {/* Features */}
        <div className="mt-12 grid gap-6 sm:grid-cols-3">
          <div className="flex items-start gap-4 rounded-lg border border-border bg-card p-6">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10">
              <Shield className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h3 className="font-semibold text-foreground">Secure</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                GDPR compliant with encrypted data storage and audit logging
              </p>
            </div>
          </div>
          <div className="flex items-start gap-4 rounded-lg border border-border bg-card p-6">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10">
              <ClipboardList className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h3 className="font-semibold text-foreground">50 Questions</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                Navigate freely between questions with auto-save
              </p>
            </div>
          </div>
          <div className="flex items-start gap-4 rounded-lg border border-border bg-card p-6">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10">
              <Users className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h3 className="font-semibold text-foreground">Accessible</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                WCAG 2.1 AA compliant for all users
              </p>
            </div>
          </div>
        </div>

        {/* Role Selection Cards */}
        <div className="mt-16">
          <h3 className="text-center text-lg font-medium text-foreground">
            Select your role to continue
          </h3>
          
          <div className="mt-8 grid gap-8 lg:grid-cols-2">
            {/* Examinee Card */}
            <Card 
              className={`cursor-pointer transition-all duration-200 ${
                selectedRole === "examinee" 
                  ? "ring-2 ring-primary shadow-lg" 
                  : "hover:border-primary/50 hover:shadow-md"
              }`}
              onClick={() => setSelectedRole("examinee")}
            >
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                    <GraduationCap className="h-6 w-6 text-primary" />
                  </div>
                  {selectedRole === "examinee" && (
                    <span className="rounded-full bg-primary px-3 py-1 text-xs font-medium text-primary-foreground">
                      Selected
                    </span>
                  )}
                </div>
                <CardTitle className="mt-4">Enter as Examinee</CardTitle>
                <CardDescription>
                  Register with your PRN and name to take the 50-question MCQ test
                </CardDescription>
              </CardHeader>
              
              {selectedRole === "examinee" && (
                <CardContent>
                  <form onSubmit={handleExamineeEntry} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="prn">Permanent Registration Number (PRN)</Label>
                      <Input
                        id="prn"
                        type="text"
                        placeholder="e.g., STU2024001"
                        value={prn}
                        onChange={(e) => setPrn(e.target.value)}
                        maxLength={20}
                        pattern="[A-Za-z0-9]+"
                        required
                        aria-describedby="prn-hint"
                      />
                      <p id="prn-hint" className="text-xs text-muted-foreground">
                        Alphanumeric, maximum 20 characters
                      </p>
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="name">Full Name</Label>
                      <Input
                        id="name"
                        type="text"
                        placeholder="Enter your full name"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        maxLength={100}
                        required
                      />
                    </div>
                    
                    {/* Privacy Notice */}
                    <div className="rounded-lg border border-border bg-muted/50 p-4">
                      <h4 className="text-sm font-medium text-foreground">Privacy Notice</h4>
                      <p className="mt-2 text-xs text-muted-foreground">
                        We collect your PRN and name to administer this examination and record your results. 
                        Your data is stored securely and retained according to institutional policy. 
                        You have the right to access, rectify, or request erasure of your data.
                      </p>
                      <div className="mt-4 flex items-start gap-2">
                        <Checkbox
                          id="privacy"
                          checked={privacyAcknowledged}
                          onCheckedChange={(checked) => setPrivacyAcknowledged(checked === true)}
                        />
                        <Label htmlFor="privacy" className="text-sm leading-tight">
                          I acknowledge that I have read and understood the privacy notice
                        </Label>
                      </div>
                    </div>
                    
                    {error && selectedRole === "examinee" && (
                      <p className="text-sm text-destructive" role="alert">{error}</p>
                    )}
                    
                    <Button type="submit" className="w-full">
                      Start Test
                      <ChevronRight className="ml-2 h-4 w-4" />
                    </Button>
                  </form>
                </CardContent>
              )}
            </Card>

            {/* Examiner Card */}
            <Card 
              className={`cursor-pointer transition-all duration-200 ${
                selectedRole === "examiner" 
                  ? "ring-2 ring-primary shadow-lg" 
                  : "hover:border-primary/50 hover:shadow-md"
              }`}
              onClick={() => setSelectedRole("examiner")}
            >
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-secondary">
                    <Shield className="h-6 w-6 text-secondary-foreground" />
                  </div>
                  {selectedRole === "examiner" && (
                    <span className="rounded-full bg-primary px-3 py-1 text-xs font-medium text-primary-foreground">
                      Selected
                    </span>
                  )}
                </div>
                <CardTitle className="mt-4">Login as Examiner</CardTitle>
                <CardDescription>
                  Access the admin portal to manage questions and view results
                </CardDescription>
              </CardHeader>
              
              {selectedRole === "examiner" && (
                <CardContent>
                  <form onSubmit={handleExaminerLogin} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="username">Username</Label>
                      <Input
                        id="username"
                        type="text"
                        placeholder="Enter your username"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        autoComplete="username"
                        required
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="password">Password</Label>
                      <div className="relative">
                        <Input
                          id="password"
                          type={showPassword ? "text" : "password"}
                          placeholder="Enter your password"
                          value={password}
                          onChange={(e) => setPassword(e.target.value)}
                          autoComplete="current-password"
                          required
                          className="pr-10"
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                          onClick={() => setShowPassword(!showPassword)}
                          aria-label={showPassword ? "Hide password" : "Show password"}
                        >
                          {showPassword ? (
                            <EyeOff className="h-4 w-4 text-muted-foreground" />
                          ) : (
                            <Eye className="h-4 w-4 text-muted-foreground" />
                          )}
                        </Button>
                      </div>
                    </div>
                    
                    {error && selectedRole === "examiner" && (
                      <p className="text-sm text-destructive" role="alert">{error}</p>
                    )}
                    
                    <Button type="submit" className="w-full">
                      Login
                      <ChevronRight className="ml-2 h-4 w-4" />
                    </Button>
                    
                    <p className="text-center text-xs text-muted-foreground">
                      Contact your administrator if you need access
                    </p>
                  </form>
                </CardContent>
              )}
            </Card>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border bg-card mt-16">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
            <p className="text-sm text-muted-foreground">
              MCQ Test Platform - Secure Examination System
            </p>
            <div className="flex gap-6 text-sm text-muted-foreground">
              <span>WCAG 2.1 AA Compliant</span>
              <span>GDPR Compliant</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
