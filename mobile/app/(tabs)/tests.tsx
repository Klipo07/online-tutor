// Банк тестов — ЕГЭ / ОГЭ / Обычные. Каскадный выбор + прохождение.
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
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

type FeedbackRating = "too_easy" | "ok" | "too_hard";

type ExamType = "ege" | "oge" | "regular";
type Difficulty = "easy" | "medium" | "hard";

type SubjectItem = { id: number; name: string; tests_count: number };
type TaskNumberItem = { task_number: number; count: number };
type TestListItem = {
  id: number;
  subject_id: number;
  topic: string;
  exam_type: ExamType;
  task_number: number | null;
  difficulty: Difficulty;
  questions_count: number;
};
type Question = {
  id: number;
  question: string;
  options: string[] | null;
  type: string;
};
type FullTest = {
  id: number;
  subject_id: number;
  topic: string;
  exam_type: ExamType;
  task_number: number | null;
  difficulty: Difficulty;
  questions: Question[];
};

type Stage =
  | "exam"
  | "subject"
  | "task"
  | "difficulty"
  | "list"
  | "loading"
  | "running"
  | "result";

const EXAM_LABELS: Record<ExamType, string> = {
  ege: "ЕГЭ",
  oge: "ОГЭ",
  regular: "Обычный",
};

const DIFFICULTY_LABELS: Record<Difficulty, string> = {
  easy: "Лёгкий",
  medium: "Средний",
  hard: "Сложный",
};

export default function TestsScreen() {
  const [stage, setStage] = useState<Stage>("exam");

  const [examType, setExamType] = useState<ExamType | null>(null);
  const [subject, setSubject] = useState<SubjectItem | null>(null);
  const [taskNumber, setTaskNumber] = useState<number | null>(null);
  const [difficulty, setDifficulty] = useState<Difficulty | null>(null);

  const [subjects, setSubjects] = useState<SubjectItem[]>([]);
  const [taskNumbers, setTaskNumbers] = useState<TaskNumberItem[]>([]);
  const [tests, setTests] = useState<TestListItem[]>([]);

  const [currentTest, setCurrentTest] = useState<FullTest | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [result, setResult] = useState<any>(null);

  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Таймер прохождения: startedAt — момент входа, elapsed — для отображения
  const startedAtRef = useRef<number | null>(null);
  const [elapsedSec, setElapsedSec] = useState(0);

  // Фидбек по сложности теста
  const [feedbackSent, setFeedbackSent] = useState<FeedbackRating | null>(null);
  const [sendingFeedback, setSendingFeedback] = useState(false);

  // Тикаем секунды, пока идёт тест
  useEffect(() => {
    if (stage !== "running") return;
    const interval = setInterval(() => {
      if (startedAtRef.current !== null) {
        setElapsedSec(Math.floor((Date.now() - startedAtRef.current) / 1000));
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [stage]);

  const resetAll = useCallback(() => {
    setStage("exam");
    setExamType(null);
    setSubject(null);
    setTaskNumber(null);
    setDifficulty(null);
    setSubjects([]);
    setTaskNumbers([]);
    setTests([]);
    setCurrentTest(null);
    setAnswers({});
    setResult(null);
    setElapsedSec(0);
    setFeedbackSent(null);
    startedAtRef.current = null;
  }, []);

  const goBack = useCallback(() => {
    if (stage === "subject") {
      setStage("exam");
      setExamType(null);
    } else if (stage === "task") {
      setStage("subject");
      setSubject(null);
    } else if (stage === "difficulty") {
      setStage("task");
      setTaskNumber(null);
    } else if (stage === "list") {
      setStage("difficulty");
      setDifficulty(null);
    } else if (stage === "running" || stage === "result") {
      setCurrentTest(null);
      setAnswers({});
      setResult(null);
      setStage("list");
    }
  }, [stage]);

  // Шаг: Выбор экзамена → загрузка предметов
  const pickExam = useCallback(async (type: ExamType) => {
    setExamType(type);
    setLoading(true);
    try {
      const res = await api.get("/tests/subjects-with-tests", {
        params: { exam_type: type },
      });
      setSubjects(res.data);
      setStage("subject");
    } catch {
      Alert.alert("Ошибка", "Не удалось загрузить предметы");
      setExamType(null);
    } finally {
      setLoading(false);
    }
  }, []);

  // Шаг: Выбор предмета → загрузка номеров заданий
  const pickSubject = useCallback(
    async (s: SubjectItem) => {
      if (!examType) return;
      setSubject(s);
      setLoading(true);
      try {
        const res = await api.get("/tests/task-numbers", {
          params: { subject_id: s.id, exam_type: examType },
        });
        setTaskNumbers(res.data);
        setStage("task");
      } catch {
        Alert.alert("Ошибка", "Не удалось загрузить задания");
        setSubject(null);
      } finally {
        setLoading(false);
      }
    },
    [examType]
  );

  // Шаг: Выбор задания → переход к сложности
  const pickTaskNumber = useCallback((n: number | null) => {
    setTaskNumber(n);
    setStage("difficulty");
  }, []);

  // Шаг: Выбор сложности → загрузка тестов
  const pickDifficulty = useCallback(
    async (d: Difficulty | null) => {
      if (!examType || !subject) return;
      setDifficulty(d);
      setLoading(true);
      try {
        const params: Record<string, any> = {
          subject_id: subject.id,
          exam_type: examType,
          limit: 50,
        };
        if (taskNumber !== null) params.task_number = taskNumber;
        if (d) params.difficulty = d;

        const res = await api.get("/tests", { params });
        setTests(res.data);
        setStage("list");
      } catch {
        Alert.alert("Ошибка", "Не удалось загрузить тесты");
        setDifficulty(null);
      } finally {
        setLoading(false);
      }
    },
    [examType, subject, taskNumber]
  );

  // Открыть тест → загрузить вопросы
  const openTest = useCallback(async (t: TestListItem) => {
    setLoading(true);
    setStage("loading");
    try {
      const res = await api.get(`/tests/${t.id}`);
      setCurrentTest(res.data);
      setAnswers({});
      setFeedbackSent(null);
      setElapsedSec(0);
      startedAtRef.current = Date.now();
      setStage("running");
    } catch {
      Alert.alert("Ошибка", "Не удалось загрузить тест");
      setStage("list");
    } finally {
      setLoading(false);
    }
  }, []);

  const submitTest = useCallback(async () => {
    if (!currentTest) return;
    setSubmitting(true);
    const timeSpent =
      startedAtRef.current !== null
        ? Math.floor((Date.now() - startedAtRef.current) / 1000)
        : null;
    try {
      const res = await api.post("/ai/submit-test", {
        test_id: currentTest.id,
        answers,
        time_spent_seconds: timeSpent,
      });
      setResult(res.data);
      setStage("result");
    } catch {
      Alert.alert("Ошибка", "Не удалось отправить ответы");
    } finally {
      setSubmitting(false);
    }
  }, [currentTest, answers]);

  const sendFeedback = useCallback(
    async (rating: FeedbackRating) => {
      if (!currentTest || feedbackSent || sendingFeedback) return;
      setSendingFeedback(true);
      try {
        await api.post(`/tests/${currentTest.id}/feedback`, { rating });
        setFeedbackSent(rating);
      } catch {
        Alert.alert("Ошибка", "Не удалось отправить отзыв");
      } finally {
        setSendingFeedback(false);
      }
    },
    [currentTest, feedbackSent, sendingFeedback]
  );

  const breadcrumb = useMemo(() => {
    const parts: string[] = [];
    if (examType) parts.push(EXAM_LABELS[examType]);
    if (subject) parts.push(subject.name);
    if (taskNumber !== null) parts.push(`№${taskNumber}`);
    if (difficulty) parts.push(DIFFICULTY_LABELS[difficulty]);
    return parts.join(" · ");
  }, [examType, subject, taskNumber, difficulty]);

  if (loading && stage !== "running") {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color={Colors.primary} />
      </View>
    );
  }

  // === Шаг 1: Выбор формата ===
  if (stage === "exam") {
    return (
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        <Text style={styles.title}>Банк тестов</Text>
        <Text style={styles.subtitle}>Выберите формат экзамена</Text>

        {(["ege", "oge", "regular"] as ExamType[]).map((t) => (
          <TouchableOpacity
            key={t}
            style={styles.bigCard}
            onPress={() => pickExam(t)}
          >
            <Text style={styles.bigCardTitle}>{EXAM_LABELS[t]}</Text>
            <Text style={styles.bigCardHint}>
              {t === "ege"
                ? "Единый государственный экзамен"
                : t === "oge"
                ? "Основной государственный экзамен"
                : "Тренировочные задания"}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
    );
  }

  // === Шаг 2: Выбор предмета ===
  if (stage === "subject") {
    return (
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        <TouchableOpacity onPress={goBack}>
          <Text style={styles.backLink}>← Назад</Text>
        </TouchableOpacity>
        <Text style={styles.crumb}>{breadcrumb}</Text>
        <Text style={styles.title}>Предмет</Text>

        {subjects.length === 0 ? (
          <Text style={styles.empty}>
            Пока нет тестов. Попробуйте другой формат.
          </Text>
        ) : (
          subjects.map((s) => (
            <TouchableOpacity
              key={s.id}
              style={styles.row}
              onPress={() => pickSubject(s)}
            >
              <Text style={styles.rowTitle}>{s.name}</Text>
              <Text style={styles.rowHint}>{s.tests_count} тестов</Text>
            </TouchableOpacity>
          ))
        )}
      </ScrollView>
    );
  }

  // === Шаг 3: Номер задания ===
  if (stage === "task") {
    return (
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        <TouchableOpacity onPress={goBack}>
          <Text style={styles.backLink}>← Назад</Text>
        </TouchableOpacity>
        <Text style={styles.crumb}>{breadcrumb}</Text>
        <Text style={styles.title}>Номер задания</Text>

        <TouchableOpacity style={styles.row} onPress={() => pickTaskNumber(null)}>
          <Text style={styles.rowTitle}>Любое задание</Text>
          <Text style={styles.rowHint}>Все доступные номера</Text>
        </TouchableOpacity>

        {taskNumbers.map((t) => (
          <TouchableOpacity
            key={t.task_number}
            style={styles.row}
            onPress={() => pickTaskNumber(t.task_number)}
          >
            <Text style={styles.rowTitle}>Задание №{t.task_number}</Text>
            <Text style={styles.rowHint}>{t.count} тестов</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
    );
  }

  // === Шаг 4: Сложность ===
  if (stage === "difficulty") {
    return (
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        <TouchableOpacity onPress={goBack}>
          <Text style={styles.backLink}>← Назад</Text>
        </TouchableOpacity>
        <Text style={styles.crumb}>{breadcrumb}</Text>
        <Text style={styles.title}>Сложность</Text>

        <TouchableOpacity style={styles.row} onPress={() => pickDifficulty(null)}>
          <Text style={styles.rowTitle}>Любая</Text>
        </TouchableOpacity>
        {(["easy", "medium", "hard"] as Difficulty[]).map((d) => (
          <TouchableOpacity
            key={d}
            style={styles.row}
            onPress={() => pickDifficulty(d)}
          >
            <Text style={styles.rowTitle}>{DIFFICULTY_LABELS[d]}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
    );
  }

  // === Шаг 5: Список тестов ===
  if (stage === "list") {
    return (
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        <TouchableOpacity onPress={goBack}>
          <Text style={styles.backLink}>← Назад</Text>
        </TouchableOpacity>
        <Text style={styles.crumb}>{breadcrumb}</Text>
        <Text style={styles.title}>Тесты ({tests.length})</Text>

        {tests.length === 0 ? (
          <>
            <Text style={styles.empty}>
              Нет тестов под эти фильтры. Попробуйте другую сложность или номер задания.
            </Text>
            <TouchableOpacity style={styles.secondaryBtn} onPress={resetAll}>
              <Text style={styles.secondaryBtnText}>Начать сначала</Text>
            </TouchableOpacity>
          </>
        ) : (
          tests.map((t) => (
            <TouchableOpacity
              key={t.id}
              style={styles.row}
              onPress={() => openTest(t)}
            >
              <Text style={styles.rowTitle}>{t.topic}</Text>
              <Text style={styles.rowHint}>
                {t.task_number ? `№${t.task_number} · ` : ""}
                {DIFFICULTY_LABELS[t.difficulty]} · {t.questions_count} вопросов
              </Text>
            </TouchableOpacity>
          ))
        )}
      </ScrollView>
    );
  }

  // === Загрузка теста ===
  if (stage === "loading") {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color={Colors.primary} />
        <Text style={styles.loadingText}>Загрузка теста...</Text>
      </View>
    );
  }

  // === Прохождение теста ===
  if (stage === "running" && currentTest) {
    const allAnswered =
      Object.keys(answers).length === currentTest.questions.length;
    const mm = String(Math.floor(elapsedSec / 60)).padStart(2, "0");
    const ss = String(elapsedSec % 60).padStart(2, "0");
    return (
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        <View style={styles.runningHeader}>
          <TouchableOpacity onPress={goBack}>
            <Text style={styles.backLink}>← Выйти</Text>
          </TouchableOpacity>
          <View style={styles.timerBadge}>
            <Text style={styles.timerText}>⏱ {mm}:{ss}</Text>
          </View>
        </View>
        <Text style={styles.crumb}>{breadcrumb}</Text>
        <Text style={styles.title}>{currentTest.topic}</Text>

        {currentTest.questions.map((q) => (
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
          style={[
            styles.button,
            (submitting || !allAnswered) && styles.buttonDisabled,
          ]}
          onPress={submitTest}
          disabled={submitting || !allAnswered}
        >
          <Text style={styles.buttonText}>
            {submitting
              ? "Проверяю..."
              : allAnswered
              ? "Отправить ответы"
              : `Ответьте на все вопросы (${Object.keys(answers).length}/${currentTest.questions.length})`}
          </Text>
        </TouchableOpacity>
      </ScrollView>
    );
  }

  // === Результат ===
  if (stage === "result" && result) {
    const totalMin = Math.floor(elapsedSec / 60);
    const totalSec = elapsedSec % 60;
    return (
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        <Text style={styles.title}>Результат</Text>
        <View style={styles.scoreCard}>
          <Text style={styles.scoreNumber}>{result.percentage}%</Text>
          <Text style={styles.scoreLabel}>
            {result.score} из {result.total} правильно
          </Text>
          {elapsedSec > 0 && (
            <Text style={styles.scoreTime}>
              Время: {totalMin} мин {totalSec} с
            </Text>
          )}
        </View>
        <Text style={styles.feedback}>{result.feedback}</Text>

        <View style={styles.feedbackBlock}>
          <Text style={styles.feedbackTitle}>Насколько был сложным тест?</Text>
          {feedbackSent ? (
            <Text style={styles.feedbackThanks}>Спасибо, отзыв учтён!</Text>
          ) : (
            <View style={styles.feedbackRow}>
              {(
                [
                  { key: "too_easy", emoji: "😊", label: "Легко" },
                  { key: "ok", emoji: "👌", label: "В самый раз" },
                  { key: "too_hard", emoji: "😅", label: "Сложно" },
                ] as { key: FeedbackRating; emoji: string; label: string }[]
              ).map((opt) => (
                <TouchableOpacity
                  key={opt.key}
                  style={styles.feedbackBtn}
                  onPress={() => sendFeedback(opt.key)}
                  disabled={sendingFeedback}
                >
                  <Text style={styles.feedbackEmoji}>{opt.emoji}</Text>
                  <Text style={styles.feedbackLabel}>{opt.label}</Text>
                </TouchableOpacity>
              ))}
            </View>
          )}
        </View>

        {result.details?.map((d: any, i: number) => (
          <View
            key={i}
            style={[
              styles.detailCard,
              d.is_correct ? styles.detailOk : styles.detailFail,
            ]}
          >
            <Text style={styles.detailQuestion}>
              {i + 1}. {d.question}
            </Text>
            <Text style={styles.detailLine}>
              Ваш ответ: <Text style={styles.detailAnswer}>{d.your_answer || "—"}</Text>
            </Text>
            {!d.is_correct && (
              <Text style={styles.detailLine}>
                Правильный: <Text style={styles.detailCorrect}>{d.correct_answer}</Text>
              </Text>
            )}
          </View>
        ))}

        <TouchableOpacity style={styles.button} onPress={resetAll}>
          <Text style={styles.buttonText}>Пройти ещё тест</Text>
        </TouchableOpacity>
      </ScrollView>
    );
  }

  return null;
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  content: { padding: 24 },
  centered: { flex: 1, justifyContent: "center", alignItems: "center" },
  title: { fontSize: 24, fontWeight: "700", color: Colors.text, marginBottom: 8 },
  subtitle: { fontSize: 14, color: Colors.textSecondary, marginBottom: 20 },
  crumb: { fontSize: 12, color: Colors.textSecondary, marginBottom: 4 },
  backLink: {
    fontSize: 14,
    color: Colors.primary,
    fontWeight: "600",
    marginBottom: 12,
  },
  empty: {
    fontSize: 14,
    color: Colors.textSecondary,
    textAlign: "center",
    marginVertical: 32,
  },
  bigCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 20,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  bigCardTitle: { fontSize: 20, fontWeight: "700", color: Colors.text },
  bigCardHint: { fontSize: 13, color: Colors.textSecondary, marginTop: 4 },
  row: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  rowTitle: { fontSize: 16, fontWeight: "600", color: Colors.text },
  rowHint: { fontSize: 13, color: Colors.textSecondary, marginTop: 4 },
  loadingText: { marginTop: 16, fontSize: 16, color: Colors.textSecondary },
  questionCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  questionText: {
    fontSize: 15,
    fontWeight: "600",
    color: Colors.text,
    marginBottom: 12,
  },
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
  secondaryBtn: {
    backgroundColor: Colors.inputBg,
    borderRadius: 12,
    padding: 14,
    alignItems: "center",
  },
  secondaryBtnText: { color: Colors.text, fontSize: 15, fontWeight: "600" },
  scoreCard: {
    backgroundColor: Colors.primary,
    borderRadius: 16,
    padding: 24,
    alignItems: "center",
    marginVertical: 16,
  },
  scoreNumber: { fontSize: 48, fontWeight: "800", color: "#fff" },
  scoreLabel: { fontSize: 16, color: "rgba(255,255,255,0.9)", marginTop: 4 },
  scoreTime: { fontSize: 13, color: "rgba(255,255,255,0.85)", marginTop: 8 },
  runningHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  timerBadge: {
    backgroundColor: Colors.primary,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 14,
    marginBottom: 12,
  },
  timerText: { color: "#fff", fontWeight: "700", fontSize: 13 },
  feedbackBlock: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  feedbackTitle: {
    fontSize: 14,
    fontWeight: "600",
    color: Colors.text,
    marginBottom: 10,
  },
  feedbackRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    gap: 8,
  },
  feedbackBtn: {
    flex: 1,
    backgroundColor: Colors.inputBg,
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: "center",
  },
  feedbackEmoji: { fontSize: 24 },
  feedbackLabel: {
    fontSize: 12,
    color: Colors.text,
    marginTop: 4,
    fontWeight: "600",
  },
  feedbackThanks: {
    fontSize: 13,
    color: Colors.success,
    fontWeight: "600",
    textAlign: "center",
  },
  feedback: {
    fontSize: 15,
    color: Colors.text,
    lineHeight: 22,
    marginBottom: 16,
  },
  detailCard: {
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
  },
  detailOk: {
    backgroundColor: "#ECFDF5",
    borderColor: "#A7F3D0",
  },
  detailFail: {
    backgroundColor: "#FEF2F2",
    borderColor: "#FECACA",
  },
  detailQuestion: {
    fontSize: 14,
    fontWeight: "600",
    color: Colors.text,
    marginBottom: 6,
  },
  detailLine: { fontSize: 13, color: Colors.text, marginTop: 2 },
  detailAnswer: { fontWeight: "600", color: Colors.text },
  detailCorrect: { fontWeight: "700", color: Colors.success },
});
