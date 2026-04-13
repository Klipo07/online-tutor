// Экран профиля, прогресса и аналитики
import { useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  Modal,
  ScrollView,
  ActivityIndicator,
} from "react-native";
import { useAuthStore } from "../../store/authStore";
import api from "../../services/api";
import { Colors } from "../../constants/theme";
import { Avatar } from "../../components/Avatar";

type Stats = {
  tests_completed: number;
  average_score: number;
  chat_sessions: number;
  lessons_completed: number;
  subjects_studied: number;
  total_study_time_minutes: number;
};

type ProgressItem = {
  subject_id: number;
  subject_name: string;
  score: number;
  weak_topics: string[];
  last_activity: string;
};

type Recommendation = {
  type: string;
  priority: string;
  message: string;
  action: string;
  subject?: string;
  topic?: string;
  score?: number;
};

type TestHistoryItem = {
  id: number;
  topic: string;
  difficulty: string;
  score: number;
  created_at: string;
};

export default function ProfileScreen() {
  const { user, logout } = useAuthStore();

  // Модальное окно прогресса
  const [showProgress, setShowProgress] = useState(false);
  const [stats, setStats] = useState<Stats | null>(null);
  const [progress, setProgress] = useState<ProgressItem[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [testHistory, setTestHistory] = useState<TestHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);

  const handleLogout = () => {
    Alert.alert("Выход", "Вы уверены, что хотите выйти?", [
      { text: "Отмена", style: "cancel" },
      { text: "Выйти", style: "destructive", onPress: logout },
    ]);
  };

  // Загрузка всех данных прогресса
  const openProgress = async () => {
    setShowProgress(true);
    setLoading(true);

    try {
      const [statsRes, progressRes, recsRes, historyRes] = await Promise.all([
        api.get("/users/me/stats"),
        api.get("/users/me/progress"),
        api.get("/ai/recommendations"),
        api.get("/users/me/test-history"),
      ]);

      setStats(statsRes.data);
      setProgress(progressRes.data.progress);
      setRecommendations(recsRes.data.recommendations);
      setTestHistory(historyRes.data.history);
    } catch {
      Alert.alert("Ошибка", "Не удалось загрузить данные прогресса");
    } finally {
      setLoading(false);
    }
  };

  // Цвет прогресс-бара по баллу
  const getScoreColor = (score: number) => {
    if (score >= 80) return Colors.success;
    if (score >= 60) return Colors.warning;
    return Colors.error;
  };

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr);
    return d.toLocaleDateString("ru-RU", {
      day: "numeric",
      month: "short",
    });
  };

  const difficultyLabel = (d: string) => {
    if (d === "easy") return "Легкий";
    if (d === "medium") return "Средний";
    return "Сложный";
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.avatarWrap}>
          <Avatar name={user?.full_name || "?"} size={72} fontSize={24} />
        </View>
        <Text style={styles.name}>{user?.full_name}</Text>
        <Text style={styles.email}>{user?.email}</Text>
        <View style={styles.badge}>
          <Text style={styles.badgeText}>
            {user?.role === "student" ? "Ученик" : user?.role === "tutor" ? "Репетитор" : user?.role}
          </Text>
        </View>
      </View>

      <View style={styles.section}>
        <TouchableOpacity style={styles.menuItem} onPress={openProgress}>
          <Text style={styles.menuIcon}>📊</Text>
          <Text style={styles.menuText}>Мой прогресс</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.menuItem}>
          <Text style={styles.menuIcon}>📅</Text>
          <Text style={styles.menuText}>Мои занятия</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.menuItem}>
          <Text style={styles.menuIcon}>⚙️</Text>
          <Text style={styles.menuText}>Настройки</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.menuItem}>
          <Text style={styles.menuIcon}>❓</Text>
          <Text style={styles.menuText}>Помощь</Text>
        </TouchableOpacity>
      </View>

      <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
        <Text style={styles.logoutText}>Выйти из аккаунта</Text>
      </TouchableOpacity>

      {/* Модальное окно — Прогресс и аналитика */}
      <Modal
        visible={showProgress}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setShowProgress(false)}
      >
        <ScrollView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Мой прогресс</Text>
            <TouchableOpacity onPress={() => setShowProgress(false)}>
              <Text style={styles.closeButton}>Закрыть</Text>
            </TouchableOpacity>
          </View>

          {loading ? (
            <View style={styles.centered}>
              <ActivityIndicator size="large" color={Colors.primary} />
              <Text style={styles.loadingText}>Загрузка аналитики...</Text>
            </View>
          ) : (
            <>
              {/* Общая статистика */}
              {stats && (
                <View style={styles.statsSection}>
                  <Text style={styles.sectionTitle}>Статистика</Text>
                  <View style={styles.statsGrid}>
                    <View style={styles.statCard}>
                      <Text style={styles.statValue}>{stats.tests_completed}</Text>
                      <Text style={styles.statLabel}>Тестов пройдено</Text>
                    </View>
                    <View style={styles.statCard}>
                      <Text style={styles.statValue}>{stats.average_score}%</Text>
                      <Text style={styles.statLabel}>Средний балл</Text>
                    </View>
                    <View style={styles.statCard}>
                      <Text style={styles.statValue}>{stats.chat_sessions}</Text>
                      <Text style={styles.statLabel}>AI-диалогов</Text>
                    </View>
                    <View style={styles.statCard}>
                      <Text style={styles.statValue}>{stats.lessons_completed}</Text>
                      <Text style={styles.statLabel}>Занятий</Text>
                    </View>
                    <View style={styles.statCard}>
                      <Text style={styles.statValue}>{stats.subjects_studied}</Text>
                      <Text style={styles.statLabel}>Предметов</Text>
                    </View>
                    <View style={styles.statCard}>
                      <Text style={styles.statValue}>{stats.total_study_time_minutes}</Text>
                      <Text style={styles.statLabel}>Минут обучения</Text>
                    </View>
                  </View>
                </View>
              )}

              {/* Прогресс по предметам */}
              {progress.length > 0 && (
                <View style={styles.progressSection}>
                  <Text style={styles.sectionTitle}>Прогресс по предметам</Text>
                  {progress.map((item) => (
                    <View key={item.subject_id} style={styles.progressCard}>
                      <View style={styles.progressHeader}>
                        <Text style={styles.progressSubject}>{item.subject_name}</Text>
                        <Text
                          style={[
                            styles.progressScore,
                            { color: getScoreColor(item.score) },
                          ]}
                        >
                          {item.score}%
                        </Text>
                      </View>
                      {/* Прогресс-бар */}
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
                      {item.weak_topics.length > 0 && (
                        <Text style={styles.weakTopics}>
                          Слабые темы: {item.weak_topics.join(", ")}
                        </Text>
                      )}
                      <Text style={styles.lastActivity}>
                        Последняя активность: {formatDate(item.last_activity)}
                      </Text>
                    </View>
                  ))}
                </View>
              )}

              {/* Рекомендации */}
              {recommendations.length > 0 && (
                <View style={styles.recsSection}>
                  <Text style={styles.sectionTitle}>Рекомендации</Text>
                  {recommendations.map((rec, i) => (
                    <View
                      key={i}
                      style={[
                        styles.recCard,
                        rec.priority === "high" && styles.recCardHigh,
                        rec.priority === "medium" && styles.recCardMedium,
                      ]}
                    >
                      <Text style={styles.recPriority}>
                        {rec.priority === "high" ? "!!!" : rec.priority === "medium" ? "!!" : "!"}
                      </Text>
                      <View style={styles.recContent}>
                        <Text style={styles.recMessage}>{rec.message}</Text>
                        <Text style={styles.recAction}>{rec.action}</Text>
                      </View>
                    </View>
                  ))}
                </View>
              )}

              {/* История тестов */}
              {testHistory.length > 0 && (
                <View style={styles.historySection}>
                  <Text style={styles.sectionTitle}>История тестов</Text>
                  {testHistory.map((item) => (
                    <View key={item.id} style={styles.historyCard}>
                      <View style={styles.historyLeft}>
                        <Text style={styles.historyTopic}>{item.topic}</Text>
                        <Text style={styles.historyMeta}>
                          {difficultyLabel(item.difficulty)} · {formatDate(item.created_at)}
                        </Text>
                      </View>
                      <Text
                        style={[
                          styles.historyScore,
                          { color: getScoreColor(item.score) },
                        ]}
                      >
                        {item.score}%
                      </Text>
                    </View>
                  ))}
                </View>
              )}

              {/* Пустое состояние */}
              {progress.length === 0 && testHistory.length === 0 && (
                <View style={styles.emptyState}>
                  <Text style={styles.emptyIcon}>📊</Text>
                  <Text style={styles.emptyTitle}>Пока нет данных</Text>
                  <Text style={styles.emptySubtext}>
                    Пройдите тест или пообщайтесь с AI-тьютором, чтобы увидеть прогресс
                  </Text>
                </View>
              )}
            </>
          )}
        </ScrollView>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  header: {
    alignItems: "center",
    paddingVertical: 32,
    backgroundColor: Colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  avatarWrap: { marginBottom: 12 },
  name: { fontSize: 20, fontWeight: "700", color: Colors.text },
  email: { fontSize: 14, color: Colors.textSecondary, marginTop: 4 },
  badge: {
    backgroundColor: Colors.primary + "20",
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
    marginTop: 8,
  },
  badgeText: { color: Colors.primary, fontSize: 12, fontWeight: "600" },
  section: { marginTop: 16 },
  menuItem: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: Colors.surface,
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  menuIcon: { fontSize: 20, marginRight: 12 },
  menuText: { fontSize: 16, color: Colors.text },
  logoutButton: {
    margin: 24,
    padding: 16,
    borderRadius: 12,
    backgroundColor: Colors.error + "10",
    alignItems: "center",
  },
  logoutText: { color: Colors.error, fontSize: 16, fontWeight: "600" },

  // Модальное окно
  modalContainer: { flex: 1, backgroundColor: Colors.background },
  modalHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    padding: 16,
    backgroundColor: Colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  modalTitle: { fontSize: 20, fontWeight: "700", color: Colors.text },
  closeButton: { fontSize: 16, color: Colors.primary, fontWeight: "600" },

  centered: { paddingVertical: 60, alignItems: "center" },
  loadingText: { marginTop: 12, color: Colors.textSecondary },

  // Статистика
  statsSection: { padding: 16 },
  sectionTitle: { fontSize: 17, fontWeight: "700", color: Colors.text, marginBottom: 12 },
  statsGrid: { flexDirection: "row", flexWrap: "wrap", gap: 10 },
  statCard: {
    width: "31%",
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 14,
    alignItems: "center",
    borderWidth: 1,
    borderColor: Colors.border,
  },
  statValue: { fontSize: 22, fontWeight: "800", color: Colors.primary },
  statLabel: { fontSize: 11, color: Colors.textSecondary, marginTop: 4, textAlign: "center" },

  // Прогресс по предметам
  progressSection: { padding: 16, paddingTop: 0 },
  progressCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  progressHeader: { flexDirection: "row", justifyContent: "space-between", marginBottom: 8 },
  progressSubject: { fontSize: 15, fontWeight: "600", color: Colors.text },
  progressScore: { fontSize: 16, fontWeight: "800" },
  progressBarBg: {
    height: 8,
    backgroundColor: Colors.inputBg,
    borderRadius: 4,
    overflow: "hidden",
  },
  progressBarFill: { height: "100%", borderRadius: 4 },
  weakTopics: { fontSize: 12, color: Colors.error, marginTop: 8 },
  lastActivity: { fontSize: 11, color: Colors.textSecondary, marginTop: 4 },

  // Рекомендации
  recsSection: { padding: 16, paddingTop: 0 },
  recCard: {
    flexDirection: "row",
    backgroundColor: Colors.surface,
    borderRadius: 10,
    padding: 14,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  recCardHigh: { borderLeftWidth: 4, borderLeftColor: Colors.error },
  recCardMedium: { borderLeftWidth: 4, borderLeftColor: Colors.warning },
  recPriority: { fontSize: 14, marginRight: 10, color: Colors.error, fontWeight: "700" },
  recContent: { flex: 1 },
  recMessage: { fontSize: 14, fontWeight: "600", color: Colors.text },
  recAction: { fontSize: 12, color: Colors.textSecondary, marginTop: 4 },

  // История тестов
  historySection: { padding: 16, paddingTop: 0, paddingBottom: 40 },
  historyCard: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    backgroundColor: Colors.surface,
    borderRadius: 10,
    padding: 14,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  historyLeft: { flex: 1 },
  historyTopic: { fontSize: 14, fontWeight: "600", color: Colors.text },
  historyMeta: { fontSize: 12, color: Colors.textSecondary, marginTop: 2 },
  historyScore: { fontSize: 18, fontWeight: "800", marginLeft: 12 },

  // Пустое состояние
  emptyState: { alignItems: "center", paddingVertical: 60 },
  emptyIcon: { fontSize: 48, marginBottom: 12 },
  emptyTitle: { fontSize: 18, fontWeight: "600", color: Colors.text },
  emptySubtext: { fontSize: 14, color: Colors.textSecondary, marginTop: 4, textAlign: "center", paddingHorizontal: 40 },
});
