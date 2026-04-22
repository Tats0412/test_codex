import { useEffect, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { fetchSessionDetail, fetchSessions } from "./api";
import { FeedbackView } from "./FeedbackView";

export function HistoryScreen({ onClose }) {
  const [sessions, setSessions] = useState(null);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  async function load() {
    try {
      setError(null);
      const list = await fetchSessions();
      setSessions(list);
    } catch (e) {
      setError(e.message || String(e));
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function openDetail(id) {
    setLoading(true);
    try {
      const detail = await fetchSessionDetail(id);
      setSelected(detail);
    } catch (e) {
      setError(e.message || String(e));
    } finally {
      setLoading(false);
    }
  }

  if (selected) {
    return (
      <ScrollView contentContainerStyle={styles.scroll}>
        <View style={styles.header}>
          <Pressable onPress={() => setSelected(null)}>
            <Text style={styles.backLink}>← 履歴に戻る</Text>
          </Pressable>
          <Text style={styles.sub}>
            {selected.song_title}
            {selected.artist ? ` / ${selected.artist}` : ""}
          </Text>
          <Text style={styles.time}>
            {new Date(selected.created_at).toLocaleString()}
          </Text>
        </View>
        <FeedbackView data={selected} />
      </ScrollView>
    );
  }

  return (
    <ScrollView
      contentContainerStyle={styles.scroll}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={async () => {
            setRefreshing(true);
            await load();
            setRefreshing(false);
          }}
          tintColor="#7aa2ff"
        />
      }
    >
      <View style={styles.header}>
        <Pressable onPress={onClose}>
          <Text style={styles.backLink}>← 戻る</Text>
        </Pressable>
        <Text style={styles.title}>練習履歴</Text>
      </View>

      {loading && <ActivityIndicator color="#7aa2ff" />}
      {error && <Text style={styles.error}>{error}</Text>}

      {sessions === null ? (
        <ActivityIndicator color="#7aa2ff" />
      ) : sessions.length === 0 ? (
        <Text style={styles.empty}>まだ履歴がありません。録音してみましょう。</Text>
      ) : (
        sessions.map((s) => (
          <Pressable
            key={s.id}
            style={styles.row}
            onPress={() => openDetail(s.id)}
          >
            <View style={{ flex: 1 }}>
              <Text style={styles.song}>{s.song_title}</Text>
              {s.artist ? <Text style={styles.artist}>{s.artist}</Text> : null}
              <Text style={styles.rowTime}>
                {new Date(s.created_at).toLocaleString()}
              </Text>
            </View>
            <View style={styles.scorePill}>
              <Text style={styles.scorePillText}>{s.overall ?? "-"}</Text>
            </View>
          </Pressable>
        ))
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scroll: { padding: 20, paddingBottom: 60, gap: 10 },
  header: { marginBottom: 12, gap: 4 },
  backLink: { color: "#7aa2ff", fontSize: 14 },
  title: { color: "#ffffff", fontSize: 24, fontWeight: "700", marginTop: 6 },
  sub: { color: "#ffffff", fontSize: 16, marginTop: 6 },
  time: { color: "#9bb0ff", fontSize: 12 },
  empty: { color: "#9bb0ff", textAlign: "center", marginTop: 40 },
  error: { color: "#ff9fb6" },
  row: {
    flexDirection: "row",
    backgroundColor: "#141a33",
    padding: 14,
    borderRadius: 12,
    alignItems: "center",
    gap: 12,
  },
  song: { color: "#ffffff", fontSize: 15, fontWeight: "600" },
  artist: { color: "#9bb0ff", fontSize: 12, marginTop: 2 },
  rowTime: { color: "#6d7bb0", fontSize: 11, marginTop: 4 },
  scorePill: {
    backgroundColor: "#1b2650",
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 999,
  },
  scorePillText: { color: "#ffffff", fontWeight: "700", fontSize: 16 },
});
