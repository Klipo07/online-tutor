// Главный экран — дашборд
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from "react-native";
import { useRouter } from "expo-router";
import { useAuthStore } from "../../store/authStore";
import { Colors } from "../../constants/theme";

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

export default function HomeScreen() {
  const user = useAuthStore((s) => s.user);
  const router = useRouter();

  return (
    <ScrollView style={styles.container}>
      <View style={styles.greeting}>
        <Text style={styles.greetingText}>
          Привет, {user?.full_name?.split(" ")[0] || "Ученик"}! 👋
        </Text>
        <Text style={styles.greetingSubtext}>Чему будем учиться сегодня?</Text>
      </View>

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
    paddingBottom: 16,
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
  quickActions: {
    flexDirection: "row",
    paddingHorizontal: 24,
    gap: 12,
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
    paddingBottom: 24,
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
});
