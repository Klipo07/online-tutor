// Главный экран — дашборд с streak, целью дня и предстоящим занятием
import { useCallback, useEffect, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  RefreshControl,
} from "react-native";
import { useRouter, useFocusEffect } from "expo-router";
import { useAuthStore } from "../../store/authStore";
import { Colors } from "../../constants/theme";
import api from "../../services/api";
import { EmailVerifyBanner } from "../../components/EmailVerifyBanner";

// Дата выпуска ЕГЭ (примерно 27 мая) — используем для отсчёта дней до экзамена
const EGE_DATE_ISO = "2026-05-27T09:00:00Z";

// Советы дня — простой локальный пул; потом можно заменить на AI-генерацию
const DAILY_TIPS = [
  "Учись каждый день по чуть-чуть — регулярность важнее количества.",
  "Пересказ — лучший способ проверить, понял ли ты тему.",
  "Сон после учёбы помогает запомнить в 2 раза больше.",
  "Объясни тему другу — если можешь объяснить, значит, знаешь.",
  "Сложные темы дели на 3–4 подтемы и учи по одной.",
  "Отдыхай каждые 45 минут — мозг работает циклами.",
  "Задай AI-тьютору вопрос, даже если кажется глупым — так и учимся.",
];

const subjects = [
  { name: "Математика", icon: "📐" },
  { name: "Русский язык", icon: "📖" },
  { name: "Физика", icon: "⚡" },
  { name: "Химия", icon: "🧪" },
  { name: "Биология", icon: "🧬" },
  { name: "История", icon: "🏛️" },
  { name: "Английский", icon: "🇬🇧" },
  { name: "Информатика", icon: "💻" },
];

type UpcomingSession = {
  id: number;
  scheduled_at: string;
  subject: string | null;
  tutor_name: string | null;
  duration_minutes: number;
};

type Stats = {
  tests_completed: number;
  average_score: number;
  chat_sessions: number;
  lessons_completed: number;
  subjects_studied: number;
  total_study_time_minutes: number;
  streak_days: number;
  active_days_this_week: number;
  upcoming_session: UpcomingSession | null;
};

// Недельная цель — 5 активных дней
const WEEKLY_GOAL = 5;

function daysUntilEge(): number {
  const diff = new Date(EGE_DATE_ISO).getTime() - Date.now();
  return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
}

function formatUpcoming(iso: string): string {
  const d = new Date(iso);
  const today = new Date();
  const tomorrow = new Date();
  tomorrow.setDate(today.getDate() + 1);

  const sameDay = (a: Date, b: Date) =>
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate();

  const time = d.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" });
  if (sameDay(d, today)) return `Сегодня в ${time}`;
  if (sameDay(d, tomorrow)) return `Завтра в ${time}`;
  return d.toLocaleDateString("ru-RU", { day: "numeric", month: "long" }) + ` в ${time}`;
}

export default function HomeScreen() {
  const user = useAuthStore((s) => s.user);
  const router = useRouter();
  const [stats, setStats] = useState<Stats | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const tip = DAILY_TIPS[new Date().getDate() % DAILY_TIPS.length];
  const egeDays = daysUntilEge();

  const loadStats = useCallback(async () => {
    try {
      const res = await api.get<Stats>("/users/me/stats");
      setStats(res.data);
    } catch {
      // Не блокируем экран — просто не показываем блок статистики
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      loadStats();
    }, [loadStats])
  );

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadStats();
    setRefreshing(false);
  }, [loadStats]);

  const streak = stats?.streak_days ?? 0;
  const weekProgress = Math.min(1, (stats?.active_days_this_week ?? 0) / WEEKLY_GOAL);

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      showsVerticalScrollIndicator={false}
    >
      <EmailVerifyBanner />

      <View style={styles.greeting}>
        <Text style={styles.greetingText}>
          Привет, {user?.full_name?.split(" ")[0] || "Ученик"}! 👋
        </Text>
        <Text style={styles.greetingSubtext}>Чему будем учиться сегодня?</Text>
      </View>

      {/* Streak + цель недели */}
      <View style={styles.statsRow}>
        <View style={[styles.statCard, styles.streakCard]}>
          <Text style={styles.streakEmoji}>🔥</Text>
          <Text style={styles.statNumber}>{streak}</Text>
          <Text style={styles.statLabel}>
            {streak === 0 ? "Начни сегодня!" : "дней подряд"}
          </Text>
        </View>
        <View style={[styles.statCard, styles.goalCard]}>
          <Text style={styles.statSmallLabel}>Цель недели</Text>
          <Text style={styles.statNumber}>
            {stats?.active_days_this_week ?? 0}/{WEEKLY_GOAL}
          </Text>
          <View style={styles.progressTrack}>
            <View style={[styles.progressFill, { width: `${weekProgress * 100}%` }]} />
          </View>
          <Text style={styles.statLabel}>активных дней</Text>
        </View>
      </View>

      {/* Предстоящее занятие */}
      {stats?.upcoming_session && (
        <TouchableOpacity
          style={styles.upcomingCard}
          activeOpacity={0.85}
          onPress={() => router.push(`/session/${stats.upcoming_session!.id}`)}
        >
          <View style={styles.upcomingHeader}>
            <Text style={styles.upcomingIcon}>📅</Text>
            <Text style={styles.upcomingLabel}>Ближайшее занятие</Text>
          </View>
          <Text style={styles.upcomingTime}>
            {formatUpcoming(stats.upcoming_session.scheduled_at)}
          </Text>
          <Text style={styles.upcomingSubject}>
            {stats.upcoming_session.subject ?? "Занятие"}
            {stats.upcoming_session.tutor_name
              ? ` · ${stats.upcoming_session.tutor_name}`
              : ""}
          </Text>
        </TouchableOpacity>
      )}

      {/* Отсчёт до ЕГЭ */}
      {egeDays > 0 && egeDays <= 180 && (
        <View style={styles.egeCard}>
          <Text style={styles.egeTitle}>До ЕГЭ осталось</Text>
          <Text style={styles.egeDays}>{egeDays} {egeDays === 1 ? "день" : "дней"}</Text>
          <Text style={styles.egeSubtitle}>Готовимся каждый день — и всё получится 🚀</Text>
        </View>
      )}

      {/* Быстрые действия */}
      <View style={styles.quickActions}>
        <TouchableOpacity
          style={[styles.actionCard, { backgroundColor: Colors.primary }]}
          onPress={() => router.push("/(tabs)/chat")}
        >
          <Text style={styles.actionIcon}>💬</Text>
          <Text style={styles.actionTitle}>AI Тьютор</Text>
          <Text style={styles.actionDesc}>Задай вопрос по любой теме</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.actionCard, { backgroundColor: Colors.secondary }]}
          onPress={() => router.push("/(tabs)/tests")}
        >
          <Text style={styles.actionIcon}>📝</Text>
          <Text style={styles.actionTitle}>Пройти тест</Text>
          <Text style={styles.actionDesc}>Проверь свои знания</Text>
        </TouchableOpacity>
      </View>

      {/* Мини-статистика */}
      {stats && (
        <View style={styles.miniStatsRow}>
          <View style={styles.miniStat}>
            <Text style={styles.miniStatNum}>{stats.tests_completed}</Text>
            <Text style={styles.miniStatLabel}>тестов</Text>
          </View>
          <View style={styles.miniStat}>
            <Text style={styles.miniStatNum}>{stats.average_score}%</Text>
            <Text style={styles.miniStatLabel}>средний балл</Text>
          </View>
          <View style={styles.miniStat}>
            <Text style={styles.miniStatNum}>{stats.lessons_completed}</Text>
            <Text style={styles.miniStatLabel}>занятий</Text>
          </View>
        </View>
      )}

      {/* Предметы */}
      <Text style={styles.sectionTitle}>Предметы</Text>
      <View style={styles.subjectsGrid}>
        {subjects.map((s) => (
          <TouchableOpacity
            key={s.name}
            style={styles.subjectCard}
            onPress={() => router.push({ pathname: "/(tabs)/chat", params: { subject: s.name } })}
          >
            <Text style={styles.subjectIcon}>{s.icon}</Text>
            <Text style={styles.subjectName}>{s.name}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Совет дня */}
      <View style={styles.tipCard}>
        <Text style={styles.tipHeader}>💡 Совет дня</Text>
        <Text style={styles.tipText}>{tip}</Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  greeting: {
    padding: 24,
    paddingBottom: 12,
  },
  greetingText: {
    fontSize: 24,
    fontWeight: "700",
    color: Colors.text,
  },
  greetingSubtext: {
    fontSize: 15,
    color: Colors.textSecondary,
    marginTop: 4,
  },
  statsRow: {
    flexDirection: "row",
    paddingHorizontal: 24,
    gap: 12,
    marginBottom: 12,
  },
  statCard: {
    flex: 1,
    borderRadius: 16,
    padding: 14,
    minHeight: 110,
  },
  streakCard: {
    backgroundColor: "#FF6A3D",
  },
  goalCard: {
    backgroundColor: "#4CAF8F",
  },
  streakEmoji: {
    fontSize: 24,
  },
  statNumber: {
    fontSize: 28,
    fontWeight: "800",
    color: "#fff",
    marginTop: 4,
  },
  statLabel: {
    fontSize: 12,
    color: "rgba(255,255,255,0.85)",
    marginTop: 2,
  },
  statSmallLabel: {
    fontSize: 12,
    fontWeight: "600",
    color: "rgba(255,255,255,0.85)",
  },
  progressTrack: {
    height: 6,
    backgroundColor: "rgba(255,255,255,0.3)",
    borderRadius: 3,
    overflow: "hidden",
    marginTop: 6,
  },
  progressFill: {
    height: "100%",
    backgroundColor: "#fff",
  },
  upcomingCard: {
    marginHorizontal: 24,
    marginBottom: 12,
    padding: 16,
    backgroundColor: Colors.primary,
    borderRadius: 16,
  },
  upcomingHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  upcomingIcon: {
    fontSize: 18,
  },
  upcomingLabel: {
    color: "rgba(255,255,255,0.85)",
    fontSize: 13,
    fontWeight: "600",
  },
  upcomingTime: {
    color: "#fff",
    fontSize: 20,
    fontWeight: "700",
    marginTop: 6,
  },
  upcomingSubject: {
    color: "rgba(255,255,255,0.9)",
    fontSize: 14,
    marginTop: 2,
  },
  egeCard: {
    marginHorizontal: 24,
    marginBottom: 12,
    padding: 14,
    backgroundColor: Colors.surface,
    borderLeftWidth: 4,
    borderLeftColor: "#E91E63",
    borderRadius: 12,
  },
  egeTitle: {
    fontSize: 12,
    color: Colors.textSecondary,
    fontWeight: "600",
  },
  egeDays: {
    fontSize: 22,
    fontWeight: "800",
    color: "#E91E63",
    marginTop: 2,
  },
  egeSubtitle: {
    fontSize: 13,
    color: Colors.text,
    marginTop: 4,
  },
  quickActions: {
    flexDirection: "row",
    paddingHorizontal: 24,
    gap: 12,
    marginTop: 4,
  },
  actionCard: {
    flex: 1,
    borderRadius: 16,
    padding: 16,
  },
  actionIcon: {
    fontSize: 28,
    marginBottom: 8,
  },
  actionTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: "#fff",
  },
  actionDesc: {
    fontSize: 12,
    color: "rgba(255,255,255,0.8)",
    marginTop: 4,
  },
  miniStatsRow: {
    flexDirection: "row",
    marginTop: 16,
    marginHorizontal: 24,
    backgroundColor: Colors.surface,
    borderRadius: 14,
    paddingVertical: 14,
  },
  miniStat: {
    flex: 1,
    alignItems: "center",
  },
  miniStatNum: {
    fontSize: 18,
    fontWeight: "700",
    color: Colors.text,
  },
  miniStatLabel: {
    fontSize: 12,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: Colors.text,
    paddingHorizontal: 24,
    paddingTop: 24,
    paddingBottom: 12,
  },
  subjectsGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    paddingHorizontal: 18,
    paddingBottom: 16,
  },
  subjectCard: {
    width: "25%",
    alignItems: "center",
    padding: 12,
  },
  subjectIcon: {
    fontSize: 32,
    marginBottom: 6,
  },
  subjectName: {
    fontSize: 12,
    color: Colors.text,
    textAlign: "center",
  },
  tipCard: {
    marginHorizontal: 24,
    marginBottom: 32,
    padding: 16,
    backgroundColor: Colors.surface,
    borderRadius: 14,
  },
  tipHeader: {
    fontSize: 13,
    fontWeight: "700",
    color: Colors.primary,
    marginBottom: 6,
  },
  tipText: {
    fontSize: 14,
    color: Colors.text,
    lineHeight: 20,
  },
});
