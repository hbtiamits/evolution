"use client";

import { useState } from "react";
import { QuizData, SubmitResult, submitQuiz, generateQuiz } from "@/lib/api";

type Phase = "intro" | "taking" | "results";

export default function QuizClient({
  courseId,
  courseTitle,
  initialQuiz,
}: {
  courseId: string;
  courseTitle: string;
  initialQuiz: QuizData | null;
}) {
  const [quiz, setQuiz] = useState<QuizData | null>(initialQuiz);
  const [phase, setPhase] = useState<Phase>("intro");
  const [answers, setAnswers] = useState<(number | null)[]>([]);
  const [current, setCurrent] = useState(0);
  const [result, setResult] = useState<SubmitResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    try {
      const q = await generateQuiz(courseId);
      setQuiz(q);
      setAnswers(new Array(q.questions.length).fill(null));
      setCurrent(0);
      setPhase("taking");
    } catch {
      setError("Failed to generate quiz. Try again.");
    } finally {
      setLoading(false);
    }
  }

  function handleStart() {
    if (!quiz) return;
    setAnswers(new Array(quiz.questions.length).fill(null));
    setCurrent(0);
    setPhase("taking");
  }

  function handleSelect(optionIndex: number) {
    setAnswers((prev) => {
      const next = [...prev];
      next[current] = optionIndex;
      return next;
    });
  }

  async function handleSubmit() {
    if (!quiz) return;
    setLoading(true);
    setError(null);
    try {
      const finalAnswers = answers.map((a) => (a === null ? 0 : a));
      const res = await submitQuiz(courseId, finalAnswers);
      setResult(res);
      setPhase("results");
    } catch {
      setError("Failed to submit quiz. Try again.");
    } finally {
      setLoading(false);
    }
  }

  function handleRetake() {
    if (!quiz) return;
    setAnswers(new Array(quiz.questions.length).fill(null));
    setCurrent(0);
    setResult(null);
    setPhase("taking");
  }

  // --- Intro phase ---
  if (phase === "intro") {
    return (
      <div className="max-w-xl mx-auto text-center py-16">
        <div className="text-5xl mb-6">🧠</div>
        <h2 className="text-2xl font-bold text-white mb-3">Test Your Knowledge</h2>
        <p className="text-white/50 mb-8">
          5 multiple-choice questions on <span className="text-white/80 font-medium">{courseTitle}</span>.
        </p>
        {error && <p className="text-red-400 text-sm mb-4">{error}</p>}
        {quiz ? (
          <button
            onClick={handleStart}
            className="px-8 py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-xl transition-colors"
          >
            Start Quiz
          </button>
        ) : (
          <button
            onClick={handleGenerate}
            disabled={loading}
            className="px-8 py-3 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold rounded-xl transition-colors"
          >
            {loading ? "Generating…" : "Generate Quiz"}
          </button>
        )}
      </div>
    );
  }

  // --- Taking phase ---
  if (phase === "taking" && quiz) {
    const q = quiz.questions[current];
    const selected = answers[current];
    const allAnswered = answers.every((a) => a !== null);

    return (
      <div className="max-w-2xl mx-auto">
        {/* Progress */}
        <div className="flex items-center justify-between mb-6">
          <span className="text-sm text-white/40">
            Question {current + 1} of {quiz.questions.length}
          </span>
          <div className="flex gap-1">
            {quiz.questions.map((_, i) => (
              <button
                key={i}
                onClick={() => setCurrent(i)}
                className={`w-6 h-2 rounded-full transition-colors ${
                  i === current
                    ? "bg-indigo-500"
                    : answers[i] !== null
                    ? "bg-indigo-800"
                    : "bg-white/15"
                }`}
              />
            ))}
          </div>
        </div>

        {/* Question */}
        <div className="border border-white/10 rounded-2xl p-8 mb-6">
          <p className="text-lg font-semibold text-white mb-6 leading-relaxed">{q.question}</p>
          <div className="space-y-3">
            {q.options.map((opt, i) => (
              <button
                key={i}
                onClick={() => handleSelect(i)}
                className={`w-full text-left px-5 py-4 rounded-xl border transition-all ${
                  selected === i
                    ? "border-indigo-500 bg-indigo-500/20 text-white"
                    : "border-white/10 text-white/70 hover:border-white/30 hover:text-white hover:bg-white/5"
                }`}
              >
                <span className="font-medium text-indigo-400 mr-3">
                  {["A", "B", "C", "D"][i]}.
                </span>
                {opt}
              </button>
            ))}
          </div>
        </div>

        {/* Navigation */}
        <div className="flex items-center justify-between">
          <button
            onClick={() => setCurrent((c) => Math.max(0, c - 1))}
            disabled={current === 0}
            className="px-5 py-2.5 rounded-xl border border-white/15 text-white/50 hover:text-white hover:border-white/30 disabled:opacity-30 transition-colors text-sm"
          >
            ← Previous
          </button>

          {current < quiz.questions.length - 1 ? (
            <button
              onClick={() => setCurrent((c) => c + 1)}
              disabled={selected === null}
              className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white font-medium transition-colors text-sm"
            >
              Next →
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={!allAnswered || loading}
              className="px-6 py-2.5 rounded-xl bg-green-600 hover:bg-green-500 disabled:opacity-40 text-white font-semibold transition-colors text-sm"
            >
              {loading ? "Submitting…" : "Submit Quiz"}
            </button>
          )}
        </div>
        {error && <p className="text-red-400 text-sm mt-4 text-center">{error}</p>}
      </div>
    );
  }

  // --- Results phase ---
  if (phase === "results" && result) {
    const pct = result.percentage;
    const scoreColor =
      pct >= 80 ? "text-green-400" : pct >= 60 ? "text-yellow-400" : "text-red-400";

    return (
      <div className="max-w-2xl mx-auto">
        {/* Score banner */}
        <div className="border border-white/10 rounded-2xl p-8 mb-8 text-center">
          <div className={`text-6xl font-bold mb-2 ${scoreColor}`}>{pct}%</div>
          <p className="text-white/50 text-lg">
            {result.score} / {result.total} correct
          </p>
          <p className={`mt-2 font-medium ${scoreColor}`}>
            {pct >= 80 ? "Excellent work!" : pct >= 60 ? "Good effort!" : "Keep studying!"}
          </p>
        </div>

        {/* Per-question breakdown */}
        <div className="space-y-4 mb-8">
          {result.results.map((r, i) => (
            <div
              key={r.question_id}
              className={`border rounded-xl p-5 ${
                r.is_correct ? "border-green-500/30 bg-green-500/5" : "border-red-500/30 bg-red-500/5"
              }`}
            >
              <div className="flex items-start gap-3 mb-3">
                <span className={`text-lg flex-shrink-0 ${r.is_correct ? "text-green-400" : "text-red-400"}`}>
                  {r.is_correct ? "✓" : "✗"}
                </span>
                <p className="text-white font-medium">{r.question}</p>
              </div>

              <div className="ml-8 space-y-1 text-sm mb-3">
                {quiz!.questions[i].options.map((opt, optIdx) => (
                  <div
                    key={optIdx}
                    className={`flex gap-2 px-3 py-1.5 rounded-lg ${
                      optIdx === r.correct_index
                        ? "bg-green-500/20 text-green-300"
                        : optIdx === r.selected_index && !r.is_correct
                        ? "bg-red-500/20 text-red-300"
                        : "text-white/40"
                    }`}
                  >
                    <span className="font-semibold">{["A", "B", "C", "D"][optIdx]}.</span>
                    {opt}
                    {optIdx === r.correct_index && (
                      <span className="ml-auto text-green-400 text-xs font-medium">correct</span>
                    )}
                    {optIdx === r.selected_index && !r.is_correct && (
                      <span className="ml-auto text-red-400 text-xs font-medium">your answer</span>
                    )}
                  </div>
                ))}
              </div>

              {r.explanation && (
                <p className="ml-8 text-xs text-white/40 italic">{r.explanation}</p>
              )}
            </div>
          ))}
        </div>

        <div className="flex gap-4">
          <button
            onClick={handleRetake}
            className="px-6 py-2.5 border border-white/20 text-white/70 hover:text-white hover:border-white/40 rounded-xl transition-colors text-sm"
          >
            Retake Quiz
          </button>
          <button
            onClick={handleGenerate}
            disabled={loading}
            className="px-6 py-2.5 border border-indigo-500/40 text-indigo-400 hover:text-indigo-300 hover:border-indigo-400 rounded-xl transition-colors text-sm disabled:opacity-50"
          >
            {loading ? "Generating…" : "New Questions"}
          </button>
        </div>
      </div>
    );
  }

  return null;
}
