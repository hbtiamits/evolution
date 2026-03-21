const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Module {
  order: number;
  title: string;
  content: string;
  key_takeaways: string[];
}

export interface Course {
  id: string;
  title: string;
  domain: string;
  summary: string;
  source_url: string | null;
  source_title: string | null;
  created_at: string;
  modules?: Module[];
}

export async function getCourses(domain?: string, limit = 20, offset = 0): Promise<Course[]> {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (domain) params.set("domain", domain);
  const res = await fetch(`${API_URL}/api/courses?${params}`, { next: { revalidate: 60 } });
  if (!res.ok) throw new Error("Failed to fetch courses");
  return res.json();
}

export async function getCourse(id: string): Promise<Course> {
  const res = await fetch(`${API_URL}/api/courses/${id}`, { next: { revalidate: 60 } });
  if (!res.ok) throw new Error("Course not found");
  return res.json();
}

export async function getDomains(): Promise<string[]> {
  const res = await fetch(`${API_URL}/api/courses/domains`, { next: { revalidate: 300 } });
  if (!res.ok) throw new Error("Failed to fetch domains");
  return res.json();
}

// --- Quiz types ---

export interface QuizQuestion {
  id: number;
  question: string;
  options: string[];
}

export interface QuizData {
  quiz_id: string;
  course_id: string;
  questions: QuizQuestion[];
}

export interface AnswerResult {
  question_id: number;
  question: string;
  selected_index: number;
  correct_index: number;
  is_correct: boolean;
  explanation: string;
}

export interface SubmitResult {
  score: number;
  total: number;
  percentage: number;
  results: AnswerResult[];
}

export async function getQuiz(courseId: string): Promise<QuizData | null> {
  const res = await fetch(`${API_URL}/api/courses/${courseId}/quiz`, { cache: "no-store" });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error("Failed to fetch quiz");
  return res.json();
}

export async function generateQuiz(courseId: string): Promise<QuizData> {
  const res = await fetch(`${API_URL}/api/courses/${courseId}/quiz/generate`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to generate quiz");
  return res.json();
}

export async function submitQuiz(courseId: string, answers: number[]): Promise<SubmitResult> {
  const res = await fetch(`${API_URL}/api/courses/${courseId}/quiz/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answers }),
  });
  if (!res.ok) throw new Error("Failed to submit quiz");
  return res.json();
}

export function formatDomain(domain: string): string {
  return domain.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}
