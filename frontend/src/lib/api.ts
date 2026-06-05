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

// ---- Video API ----

export interface VideoJob {
  job_id: string;
  status: "processing" | "done" | "error";
  progress: number;
  message: string;
  title?: string;
  subtitle?: string;
  scenes?: number;
  duration?: number;
  video_url?: string;
  error?: string;
}

export async function startVideoGeneration(prompt: string): Promise<{ job_id: string }> {
  const res = await fetch(`${API_URL}/api/video/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
  if (!res.ok) throw new Error("Failed to start video generation");
  return res.json();
}

export async function getVideoJob(jobId: string): Promise<VideoJob> {
  const res = await fetch(`${API_URL}/api/video/jobs/${jobId}`);
  if (!res.ok) throw new Error("Failed to fetch job status");
  return res.json();
}

export function getVideoStreamUrl(jobId: string): string {
  return `${API_URL}/api/video/stream/${jobId}`;
}
