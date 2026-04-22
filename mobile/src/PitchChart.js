import { StyleSheet, Text, View } from "react-native";
import Svg, { Circle, Line, Polyline } from "react-native-svg";

const WIDTH = 320;
const HEIGHT = 140;
const PAD = 8;

export function PitchChart({ features }) {
  if (!features) return null;
  const pts = features.pitch_contour_midi || [];
  const times = features.contour_times_sec || [];
  if (pts.length === 0) return null;

  const validVals = pts.filter((v) => v != null);
  if (validVals.length === 0) return null;

  const minY = Math.min(...validVals) - 1;
  const maxY = Math.max(...validVals) + 1;
  const minX = times[0];
  const maxX = times[times.length - 1] || minX + 1;

  const xScale = (t) =>
    PAD + ((t - minX) / Math.max(0.001, maxX - minX)) * (WIDTH - 2 * PAD);
  const yScale = (m) =>
    HEIGHT - PAD - ((m - minY) / Math.max(0.001, maxY - minY)) * (HEIGHT - 2 * PAD);

  // Build polylines broken at unvoiced gaps
  const segments = [];
  let current = [];
  pts.forEach((v, i) => {
    if (v == null) {
      if (current.length > 1) segments.push(current);
      current = [];
    } else {
      current.push(`${xScale(times[i]).toFixed(1)},${yScale(v).toFixed(1)}`);
    }
  });
  if (current.length > 1) segments.push(current);

  return (
    <View style={styles.card}>
      <Text style={styles.title}>音程の推移</Text>
      <Svg width={WIDTH} height={HEIGHT}>
        <Line
          x1={PAD}
          y1={HEIGHT / 2}
          x2={WIDTH - PAD}
          y2={HEIGHT / 2}
          stroke="#2a315a"
          strokeWidth="1"
          strokeDasharray="3,3"
        />
        {segments.map((seg, i) => (
          <Polyline
            key={i}
            points={seg.join(" ")}
            fill="none"
            stroke="#7aa2ff"
            strokeWidth="2"
          />
        ))}
        {pts.map((v, i) =>
          v == null ? null : (
            <Circle
              key={i}
              cx={xScale(times[i])}
              cy={yScale(v)}
              r="1.5"
              fill="#7aa2ff"
            />
          ),
        )}
      </Svg>
      <View style={styles.axis}>
        <Text style={styles.axisLabel}>0s</Text>
        <Text style={styles.axisLabel}>{maxX.toFixed(1)}s</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#141a33",
    padding: 12,
    borderRadius: 14,
    marginTop: 12,
  },
  title: { color: "#9bb0ff", fontSize: 13, fontWeight: "600", marginBottom: 6 },
  axis: { flexDirection: "row", justifyContent: "space-between", marginTop: 4 },
  axisLabel: { color: "#6d7bb0", fontSize: 11 },
});
