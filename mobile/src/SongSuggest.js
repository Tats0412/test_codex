import { useEffect, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { fetchSongs } from "./api";

export function SongSuggest({ query, onPick }) {
  const [songs, setSongs] = useState([]);

  useEffect(() => {
    let cancelled = false;
    fetchSongs()
      .then((s) => {
        if (!cancelled) setSongs(s);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  const q = (query || "").trim().toLowerCase();
  if (!q || songs.length === 0) return null;

  const matches = songs
    .filter((s) => s.song_title.toLowerCase().includes(q))
    .slice(0, 5);

  if (matches.length === 0) return null;

  return (
    <View style={styles.box}>
      {matches.map((m) => (
        <Pressable
          key={m.song_title}
          style={styles.item}
          onPress={() => onPick(m)}
        >
          <Text style={styles.title}>{m.song_title}</Text>
          {m.artist ? <Text style={styles.artist}>{m.artist}</Text> : null}
        </Pressable>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  box: {
    marginTop: 4,
    backgroundColor: "#0f1530",
    borderRadius: 10,
    overflow: "hidden",
  },
  item: {
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderBottomColor: "#1b2650",
    borderBottomWidth: 1,
  },
  title: { color: "#ffffff", fontSize: 14 },
  artist: { color: "#9bb0ff", fontSize: 11, marginTop: 2 },
});
