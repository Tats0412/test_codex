import { StyleSheet, Text, View } from "react-native";

function ScoreBar({ label, value }) {
  const clamped = Math.max(0, Math.min(100, value || 0));
  return (
    <View style={styles.scoreRow}>
      <Text style={styles.scoreLabel}>{label}</Text>
      <View style={styles.scoreTrack}>
        <View style={[styles.scoreFill, { width: `${clamped}%` }]} />
      </View>
      <Text style={styles.scoreValue}>{Math.round(clamped)}</Text>
    </View>
  );
}

export function FeedbackView({ data }) {
  if (!data) return null;
  const { feedback } = data;
  if (!feedback) return null;

  const scores = feedback.scores || {};

  return (
    <View style={styles.container}>
      <View style={styles.overallBox}>
        <Text style={styles.overallLabel}>総合スコア</Text>
        <Text style={styles.overallValue}>{feedback.overall_score ?? "-"}</Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>今日のワンポイント</Text>
        <Text style={styles.onePoint}>{feedback.one_point}</Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>項目別スコア</Text>
        <ScoreBar label="音程" value={scores.pitch} />
        <ScoreBar label="リズム" value={scores.rhythm} />
        <ScoreBar label="表現" value={scores.expression} />
        <ScoreBar label="安定" value={scores.stability} />
      </View>

      {feedback.strengths?.length > 0 && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>良かったところ</Text>
          {feedback.strengths.map((s, i) => (
            <Text key={i} style={styles.bullet}>
              ・{s}
            </Text>
          ))}
        </View>
      )}

      {feedback.improvements?.length > 0 && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>改善ポイント</Text>
          {feedback.improvements.map((imp, i) => (
            <View key={i} style={styles.improvement}>
              <Text style={styles.improvementArea}>{imp.area}</Text>
              <Text style={styles.improvementDetail}>{imp.detail}</Text>
              {imp.drill ? (
                <Text style={styles.improvementDrill}>練習: {imp.drill}</Text>
              ) : null}
            </View>
          ))}
        </View>
      )}

      {feedback.song_specific ? (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>この曲ならではの指摘</Text>
          <Text style={styles.paragraph}>{feedback.song_specific}</Text>
        </View>
      ) : null}

      {feedback.next_step ? (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>次回までの宿題</Text>
          <Text style={styles.paragraph}>{feedback.next_step}</Text>
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: 12, marginTop: 16 },
  overallBox: {
    backgroundColor: "#1b2650",
    padding: 20,
    borderRadius: 16,
    alignItems: "center",
  },
  overallLabel: { color: "#9bb0ff", fontSize: 14, marginBottom: 4 },
  overallValue: { color: "#ffffff", fontSize: 48, fontWeight: "700" },
  card: {
    backgroundColor: "#141a33",
    padding: 16,
    borderRadius: 14,
    gap: 8,
  },
  cardTitle: { color: "#9bb0ff", fontSize: 13, fontWeight: "600" },
  onePoint: { color: "#ffffff", fontSize: 16, lineHeight: 22 },
  scoreRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  scoreLabel: { color: "#dfe5ff", width: 48, fontSize: 13 },
  scoreTrack: {
    flex: 1,
    height: 8,
    backgroundColor: "#2a315a",
    borderRadius: 4,
    overflow: "hidden",
  },
  scoreFill: { height: "100%", backgroundColor: "#7aa2ff" },
  scoreValue: { color: "#ffffff", width: 32, textAlign: "right", fontSize: 13 },
  bullet: { color: "#ffffff", fontSize: 14, lineHeight: 20 },
  improvement: {
    backgroundColor: "#0f1530",
    padding: 10,
    borderRadius: 10,
    gap: 2,
  },
  improvementArea: { color: "#ffd48a", fontWeight: "600" },
  improvementDetail: { color: "#ffffff", lineHeight: 20 },
  improvementDrill: { color: "#9bb0ff", fontStyle: "italic", marginTop: 4 },
  paragraph: { color: "#ffffff", lineHeight: 20 },
});
