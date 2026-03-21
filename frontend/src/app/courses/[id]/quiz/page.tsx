import { getCourse, getQuiz } from "@/lib/api";
import QuizClient from "@/components/QuizClient";
import Link from "next/link";
import { notFound } from "next/navigation";

export default async function QuizPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  let course;
  try {
    course = await getCourse(id);
  } catch {
    notFound();
  }

  // Pre-fetch existing quiz (null if not generated yet)
  const quiz = await getQuiz(id);

  return (
    <div>
      <div className="mb-8">
        <Link
          href={`/courses/${id}`}
          className="text-sm text-white/40 hover:text-white transition-colors"
        >
          ← Back to course
        </Link>
      </div>
      <QuizClient courseId={id} courseTitle={course.title} initialQuiz={quiz} />
    </div>
  );
}
