import { getCourses, getDomains } from "@/lib/api";
import CourseCard from "@/components/CourseCard";
import Link from "next/link";

export default async function HomePage({
  searchParams,
}: {
  searchParams: Promise<{ domain?: string }>;
}) {
  const { domain } = await searchParams;
  const [courses, domains] = await Promise.all([getCourses(domain), getDomains()]);

  return (
    <div>
      <div className="mb-10">
        <h1 className="text-4xl font-bold text-white mb-3">AI Courses</h1>
        <p className="text-white/50 text-lg">
          Structured mini-courses generated daily from the latest AI research papers.
        </p>
      </div>

      {/* Domain filter */}
      {domains.length > 0 && (
        <div className="flex gap-2 flex-wrap mb-8">
          <Link
            href="/"
            className={`text-sm px-3 py-1.5 rounded-full border transition-colors ${
              !domain
                ? "bg-indigo-600 border-indigo-600 text-white"
                : "border-white/20 text-white/60 hover:text-white hover:border-white/40"
            }`}
          >
            All
          </Link>
          {domains.map((d) => (
            <Link
              key={d}
              href={`/?domain=${d}`}
              className={`text-sm px-3 py-1.5 rounded-full border transition-colors capitalize ${
                domain === d
                  ? "bg-indigo-600 border-indigo-600 text-white"
                  : "border-white/20 text-white/60 hover:text-white hover:border-white/40"
              }`}
            >
              {d.replace(/_/g, " ")}
            </Link>
          ))}
        </div>
      )}

      {courses.length === 0 ? (
        <div className="text-center py-24 text-white/30">
          <p className="text-xl mb-2">No courses yet</p>
          <p className="text-sm">Courses will appear here once the pipeline runs.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {courses.map((course) => (
            <CourseCard key={course.id} course={course} />
          ))}
        </div>
      )}
    </div>
  );
}
