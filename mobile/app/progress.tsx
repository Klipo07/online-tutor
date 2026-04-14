// Экран прогресса — статистика, heatmap, предметы, слабые темы
import { useCallback, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  TouchableOpacity,
  RefreshControl,
} from "react-native";
import { Stack, useFocusEffect, useRouter } from "expo-router";
import api from "../services/api";
import { Colors } from "../constants/theme";
import { Heatmap } from "../components/Heatmap";

type Stats = {
  tests_completed: number;
  average_score: number;
  chat_sessions: number;
  lessons_completed: number;
  subjects_studied: number;
  total_study_time_minutes: number;
  streak_days: number;
  active_days_this_week: number;
};

type ProgressItem = {
  subject_id: number;
  subject_name: string;
  score: number;
  weak_topics: string[];
  last_activity: string;
};

type ActivityDay = { date: string; count: number };

function getScoreColor(score: number) {
  if (score >= 80) return Colors.success;
  if (score >= 60) return Colors.warning;
  return Colors.error;
}

function formatHours(minutes: number): string {
  if (minutes < 60) return `${minutes} мин`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m === 0 ? `${h} ч` : `${h} ч ${m} м`;
}

export default function ProgressScreen() {
  const router = useRouter();
  const [stats, setStats] = useState<Stats | null>(null);
  const [progress, setProgress] = useState<ProgressItem[]>([]);
  const [activity, setActivity] = useState<ActivityDay[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const [s, p, a] = await Promise.all([
        api.get("/users/me/stats"),
        api.get("/users/me/progress"),
        api.get("/users/me/activity", { params: { days: 91 } }),
      ]);
      setStats(s.data);
      setProgress(p.data.progress);
      setActivity(a.data.activity);
    } catch {
      // noop
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      setLoading(true);
      load();
    }, [load]),
  );

  const onRefresh = () => {
    setRefreshing(true);
    load();
  };

  const openWeakTopic = (subject: string, topic: string) => {
    router.push({
      pathname: "/(tabs)/chat",
      params: { subject, topic },
    });
  };

  const weakTopics = progress
    .flatMap((p) => p.weak_topics.map((t) => ({ subject: p.subject_name, topic: t, score: p.score })))
    .slice(0, 5);

  return (
    <>
      <Stack.Screen options={{ title: "Мой прогресс" }} />
      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.content}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      >
        {loading ? (
          <View style={styles.centered}>
            <ActivityIndicator size="large" color={Colors.primary} />
          </View>
        ) : (
          <>
            {/* Streak + основные метрики */}
            {stats && (
              <View style={styles.topRow}>
                <View style={[styles.streakCard]}>
                  <Text style={styles.streakIcon}>🔥</Text>
                  <Text style={styles.streakValue}>{stats.streak_days}</Text>
                  <Text style={styles.streakLabel}>
                    {stats.streak_days === 1 ? "день подряд" : "дней подряд"}
                  </Text>
                </View>
                <View style={styles.sideStats}>
                  <View style={styles.sideCard}>
                    <Text style={styles.sideValue}>{stats.active_days_this_week}/7</Text>
                    <Text style={styles.sideLabel}>дней за неделю</Text>
                  </View>
                  <View style={styles.sideCard}>
                    <Text style={styles.sideValue}>{formatHours(stats.total_study_time_minutes)}</Text>
                    <Text style={styles.sideLabel}>всего обучения</Text>
                  </View>
                </View>
              </View>
            )}

            {/* Heatmap */}
            {activity.length > 0 && (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>Активность за 90 дней</Text>
                <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                  <Heatmap data={activity} />
                </ScrollView>
              </View>
            )}

            {/* Метрики сеткой */}
            {stats && (
              <View style={styles.metricsGrid}>
                <Metric value={stats.tests_completed} label="Тестов" />
                <Metric value={`${stats.average_score}%`} label="Средний балл" />
                <Metric value={stats.chat_sessions} label="AI-диалогов" />
                <Metric value={stats.lessons_completed} label="Занятий" />
              </View>
            )}

            {/* Прогресс по предметам */}
            {progress.length > 0 && (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>По предметам</Text>
                {progress.map((item) => (
                  <View key={item.subject_id} style={styles.progressCard}>
                    <View style={styles.progressHeader}>
                      <Text style={styles.progressSubject}>{item.subject_name}</Text>
                      <Text style={[styles.progressScore, { color: getScoreColor(item.score) }]}>
                        {item.score}%
                      </Text>
                    </View>
                    <View style={styles.progressBarBg}>
                      <View
                        style={[
                          styles.progressBarFill,
                          {
                            width: `${Math.min(item.score, 100)}%`,
                            backgroundColor: getScoreColor(item.score),
                          },
                        ]}
                      />
                    </View>
                  </View>
                ))}
              </View>
            )}

            {/* Слабые темы */}
            {weakTopics.length > 0 && (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>Подтяните слабые темы</Text>
                {weakTopics.map((w, i) => (
                  <TouchableOpacity
                    key={`${w.subject}-${w.topic}-${i}`}
                    style={styles.weakCard}
                    onPress={() => openWeakTopic(w.subject, w.topic)}
                  >
                    <View style={{ flex: 1 }}>
                      <Text style={styles.weakTopic}>{w.topic}</Text>
                      <Text style={styles.weakSubject}>{w.subject}</Text>
                    </View>
                    <Text style={styles.weakArrow}>→</Text>
                  </TouchableOpacity>
                ))}
              </View>
            )}

            {/* Пустое состояние */}
            {progress.length === 0 && stats?.tests_completed === 0 && (
              <View style={styles.empty}>
                <Text style={styles.emptyIcon}>📊</Text>
                <Text style={styles.emptyTitle}>Пока нет данных</Text>
                <Text style={styles.emptyText}>
                  Пройдите первый тест или пообщайтесь с AI-тьютором
                </Text>
              </View>
            )}
          </>
        )}
      </ScrollView>
    </>
  );
}

function Metric({ value, label }: { value: string | number; label: string }) {
  return (
    <View style={styles.metricCard}>
      <Text style={styles.metricValue}>{value}</Text>
      <Text style={styles.metricLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  content: { padding: 16, paddingBottom: 40 },
  centered: { paddingVertical: 60, alignItems: "center" },

  topRow: { flexDirection: "row", gap: 10, marginBottom: 16 },
  streakCard: {
    flex: 1.2,
    backgroundColor: "#FFF7ED",
    borderRadius: 14,
    padding: 16,
    alignItems: "center",
    borderWidth: 1,
    borderColor: "#FED7AA",
  },
  streakIcon: { fontSize: 32 },
  streakValue: { fontSize: 32, fontWeight: "800", color: "#EA580C" },
  streakLabel: { fontSize: 12, color: "#9A3412", marginTop: 2 },
  sideStats: { flex: 1, gap: 10 },
  sideCard: {
    flex: 1,
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 12,
    borderWidth: 1,
    borderColor: Colors.border,
    justifyContent: "center",
  },
  sideValue: { fontSize: 18, fontWeight: "700", color: Colors.text },
  sideLabel: { fontSize: 11, color: Colors.textSecondary, marginTop: 2 },

  section: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 14,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  sectionTitle: { fontSize: 15, fontWeight: "700", color: Colors.text, marginBottom: 12 },

  metricsGrid: { flexDirection: "row", flexWrap: "wrap", gap: 8, marginBottom: 14 },
  metricCard: {
    flexGrow: 1,
    flexBasis: "22%",
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 12,
    alignItems: "center",
    borderWidth: 1,
    borderColor: Colors.border,
  },
  metricValue: { fontSize: 20, fontWeight: "800", color: Colors.primary },
  metricLabel: { fontSize: 11, color: Colors.textSecondary, marginTop: 4, textAlign: "center" },

  progressCard: { marginBottom: 12 },
  progressHeader: { flexDirection: "row", justifyContent: "space-between", marginBottom: 6 },
  progressSubject: { fontSize: 14, fontWeight: "600", color: Colors.text },
  progressScore: { fontSize: 14, fontWeight: "800" },
  progressBarBg: { height: 8, backgroundColor: Colors.inputBg, borderRadius: 4, overflow: "hidden" },
  progressBarFill: { height: "100%", borderRadius: 4 },

  weakCard: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  weakTopic: { fontSize: 14, fontWeight: "600", color: Colors.text },
  weakSubject: { fontSize: 12, color: Colors.textSecondary, marginTop: 2 },
  weakArrow: { fontSize: 20, color: Colors.primary, marginLeft: 8 },

  empty: { alignItems: "center", paddingVertical: 40 },
  emptyIcon: { fontSize: 48, marginBottom: 12 },
  emptyTitle: { fontSize: 18, fontWeight: "600", color: Colors.text },
  emptyText: { fontSize: 14, color: Colors.textSecondary, marginTop: 4, textAlign: "center", paddingHorizontal: 40 },
});
