import { getDomains, getCourses, formatDomain } from "@/lib/api";
import CourseCard from "@/components/CourseCard";

export default async function DomainsPage() {
  const domains = await getDomains();

  const domainCourses = await Promise.all(
    domains.map(async (domain) => ({
      domain,
      courses: await getCourses(domain, 3),
    }))
  );

  return (
    <div>
      <div className="mb-10">
        <h1 className="text-4xl font-bold text-white mb-3">Explore by Domain</h1>
        <p className="text-white/50">Browse courses organized by research area.</p>
      </div>

      <div className="space-y-14">
        {domainCourses.map(({ domain, courses }) => (
          <section key={domain}>
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-2xl font-semibold text-white">{formatDomain(domain)}</h2>
              <a
                href={`/?domain=${domain}`}
                className="text-sm text-indigo-400 hover:text-indigo-300 transition-colors"
              >
                View all →
              </a>
            </div>
            {courses.length === 0 ? (
              <p className="text-white/30 text-sm">No courses yet in this domain.</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                {courses.map((course) => (
                  <CourseCard key={course.id} course={course} />
                ))}
              </div>
            )}
          </section>
        ))}
      </div>
    </div>
  );
}
