import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";

export const metadata: Metadata = {
  title: "AI Course Generator",
  description: "Autonomous AI-powered courses generated daily from latest research",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <nav className="border-b border-white/10 px-6 py-4">
          <div className="max-w-6xl mx-auto flex items-center justify-between">
            <Link href="/" className="text-xl font-bold text-white tracking-tight">
              AI Courses
            </Link>
            <div className="flex gap-6 text-sm text-white/60">
              <Link href="/" className="hover:text-white transition-colors">Browse</Link>
              <Link href="/domains" className="hover:text-white transition-colors">Domains</Link>
            </div>
          </div>
        </nav>
        <main className="max-w-6xl mx-auto px-6 py-10">{children}</main>
      </body>
    </html>
  );
}
