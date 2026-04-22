import { useEffect, useRef, useState } from "react";
import { Audio } from "expo-av";

export function usePlayer() {
  const soundRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    return () => {
      if (soundRef.current) soundRef.current.unloadAsync().catch(() => {});
    };
  }, []);

  async function play(uri) {
    if (!uri) return;
    if (soundRef.current) {
      await soundRef.current.unloadAsync().catch(() => {});
      soundRef.current = null;
    }
    const { sound } = await Audio.Sound.createAsync(
      { uri },
      { shouldPlay: true },
      (status) => {
        if (!status.isLoaded) return;
        if (status.didJustFinish) setIsPlaying(false);
        else setIsPlaying(Boolean(status.isPlaying));
      },
    );
    soundRef.current = sound;
    setIsPlaying(true);
  }

  async function stop() {
    if (soundRef.current) {
      await soundRef.current.stopAsync().catch(() => {});
      setIsPlaying(false);
    }
  }

  return { isPlaying, play, stop };
}
