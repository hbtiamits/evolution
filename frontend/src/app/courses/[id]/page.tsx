import { getCourse, formatDomain, formatDate } from "@/lib/api";
import Link from "next/link";
import { notFound } from "next/navigation";

export default async function CoursePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  let course;
  try {
    course = await getCourse(id);
  } catch {
    notFound();
  }

  const sortedModules = [...(course.modules ?? [])].sort((a, b) => a.order - b.order);

  return (
    <div className="max-w-3xl">
      {/* Back */}
      <Link href="/" className="text-sm text-white/40 hover:text-white transition-colors mb-8 inline-block">
        ← Back to courses
      </Link>

      {/* Header */}
      <div className="mb-10">
        <div className="flex items-center gap-3 mb-4">
          <span className="text-xs font-medium px-2 py-1 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
            {formatDomain(course.domain)}
          </span>
          <span className="text-xs text-white/30">{formatDate(course.created_at)}</span>
        </div>
        <h1 className="text-3xl font-bold text-white mb-4 leading-tight">{course.title}</h1>
        <p className="text-white/60 text-lg leading-relaxed">{course.summary}</p>
        {course.source_url && (
          <a
            href={course.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block mt-4 text-sm text-indigo-400 hover:text-indigo-300 transition-colors"
          >
            Source: {course.source_title || course.source_url} ↗
          </a>
        )}
      </div>

      {/* Modules */}
      <div className="space-y-8">
        {sortedModules.map((module, index) => (
          <div key={module.order} className="border border-white/10 rounded-xl p-6">
            <div className="flex items-center gap-3 mb-4">
              <span className="w-7 h-7 rounded-full bg-indigo-600 text-white text-xs font-bold flex items-center justify-center flex-shrink-0">
                {index + 1}
              </span>
              <h2 className="text-xl font-semibold text-white">{module.title}</h2>
            </div>

            <div className="text-white/70 leading-relaxed whitespace-pre-wrap mb-5">
              {module.content}
            </div>

            {module.key_takeaways?.length > 0 && (
              <div className="bg-white/5 rounded-lg p-4">
                <p className="text-xs font-semibold text-white/40 uppercase tracking-wider mb-3">
                  Key Takeaways
                </p>
                <ul className="space-y-2">
                  {module.key_takeaways.map((point, i) => (
                    <li key={i} className="flex gap-2 text-sm text-white/70">
                      <span className="text-indigo-400 mt-0.5 flex-shrink-0">✓</span>
                      {point}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
