"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { startVideoGeneration, getVideoJob, getVideoStreamUrl, VideoJob } from "@/lib/api";

const EXAMPLES = [
  "Create a 30-second product launch video for a new electric skateboard called 'Volt' — bold, futuristic, dark theme with electric blue accents",
  "Make a warm, inviting promo video for a family-owned Italian restaurant called 'La Cucina' with earthy tones",
  "Generate a professional 45-second company intro for a fintech startup focused on AI-powered investments",
  "Create an energetic fitness app promotion video with vibrant colors and motivational messages",
  "Design a cinematic travel video showcasing highlights of a luxury Maldives resort",
];

const POLL_INTERVAL = 1500;

export default function VideoGenerator() {
  const [prompt, setPrompt] = useState("");
  const [jobId, setJobId] = useState<string | null>(null);
  const [job, setJob] = useState<VideoJob | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const startPolling = useCallback(
    (id: string) => {
      stopPolling();
      pollRef.current = setInterval(async () => {
        try {
          const data = await getVideoJob(id);
          setJob(data);
          if (data.status === "done" || data.status === "error") {
            stopPolling();
            setIsLoading(false);
            if (data.status === "error") {
              setError(data.error || "Video generation failed");
            }
          }
        } catch {
          // ignore transient poll errors
        }
      }, POLL_INTERVAL);
    },
    [stopPolling]
  );

  useEffect(() => () => stopPolling(), [stopPolling]);

  const handleGenerate = async () => {
    if (!prompt.trim() || isLoading) return;
    setError(null);
    setJob(null);
    setJobId(null);
    setIsLoading(true);

    try {
      const { job_id } = await startVideoGeneration(prompt.trim());
      setJobId(job_id);
      startPolling(job_id);
    } catch (e) {
      setError("Could not connect to the video server. Make sure the backend is running.");
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      handleGenerate();
    }
  };

  const handleReset = () => {
    stopPolling();
    setJobId(null);
    setJob(null);
    setIsLoading(false);
    setError(null);
    setPrompt("");
  };

  const progress = job?.progress ?? 0;
  const isDone = job?.status === "done";
  const isError = job?.status === "error";

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-white mb-3 tracking-tight">
          NLP Video Generator
        </h1>
        <p className="text-white/50 text-lg">
          Describe your video in plain English and watch AI bring it to life — scenes, narration, and visuals included.
        </p>
      </div>

      {/* Prompt area */}
      {!isDone && (
        <div className="space-y-4">
          <div className="relative">
            <textarea
              className="w-full h-36 bg-white/5 border border-white/10 rounded-xl px-5 py-4 text-white text-base resize-none placeholder-white/25 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors"
              placeholder="Describe your video… e.g. 'Create a 30-second product launch for a smart coffee maker with a modern, warm aesthetic'"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
            />
            <span className="absolute bottom-3 right-4 text-white/20 text-xs">
              {prompt.length > 0 ? `${prompt.length} chars` : "Ctrl+Enter to generate"}
            </span>
          </div>

          {/* Example prompts */}
          <div className="space-y-2">
            <p className="text-white/30 text-xs uppercase tracking-widest">Try an example</p>
            <div className="flex flex-col gap-2">
              {EXAMPLES.map((ex, i) => (
                <button
                  key={i}
                  onClick={() => setPrompt(ex)}
                  disabled={isLoading}
                  className="text-left text-sm text-white/40 hover:text-white/70 hover:bg-white/5 px-3 py-2 rounded-lg transition-colors border border-transparent hover:border-white/10 truncate"
                >
                  {ex}
                </button>
              ))}
            </div>
          </div>

          <button
            onClick={handleGenerate}
            disabled={isLoading || !prompt.trim()}
            className="w-full py-3 rounded-xl font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed transition-all focus:outline-none focus:ring-2 focus:ring-indigo-400"
          >
            {isLoading ? "Generating…" : "Generate Video"}
          </button>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-red-300 text-sm flex items-start gap-3">
          <span className="text-lg">⚠</span>
          <div>
            <p className="font-medium mb-1">Generation failed</p>
            <p className="text-red-400/80">{error}</p>
            <button onClick={handleReset} className="mt-3 text-red-300 underline text-xs">
              Try again
            </button>
          </div>
        </div>
      )}

      {/* Progress */}
      {isLoading && job && (
        <div className="space-y-3">
          <div className="flex justify-between text-sm">
            <span className="text-white/60">{job.message}</span>
            <span className="text-indigo-400 font-mono">{Math.round(progress * 100)}%</span>
          </div>
          <div className="h-2 bg-white/10 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-indigo-600 to-purple-500 rounded-full transition-all duration-500"
              style={{ width: `${Math.round(progress * 100)}%` }}
            />
          </div>
          <ProgressSteps progress={progress} />
        </div>
      )}

      {/* Waiting spinner (before first poll result) */}
      {isLoading && !job && (
        <div className="flex items-center gap-3 text-white/50">
          <LoadingDots />
          <span className="text-sm">Connecting to generation server…</span>
        </div>
      )}

      {/* Result */}
      {isDone && job && (
        <div className="space-y-6">
          {/* Meta */}
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <h2 className="text-2xl font-bold text-white">{job.title}</h2>
              {job.subtitle && <p className="text-white/50 mt-1">{job.subtitle}</p>}
              <div className="flex gap-4 mt-3 text-sm text-white/40">
                <span>{job.scenes} scenes</span>
                <span>•</span>
                <span>{job.duration}s total</span>
              </div>
            </div>
            <div className="flex gap-2">
              <a
                href={getVideoStreamUrl(jobId!)}
                download={`${job.title?.replace(/\s+/g, "_") || "video"}.mp4`}
                className="px-4 py-2 bg-white/10 hover:bg-white/20 border border-white/10 rounded-lg text-sm text-white transition-colors"
              >
                Download MP4
              </a>
              <button
                onClick={handleReset}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm text-white transition-colors"
              >
                New Video
              </button>
            </div>
          </div>

          {/* Video player */}
          <div className="rounded-2xl overflow-hidden bg-black border border-white/10 shadow-2xl">
            <video
              ref={videoRef}
              src={getVideoStreamUrl(jobId!)}
              controls
              autoPlay
              loop
              className="w-full aspect-video"
            >
              Your browser does not support video playback.
            </video>
          </div>

          {/* Prompt recap */}
          <div className="bg-white/5 border border-white/10 rounded-xl px-5 py-4 text-sm text-white/40">
            <span className="text-white/20 uppercase text-xs tracking-widest block mb-2">Generated from</span>
            {prompt}
          </div>
        </div>
      )}
    </div>
  );
}

function ProgressSteps({ progress }: { progress: number }) {
  const steps = [
    { label: "AI Planning", threshold: 0.05 },
    { label: "Narration", threshold: 0.2 },
    { label: "Rendering Scenes", threshold: 0.25 },
    { label: "Compiling Video", threshold: 0.8 },
    { label: "Finalizing", threshold: 0.98 },
  ];
  return (
    <div className="flex gap-2 flex-wrap">
      {steps.map((s, i) => {
        const done = progress >= s.threshold;
        return (
          <span
            key={i}
            className={`text-xs px-3 py-1 rounded-full border transition-colors ${
              done
                ? "border-indigo-500/50 bg-indigo-500/20 text-indigo-300"
                : "border-white/10 text-white/20"
            }`}
          >
            {done ? "✓ " : ""}
            {s.label}
          </span>
        );
      })}
    </div>
  );
}

function LoadingDots() {
  return (
    <div className="flex gap-1">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce"
          style={{ animationDelay: `${i * 0.15}s` }}
        />
      ))}
    </div>
  );
}
