import React, { useState, useRef, useEffect, useCallback } from "react";
import VideoWindow from "../components/VideoWindow";
import ChatInterface from "../components/ChatInterface";

const INITIAL_CONTEXT = "You are an Albert Einstein, a physicist who developed the theory of relativity. You are teaching a class about the relativity theory. Answer the questions from the students in a friendly and informative manner in english. You've prepared a lesson with slides to help explain the concepts. Below are the slides you showed and questions from the students with your answers.";

const slidesCount = 9; // Update this if you add/remove slides

function getSlidePaths(idx: number) {
  return {
    slideTextFile: `/` + idx + `/slide_` + idx + `.txt`,
    slideImage: `/` + idx + `/` + idx + `.jpg`,
    video: `/` + idx + `/einstein_` + idx + `.mp4`,
  };
}

const LOOP_VIDEO = "/einsten-basic.mp4";
const TALKING_LOOP_VIDEO = "/einsten-basic.mp4";

// State machine: 'slide-video', 'pause-loop', 'playing-audio', 'initial'
const Index: React.FC = () => {
  const [lessonStarted, setLessonStarted] = useState(false);
  const [currentSlideIdx, setCurrentSlideIdx] = useState(0);
  const [phase, setPhase] = useState<'slide-video' | 'pause-loop' | 'playing-audio' | 'initial'>('initial');
  const [pendingQuestion, setPendingQuestion] = useState<string | null>(null);
  const [context, setContext] = useState(INITIAL_CONTEXT);
  const [slideTexts, setSlideTexts] = useState<string[]>([]);
  const pauseTimeout = useRef<NodeJS.Timeout | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Load all slide texts on mount
  useEffect(() => {
    Promise.all(
      Array.from({ length: slidesCount }, (_, idx) =>
        fetch(getSlidePaths(idx).slideTextFile).then(r => r.text())
      )
    )
      .then(setSlideTexts)
      .catch(err => {
        console.error("Failed to load slide texts", err);
        setSlideTexts(Array(slidesCount).fill(""));
      });
  }, []);

  // On mount, set phase to 'initial'
  useEffect(() => {
    setPhase('initial');
  }, []);

  // When slide video ends, start pause phase and add slide text to context
  const handleSlideVideoEnd = useCallback(() => {
    setContext(prev => prev + `\nSlide_${currentSlideIdx + 1}: "${slideTexts[currentSlideIdx] || ''}"`);
    setPhase("pause-loop");
  }, [currentSlideIdx, slideTexts]);

  // Handle chat input
  const handleQuestion = useCallback(async (question: string) => {
    if (!lessonStarted) {
      // Only accept 'Yes' (case-insensitive)
      if (question.trim().toLowerCase() === 'yes') {
        setLessonStarted(true);
        setPhase('slide-video');
      }
      // Ignore any other input for the first message
      return;
    }
    // When a question is sent from chat
    setPendingQuestion(question);
    setPhase("playing-audio");
    try {
      const response = await fetch("http://localhost:8000/synthesize-speech", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ context, question }),
      });
      if (!response.ok) throw new Error("Failed to synthesize speech");
      const data = await response.json();
      const answerText = data.answer || "";
      const audioBase64 = data.audio_base64;
      // Decode base64 audio
      const audioBlob = base64ToBlob(audioBase64, "audio/mp3");
      const audioUrl = URL.createObjectURL(audioBlob);
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      const audio = new Audio(audioUrl);
      audioRef.current = audio;
      audio.onended = () => {
        setPhase("pause-loop");
        setPendingQuestion(null);
      };
      audio.play();
      setContext((prev) => prev + `\nQ: ${question}\nA: ${answerText}`);
    } catch (error) {
      console.error("Error synthesizing or playing audio:", error);
      setPhase("pause-loop");
      setPendingQuestion(null);
    }
  }, [context, lessonStarted]);

  // Helper to decode base64 to Blob
  function base64ToBlob(base64: string, mime: string) {
    const byteChars = atob(base64);
    const byteNumbers = new Array(byteChars.length);
    for (let i = 0; i < byteChars.length; i++) {
      byteNumbers[i] = byteChars.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: mime });
  }

  // Pause phase: start 10s timer, if no question, advance slide
  useEffect(() => {
    if (phase === "pause-loop") {
      if (pauseTimeout.current) clearTimeout(pauseTimeout.current);
      pauseTimeout.current = setTimeout(() => {
        setPhase("slide-video");
        setCurrentSlideIdx((idx) => (idx + 1) % slidesCount);
      }, 10000);
    } else if (phase !== "pause-loop" && pauseTimeout.current) {
      clearTimeout(pauseTimeout.current);
      pauseTimeout.current = null;
    }
    return () => {
      if (pauseTimeout.current) clearTimeout(pauseTimeout.current);
    };
  }, [phase]);

  // Clean up audio on unmount
  useEffect(() => {
    return () => {
      if (audioRef.current) audioRef.current.pause();
    };
  }, []);

  // Determine what to show in VideoWindow
  const currentSlidePaths = getSlidePaths(currentSlideIdx);

  let videoSrc = null;
  let showVideo = false;
  let loop = false;
  let muted = false;
  if (phase === "initial") {
    videoSrc = LOOP_VIDEO;
    showVideo = true;
    loop = true;
    muted = true;
  } else if (phase === "slide-video") {
    videoSrc = currentSlidePaths.video;
    showVideo = true;
    loop = false;
    muted = false;
  } else if (phase === "pause-loop") {
    videoSrc = LOOP_VIDEO;
    showVideo = true;
    loop = true;
    muted = true;
  } else if (phase === "playing-audio") {
    videoSrc = TALKING_LOOP_VIDEO;
    showVideo = true;
    loop = true;
    muted = true;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-4 md:p-8">
      <div className="max-w-7xl h-[calc(100vh-4rem)] mx-auto bg-white rounded-lg shadow-xl overflow-hidden">
        <div className="flex flex-col md:flex-row h-full">
          {/* Video takes up 70% on larger screens */}
          <div className="w-full md:w-[70%] h-1/2 md:h-full">
            <VideoWindow
              slide={{
                slideText: slideTexts[currentSlideIdx] || "",
                slideImage: currentSlidePaths.slideImage,
                video: currentSlidePaths.video,
              }}
              videoSrc={videoSrc}
              showVideo={showVideo}
              loop={loop}
              muted={muted}
              onSlideVideoEnd={handleSlideVideoEnd}
              phase={phase}
            />
          </div>
          {/* Chat takes up 30% on larger screens */}
          <div className="w-full md:w-[30%] h-1/2 md:h-full">
            <ChatInterface onSendQuestion={handleQuestion} lessonStarted={lessonStarted} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;
