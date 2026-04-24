// Дашборд репетитора — ближайшее занятие, заработок, ученики, отзывы
import { useCallback, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
} from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import api from "../services/api";
import { useAuthStore } from "../store/authStore";
import { Colors } from "../constants/theme";

type TutorStats = {
  students_count: number;
  sessions_completed: number;
  sessions_upcoming: number;
  earnings_month: number;
  rating: number;
  reviews_count: number;
  next_session_at: string | null;
  next_session_student: string | null;
  next_session_subject: string | null;
};

function formatWhen(iso: string): string {
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

export default function TutorDashboard() {
  const user = useAuthStore((s) => s.user);
  const isAuth = useAuthStore((s) => s.isAuth);
  const router = useRouter();
  const [stats, setStats] = useState<TutorStats | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    // Не дёргаем /tutors/me/* если уже разлогинились — экран может быть ещё
    // смонтирован в момент logout, 401 вылетел бы в глобальный interceptor
    if (!isAuth) return;
    try {
      const res = await api.get<TutorStats>("/tutors/me/stats");
      setStats(res.data);
    } catch {
      // Просто не показываем блок статистики при ошибке
    }
  }, [isAuth]);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load])
  );

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  }, [load]);

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      showsVerticalScrollIndicator={false}
    >
      <View style={styles.greeting}>
        <Text style={styles.greetingText}>
          Добро пожаловать, {user?.first_name || "репетитор"}! 👋
        </Text>
        <Text style={styles.greetingSubtext}>
          {stats && stats.sessions_upcoming > 0
            ? `У вас ${stats.sessions_upcoming} ${pluralRus(stats.sessions_upcoming, ["занятие", "занятия", "занятий"])} впереди`
            : "Проверяйте расписание и отзывы"}
        </Text>
      </View>

      {/* Ближайшее занятие */}
      {stats?.next_session_at && (
        <View style={styles.nextCard}>
          <View style={styles.nextHeader}>
            <Text style={styles.nextIcon}>📅</Text>
            <Text style={styles.nextLabel}>Ближайшее занятие</Text>
          </View>
          <Text style={styles.nextTime}>{formatWhen(stats.next_session_at)}</Text>
          <Text style={styles.nextSub}>
            {stats.next_session_student ?? "—"}
            {stats.next_session_subject ? ` · ${stats.next_session_subject}` : ""}
          </Text>
        </View>
      )}

      {/* Две карточки — заработок / рейтинг */}
      <View style={styles.statsRow}>
        <View style={[styles.statCard, styles.earningsCard]}>
          <Text style={styles.statEmoji}>💰</Text>
          <Text style={styles.statNumber}>
            {(stats?.earnings_month ?? 0).toLocaleString("ru-RU")} ₽
          </Text>
          <Text style={styles.statLabel}>за 30 дней</Text>
        </View>
        <View style={[styles.statCard, styles.ratingCard]}>
          <Text style={styles.statEmoji}>⭐</Text>
          <Text style={styles.statNumber}>
            {(stats?.rating ?? 0).toFixed(1)}
          </Text>
          <Text style={styles.statLabel}>
            {stats?.reviews_count ?? 0}{" "}
            {pluralRus(stats?.reviews_count ?? 0, ["отзыв", "отзыва", "отзывов"])}
          </Text>
        </View>
      </View>

      {/* Мини-статистика */}
      <View style={styles.miniStats}>
        <View style={styles.miniStat}>
          <Text style={styles.miniStatNum}>{stats?.students_count ?? 0}</Text>
          <Text style={styles.miniStatLabel}>учеников</Text>
        </View>
        <View style={styles.miniStat}>
          <Text style={styles.miniStatNum}>{stats?.sessions_completed ?? 0}</Text>
          <Text style={styles.miniStatLabel}>проведено</Text>
        </View>
        <View style={styles.miniStat}>
          <Text style={styles.miniStatNum}>{stats?.sessions_upcoming ?? 0}</Text>
          <Text style={styles.miniStatLabel}>впереди</Text>
        </View>
      </View>

      {/* Быстрые действия */}
      <View style={styles.quickActions}>
        <TouchableOpacity
          style={[styles.actionCard, { backgroundColor: Colors.primary }]}
          onPress={() => router.push("/(tabs)/t-schedule")}
        >
          <Text style={styles.actionIcon}>🕘</Text>
          <Text style={styles.actionTitle}>Моё расписание</Text>
          <Text style={styles.actionDesc}>Настроить рабочие часы</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.actionCard, { backgroundColor: Colors.secondary }]}
          onPress={() => router.push("/tutor-profile-edit")}
        >
          <Text style={styles.actionIcon}>✏️</Text>
          <Text style={styles.actionTitle}>Мой профиль</Text>
          <Text style={styles.actionDesc}>Предметы и цена</Text>
        </TouchableOpacity>
      </View>

      {/* CTA — посмотреть отзывы */}
      <TouchableOpacity
        style={styles.reviewsCard}
        onPress={() => router.push("/tutor-reviews")}
      >
        <View style={{ flex: 1 }}>
          <Text style={styles.reviewsTitle}>Отзывы обо мне</Text>
          <Text style={styles.reviewsSub}>
            {stats?.reviews_count
              ? `${stats.reviews_count} отзывов · средняя ${stats.rating.toFixed(1)}`
              : "Пока нет отзывов"}
          </Text>
        </View>
        <Text style={styles.reviewsArrow}>›</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

// Простое русское склонение для 1/2-4/5+
function pluralRus(n: number, forms: [string, string, string]): string {
  const abs = Math.abs(n) % 100;
  const n1 = abs % 10;
  if (abs > 10 && abs < 20) return forms[2];
  if (n1 > 1 && n1 < 5) return forms[1];
  if (n1 === 1) return forms[0];
  return forms[2];
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  greeting: { padding: 24, paddingBottom: 12 },
  greetingText: { fontSize: 24, fontWeight: "700", color: Colors.text },
  greetingSubtext: { fontSize: 15, color: Colors.textSecondary, marginTop: 4 },

  nextCard: {
    marginHorizontal: 24,
    marginBottom: 12,
    padding: 16,
    backgroundColor: Colors.primary,
    borderRadius: 16,
  },
  nextHeader: { flexDirection: "row", alignItems: "center", gap: 6 },
  nextIcon: { fontSize: 18 },
  nextLabel: { color: "rgba(255,255,255,0.85)", fontSize: 13, fontWeight: "600" },
  nextTime: { color: "#fff", fontSize: 20, fontWeight: "700", marginTop: 6 },
  nextSub: { color: "rgba(255,255,255,0.9)", fontSize: 14, marginTop: 2 },

  statsRow: { flexDirection: "row", paddingHorizontal: 24, gap: 12, marginBottom: 12 },
  statCard: { flex: 1, borderRadius: 16, padding: 14, minHeight: 110 },
  earningsCard: { backgroundColor: "#4CAF8F" },
  ratingCard: { backgroundColor: "#FFB84D" },
  statEmoji: { fontSize: 22 },
  statNumber: { fontSize: 22, fontWeight: "800", color: "#fff", marginTop: 4 },
  statLabel: { fontSize: 12, color: "rgba(255,255,255,0.85)", marginTop: 2 },

  miniStats: {
    flexDirection: "row",
    marginHorizontal: 24,
    backgroundColor: Colors.surface,
    borderRadius: 14,
    paddingVertical: 14,
    marginBottom: 12,
  },
  miniStat: { flex: 1, alignItems: "center" },
  miniStatNum: { fontSize: 18, fontWeight: "700", color: Colors.text },
  miniStatLabel: { fontSize: 12, color: Colors.textSecondary, marginTop: 2 },

  quickActions: { flexDirection: "row", paddingHorizontal: 24, gap: 12, marginTop: 4 },
  actionCard: { flex: 1, borderRadius: 16, padding: 16 },
  actionIcon: { fontSize: 28, marginBottom: 8 },
  actionTitle: { fontSize: 16, fontWeight: "700", color: "#fff" },
  actionDesc: { fontSize: 12, color: "rgba(255,255,255,0.8)", marginTop: 4 },

  reviewsCard: {
    flexDirection: "row",
    alignItems: "center",
    marginHorizontal: 24,
    marginTop: 16,
    marginBottom: 32,
    padding: 16,
    backgroundColor: Colors.surface,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  reviewsTitle: { fontSize: 15, fontWeight: "700", color: Colors.text },
  reviewsSub: { fontSize: 13, color: Colors.textSecondary, marginTop: 2 },
  reviewsArrow: { fontSize: 24, color: Colors.textSecondary },
});
