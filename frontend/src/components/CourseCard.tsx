import Link from "next/link";
import { Course, formatDomain, formatDate } from "@/lib/api";

export default function CourseCard({ course }: { course: Course }) {
  return (
    <Link href={`/courses/${course.id}`}>
      <div className="group border border-white/10 rounded-xl p-6 hover:border-white/30 hover:bg-white/5 transition-all cursor-pointer">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs font-medium px-2 py-1 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
            {formatDomain(course.domain)}
          </span>
          <span className="text-xs text-white/30">{formatDate(course.created_at)}</span>
        </div>
        <h2 className="text-lg font-semibold text-white mb-2 group-hover:text-indigo-300 transition-colors line-clamp-2">
          {course.title}
        </h2>
        <p className="text-sm text-white/60 line-clamp-3">{course.summary}</p>
        <div className="mt-4 text-xs text-indigo-400 font-medium">
          Start learning →
        </div>
      </div>
    </Link>
  );
}
