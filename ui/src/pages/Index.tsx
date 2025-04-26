import React, { useState, useRef, useEffect, useCallback } from "react";
import VideoWindow from "../components/VideoWindow";
import ChatInterface from "../components/ChatInterface";

const INITIAL_CONTEXT = "You are an Albert Einstein, a physicist who developed the theory of relativity. You are teaching a class about the relativity theory. Answer the questions from the students in a friendly and informative manner in english. You've prepared a lesson with slides to help explain the concepts. Below are the slides you showed and questions from the students with your answers.";

const slidesCount = 9; // Update this if you add/remove slides

var QUESTIONS_REACTIONS = ["/einstein_q1.mp4", "/einstein_q2.mp4"];


function getSlidePaths(idx: number) {
  return {
    slideTextFile: `/` + idx + `/slide_` + idx + `.txt`,
    slideImage: `/` + idx + `/` + idx + `.png`,
    video: `/` + idx + `/einstein_` + idx + `.mp4`,
  };
}

const LOOP_VIDEO = "/einsten-basic.mp4";
const TALKING_LOOP_VIDEO = "/einsten-basic.mp4";
const NO_SOUND_VIDEO = "/einstein_no_sound.mp4";

// State machine: 'slide-video', 'waiting-audio', 'playing-audio', 'initial', 'finished', 'reaction-video'
const Index: React.FC = () => {
  const [lessonStarted, setLessonStarted] = useState(false);
  const [currentSlideIdx, setCurrentSlideIdx] = useState(0);
  const [phase, setPhase] = useState<'slide-video' | 'waiting-audio' | 'playing-audio' | 'initial' | 'finished' | 'reaction-video'>('initial');
  const [context, setContext] = useState(INITIAL_CONTEXT);
  const [slideTexts, setSlideTexts] = useState<string[]>([]);
  const [questionQueue, setQuestionQueue] = useState<string[]>([]);
  const [isProcessingQueue, setIsProcessingQueue] = useState(false);
  const [reactionVideoSrc, setReactionVideoSrc] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const questionQueueRef = useRef<string[]>([]);
  useEffect(() => {
    questionQueueRef.current = questionQueue;
  }, [questionQueue]);

  // Only allow one processing at a time
  const isProcessingRef = useRef(false);

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

  // Process the question queue safely
  const processQuestionQueue = useCallback(async () => {
    if (isProcessingRef.current) return;
    isProcessingRef.current = true;
    while (questionQueueRef.current.length > 0) {
      const question = questionQueueRef.current[0];
      // 1. Play random reaction video
      const randomReaction = QUESTIONS_REACTIONS[Math.floor(Math.random() * QUESTIONS_REACTIONS.length)];
      setReactionVideoSrc(randomReaction);
      setPhase('reaction-video');
      // Wait for reaction video to finish
      await new Promise<void>((resolve) => {
        const handler = () => {
          setReactionVideoSrc(null);
          resolve();
        };
        // Attach a one-time event handler to VideoWindow via a custom event
        window.addEventListener('reactionVideoEnded', handler, { once: true });
      });
      setPhase('waiting-audio'); // Set phase to waiting-audio while waiting for API
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
        setPhase('playing-audio'); // Switch to playing-audio when audio is about to play
        await new Promise<void>((resolve) => {
          const audio = new Audio(audioUrl);
          audioRef.current = audio;
          audio.onended = () => {
            resolve();
          };
          audio.play();
        });
        setContext((prev) => prev + `\nQ: ${question}\nA: ${answerText}`);
      } catch (error) {
        console.error("Error synthesizing or playing audio:", error);
      }
      // Remove the answered question
      setQuestionQueue((prev) => prev.slice(1));
      // Wait for state update
      await new Promise((resolve) => setTimeout(resolve, 0));
    }
    isProcessingRef.current = false;
    setIsProcessingQueue(false);
    // Advance to next slide or finish
    if (currentSlideIdx < slidesCount - 1) {
      setCurrentSlideIdx((idx) => idx + 1);
      setPhase('slide-video');
    } else {
      setPhase('finished');
    }
  }, [context, currentSlideIdx]);

  // When the queue changes and we're processing, process the next question
  useEffect(() => {
    if (isProcessingQueue && questionQueue.length > 0 && !isProcessingRef.current) {
      processQuestionQueue();
    }
  }, [questionQueue, isProcessingQueue, processQuestionQueue]);

  // When slide video ends, start processing the queue
  const handleSlideVideoEnd = useCallback(() => {
    setContext(prev => prev + `\nSlide_${currentSlideIdx + 1}: "${slideTexts[currentSlideIdx] || ''}"`);
    if (questionQueueRef.current.length > 0) {
      setIsProcessingQueue(true);
    } else {
      // No questions, advance slide or finish
      if (currentSlideIdx < slidesCount - 1) {
        setCurrentSlideIdx((idx) => idx + 1);
        setPhase('slide-video');
      } else {
        setPhase('finished');
      }
    }
  }, [currentSlideIdx, slideTexts]);

  // Handle chat input: queue questions during slide-video or answer phase
  const handleQuestion = useCallback((question: string) => {
    if (!lessonStarted) {
      // Ignore all input if lesson hasn't started
      return;
    }
    setQuestionQueue((prev) => [...prev, question]);
    // If currently not processing, start processing
    if (!isProcessingQueue && phase !== 'slide-video') {
      setIsProcessingQueue(true);
    }
  }, [lessonStarted, isProcessingQueue, phase]);

  // Handler for Start Lesson button
  const handleStartLesson = useCallback(() => {
    setLessonStarted(true);
    setPhase('slide-video');
  }, []);

  // Handler for Stop Lesson button
  const handleStopLesson = useCallback(() => {
    setPhase('finished');
    setIsProcessingQueue(false);
    isProcessingRef.current = false;
    setQuestionQueue([]);
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
  }, []);

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
  } else if (phase === "waiting-audio") {
    videoSrc = TALKING_LOOP_VIDEO; // Show talking loop video while waiting for API
    showVideo = true;
    loop = true;
    muted = true;
  } else if (phase === "playing-audio") {
    videoSrc = NO_SOUND_VIDEO; // Play muted no-sound video while audio is playing
    showVideo = true;
    loop = true;
    muted = true;
  } else if (phase === 'reaction-video' && reactionVideoSrc) {
    videoSrc = reactionVideoSrc;
    showVideo = true;
    loop = false;
    muted = false;
  }

  // Custom handler for reaction video end
  const handleReactionVideoEnd = useCallback(() => {
    // Dispatch a custom event to notify processQuestionQueue
    window.dispatchEvent(new Event('reactionVideoEnded'));
  }, []);

  if (phase === 'finished') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-4 md:p-8 flex items-center justify-center">
        <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-xl p-8 text-center">
          <h1 className="text-3xl font-bold mb-4">Presentation Finished</h1>
          <p className="text-lg text-gray-700">Thank you for attending the lesson on relativity theory!</p>
        </div>
      </div>
    );
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
              onSlideVideoEnd={phase === 'reaction-video' ? handleReactionVideoEnd : handleSlideVideoEnd}
              phase={phase}
            />
          </div>
          {/* Chat takes up 30% on larger screens */}
          <div className="w-full md:w-[30%] h-1/2 md:h-full">
            <ChatInterface 
              onSendQuestion={handleQuestion} 
              lessonStarted={lessonStarted} 
              onStartLesson={handleStartLesson}
              onStopLesson={handleStopLesson}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;
