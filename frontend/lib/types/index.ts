/** API types aligned with backend Pydantic schemas (PRD §9.6). */

export type UserRole = "EXAMINEE" | "EXAMINER";
export type SessionStatus = "ACTIVE" | "COMPLETED" | "EXPIRED";
export type CorrectOption = "A" | "B" | "C" | "D";
export type SelectedOption = CorrectOption;
export type SelectionMode = "FIXED_ORDER" | "RANDOM_SAMPLE";

export type ResponseMeta = {
  request_id: string;
  next_cursor?: string | null;
};

export type SuccessEnvelope<T> = {
  data: T;
  meta: ResponseMeta;
};

export type CsrfTokenData = {
  csrf_token: string;
};

export type ExaminerLoginData = {
  user_id: string;
  username: string;
  must_change_password: boolean;
};

export type ExamineeSessionResource = {
  session_id: string;
  status: SessionStatus;
  total_questions: number;
  answered_count: number;
  current_position: number;
  started_at: string;
  expires_at: string;
};

export type CurrentUserData = {
  user_id: string;
  role: UserRole;
  csrf_token: string;
  prn?: string | null;
  name?: string | null;
  username?: string | null;
  is_admin?: boolean;
};

export type QuestionOption = {
  key: CorrectOption;
  text: string;
};

export type ExamineeQuestionAtPosition = {
  position: number;
  total: number;
  question: {
    question_id: string;
    question_text: string;
    options: QuestionOption[];
  };
  selected_option: SelectedOption | null;
  answered_count: number;
};

export type SaveResponseResult = {
  question_id: string;
  selected_option: SelectedOption | null;
  updated_at: string;
  answered_count: number;
};

export type SubmitSessionResult = {
  session_id: string;
  status: SessionStatus;
  score: number;
  max_score: number;
  correct_count: number;
  incorrect_count: number;
  unattempted_count: number;
  submitted_at: string;
};

export type ReviewItem = {
  position: number;
  question_text: string;
  options: QuestionOption[];
  selected_option: SelectedOption | null;
  correct_option: CorrectOption;
  is_correct: boolean | null;
};

export type ReviewResult = {
  items: ReviewItem[];
};

export type QuestionOut = {
  question_id: string;
  question_text: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  correct_option: CorrectOption;
  question_version: number;
  is_deleted: boolean;
  updated_at: string;
};

export type QuestionListData = {
  items: QuestionOut[];
  next_cursor: string | null;
  active_count: number;
};

export type SessionSummaryOut = {
  session_id: string;
  status: SessionStatus;
  score: number | null;
  submitted_at: string | null;
  prn: string | null;
  name: string | null;
};

export type SessionListData = {
  items: SessionSummaryOut[];
  next_cursor: string | null;
};

export type SessionQuestionResultOut = {
  question_id: string;
  position: number;
  question_text: string;
  selected_option: SelectedOption | null;
  correct_option: CorrectOption;
  is_correct: boolean | null;
};

export type SessionDetailOut = {
  session_id: string;
  user_id: string;
  status: SessionStatus;
  score: number | null;
  started_at: string;
  submitted_at: string | null;
  selection_mode: SelectionMode;
  prn: string | null;
  name: string | null;
  responses: SessionQuestionResultOut[];
};

export type PlatformSettingsOut = {
  retention_days_completed: number;
  allow_examinee_retake: boolean;
  question_selection_mode: SelectionMode;
};

export type ExaminerUserOut = {
  user_id: string;
  username: string;
  is_active: boolean;
  force_password_change: boolean;
  created_at: string;
};

export type EraseExamineeData = {
  user_id: string;
  job_id: string;
  status: string;
};
