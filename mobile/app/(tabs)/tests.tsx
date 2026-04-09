// Экран тестов
import { useState } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
  ActivityIndicator,
} from "react-native";
import api from "../../services/api";
import { Colors } from "../../constants/theme";

type Question = {
  id: number;
  question: string;
  options: string[] | null;
  type: string;
};

type TestState = {
  test_id: number;
  questions: Question[];
};

export default function TestsScreen() {
  const [test, setTest] = useState<TestState | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);

  const subjects = [
    { name: "Математика", topic: "Квадратные уравнения" },
    { name: "Русский язык", topic: "Правописание" },
    { name: "Физика", topic: "Механика" },
    { name: "История", topic: "Великая Отечественная война" },
  ];

  const generateTest = async (subject: string, topic: string) => {
    setGenerating(true);
    setTest(null);
    setResult(null);
    setAnswers({});
    try {
      const res = await api.post("/ai/generate-test", {
        subject,
        topic,
        difficulty: "medium",
        num_questions: 5,
      });
      setTest({ test_id: res.data.test_id, questions: res.data.questions });
    } catch {
      Alert.alert("Ошибка", "Не удалось сгенерировать тест");
    } finally {
      setGenerating(false);
    }
  };

  const submitTest = async () => {
    if (!test) return;
    setLoading(true);
    try {
      const res = await api.post("/ai/submit-test", {
        test_id: test.test_id,
        answers,
      });
      setResult(res.data);
    } catch {
      Alert.alert("Ошибка", "Не удалось отправить ответы");
    } finally {
      setLoading(false);
    }
  };

  // Выбор предмета
  if (!test && !generating) {
    return (
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        <Text style={styles.title}>Выберите тест</Text>
        <Text style={styles.subtitle}>AI сгенерирует тест специально для вас</Text>

        {subjects.map((s) => (
          <TouchableOpacity
            key={s.name}
            style={styles.subjectCard}
            onPress={() => generateTest(s.name, s.topic)}
          >
            <Text style={styles.subjectName}>{s.name}</Text>
            <Text style={styles.subjectTopic}>{s.topic}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
    );
  }

  // Генерация
  if (generating) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color={Colors.primary} />
        <Text style={styles.loadingText}>AI генерирует тест...</Text>
      </View>
    );
  }

  // Результат
  if (result) {
    return (
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        <Text style={styles.title}>Результат</Text>
        <View style={styles.scoreCard}>
          <Text style={styles.scoreNumber}>{result.percentage}%</Text>
          <Text style={styles.scoreLabel}>
            {result.score} из {result.total} правильно
          </Text>
        </View>
        <Text style={styles.feedback}>{result.feedback}</Text>
        <TouchableOpacity
          style={styles.button}
          onPress={() => { setTest(null); setResult(null); setAnswers({}); }}
        >
          <Text style={styles.buttonText}>Пройти ещё тест</Text>
        </TouchableOpacity>
      </ScrollView>
    );
  }

  // Тест
  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Тест</Text>

      {test?.questions.map((q) => (
        <View key={q.id} style={styles.questionCard}>
          <Text style={styles.questionText}>
            {q.id}. {q.question}
          </Text>
          {q.options?.map((opt) => (
            <TouchableOpacity
              key={opt}
              style={[
                styles.optionButton,
                answers[String(q.id)] === opt && styles.optionSelected,
              ]}
              onPress={() =>
                setAnswers((prev) => ({ ...prev, [String(q.id)]: opt }))
              }
            >
              <Text
                style={[
                  styles.optionText,
                  answers[String(q.id)] === opt && styles.optionTextSelected,
                ]}
              >
                {opt}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      ))}

      <TouchableOpacity
        style={[styles.button, loading && styles.buttonDisabled]}
        onPress={submitTest}
        disabled={loading}
      >
        <Text style={styles.buttonText}>
          {loading ? "Проверяю..." : "Отправить ответы"}
        </Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  content: { padding: 24 },
  centered: { flex: 1, justifyContent: "center", alignItems: "center" },
  title: { fontSize: 24, fontWeight: "700", color: Colors.text, marginBottom: 8 },
  subtitle: { fontSize: 14, color: Colors.textSecondary, marginBottom: 20 },
  subjectCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  subjectName: { fontSize: 16, fontWeight: "600", color: Colors.text },
  subjectTopic: { fontSize: 13, color: Colors.textSecondary, marginTop: 4 },
  loadingText: { marginTop: 16, fontSize: 16, color: Colors.textSecondary },
  questionCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  questionText: { fontSize: 15, fontWeight: "600", color: Colors.text, marginBottom: 12 },
  optionButton: {
    backgroundColor: Colors.inputBg,
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
  },
  optionSelected: { backgroundColor: Colors.primary },
  optionText: { fontSize: 14, color: Colors.text },
  optionTextSelected: { color: "#fff", fontWeight: "600" },
  button: {
    backgroundColor: Colors.primary,
    borderRadius: 12,
    padding: 16,
    alignItems: "center",
    marginTop: 8,
    marginBottom: 24,
  },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { color: "#fff", fontSize: 16, fontWeight: "600" },
  scoreCard: {
    backgroundColor: Colors.primary,
    borderRadius: 16,
    padding: 24,
    alignItems: "center",
    marginVertical: 16,
  },
  scoreNumber: { fontSize: 48, fontWeight: "800", color: "#fff" },
  scoreLabel: { fontSize: 16, color: "rgba(255,255,255,0.9)", marginTop: 4 },
  feedback: { fontSize: 15, color: Colors.text, lineHeight: 22, marginBottom: 16 },
});
