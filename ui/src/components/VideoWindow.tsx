import React, { useRef, useEffect } from "react";

interface VideoWindowProps {
  slide: { slideText: string; slideImage: string; video: string };
  videoSrc: string | null;
  showVideo: boolean;
  loop: boolean;
  onSlideVideoEnd: () => void;
  phase: 'slide-video' | 'pause-loop' | 'playing-audio';
}

const VideoWindow: React.FC<VideoWindowProps> = ({
  slide,
  videoSrc,
  showVideo,
  loop,
  onSlideVideoEnd,
  phase,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (showVideo && videoRef.current) {
      videoRef.current.currentTime = 0;
      videoRef.current.play().catch((error) => {
        console.error("Video playback error:", error);
      });
    }
  }, [videoSrc, showVideo]);

  return (
    <div className="relative w-full h-full bg-gray-900 rounded-l-lg overflow-hidden flex items-center justify-center">
      {/* Slide image as background */}
      <img
        src={slide.slideImage}
        alt="Slide"
        className="w-full h-full object-contain"
      />

      {/* Circular video overlay */}
      {showVideo && videoSrc && (
        <div className="absolute bottom-8 right-8 w-56 h-56 rounded-full overflow-hidden border-4 border-white shadow-lg flex items-center justify-center">
          <video
            ref={videoRef}
            src={videoSrc}
            className="w-full h-full object-cover -translate-y+100"
            autoPlay
            muted={phase === 'playing-audio' || phase === 'initial'}
            loop={loop}
            onEnded={loop ? undefined : onSlideVideoEnd}
          />
        </div>
      )}

    </div>
  );
};

export default VideoWindow;
