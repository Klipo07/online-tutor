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
  Image,
  TextInput,
  Linking,
} from "react-native";
import api from "../../services/api";
import { Colors, API_URL } from "../../constants/theme";

// API_URL = http://host/api/v1 — для статики (картинки) нужен корень без /api/v1
const STATIC_BASE = API_URL.replace(/\/api\/v1\/?$/, "");
const absUrl = (path: string): string =>
  path.startsWith("http") ? path : `${STATIC_BASE}${path}`;

// Чистим маркеры "[рисунок N]" из текста — картинка показывается отдельным <Image>
const cleanQuestionText = (text: string): string =>
  text.replace(/\[рисунок\s+\d+\]\s*/gi, "").trim();

type FeedbackRating = "too_easy" | "ok" | "too_hard";

type ExamType = "ege" | "oge" | "regular";
type Difficulty = "easy" | "medium" | "hard";

type SubjectItem = { id: number; name: string; slug: string; tests_count: number };
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
  image_urls?: string[];
  source_url?: string | null;
  from_bank?: boolean;
};

type Stage =
  | "exam"
  | "mode"
  | "subject"
  | "math-variant"
  | "task"
  | "difficulty"
  | "num-questions"
  | "list"
  | "loading"
  | "running"
  | "result";

type PickMode = "manual" | "ai";

type MathVariant = "profile" | "base";

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

// Доступное количество вопросов в одном AI-сгенерированном тесте.
// Бэк валидирует 1..30 — фронт показывает несколько ходовых пресетов.
const NUM_QUESTIONS_PRESETS: number[] = [3, 5, 10, 15, 20];

// Fallback максимум, если /tests/task-range упал. Для regular на бэке тоже 30.
const TASK_RANGE_FALLBACK = 30;

export default function TestsScreen() {
  const [stage, setStage] = useState<Stage>("exam");
  const [mode, setMode] = useState<PickMode>("manual");

  const [examType, setExamType] = useState<ExamType | null>(null);
  const [subject, setSubject] = useState<SubjectItem | null>(null);
  const [mathVariant, setMathVariant] = useState<MathVariant | null>(null);
  const [taskNumber, setTaskNumber] = useState<number | null>(null);
  const [difficulty, setDifficulty] = useState<Difficulty | null>(null);
  // Сложность, которую подобрал AI — показываем плашку «AI подобрал: medium»
  const [aiDifficulty, setAiDifficulty] = useState<Difficulty | null>(null);

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
    setMode("manual");
    setExamType(null);
    setSubject(null);
    setMathVariant(null);
    setTaskNumber(null);
    setDifficulty(null);
    setAiDifficulty(null);
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
    if (stage === "mode") {
      setStage("exam");
      setExamType(null);
    } else if (stage === "subject") {
      setStage("mode");
      setSubject(null);
    } else if (stage === "math-variant") {
      setStage("subject");
      setSubject(null);
      setMathVariant(null);
    } else if (stage === "task") {
      // Если это математика ЕГЭ — возвращаемся к выбору профиля/базы.
      // Иначе — к выбору предмета.
      const needsMathStep =
        examType === "ege" && subject?.slug === "math";
      if (needsMathStep) {
        setStage("math-variant");
        setMathVariant(null);
      } else {
        setStage("subject");
        setSubject(null);
      }
    } else if (stage === "difficulty") {
      setStage("task");
      setTaskNumber(null);
    } else if (stage === "num-questions") {
      setStage("difficulty");
      setDifficulty(null);
    } else if (stage === "list") {
      // Для AI-подбора назад к выбору предмета; для manual — к сложности
      if (mode === "ai") {
        setAiDifficulty(null);
        setStage("subject");
      } else {
        setStage("difficulty");
        setDifficulty(null);
      }
    } else if (stage === "running" || stage === "result") {
      setCurrentTest(null);
      setAnswers({});
      setResult(null);
      // Manual-режим — нет списка тестов (AI генерировал на лету),
      // возвращаемся к выбору количества вопросов, чтобы сгенерировать заново
      setStage(mode === "ai" ? "list" : "num-questions");
    }
  }, [stage, mode, examType, subject]);

  // Шаг: Выбор экзамена → выбор режима (AI vs manual)
  const pickExam = useCallback((type: ExamType) => {
    setExamType(type);
    setStage("mode");
  }, []);

  // Шаг: Выбор режима → загрузка предметов
  const pickMode = useCallback(
    async (m: PickMode) => {
      if (!examType) return;
      setMode(m);
      setLoading(true);
      try {
        const res = await api.get("/tests/subjects-with-tests", {
          params: { exam_type: examType },
        });
        setSubjects(res.data);
        setStage("subject");
      } catch {
        Alert.alert("Ошибка", "Не удалось загрузить предметы");
      } finally {
        setLoading(false);
      }
    },
    [examType]
  );

  // Загрузка списка номеров заданий — реальный максимум по предмету/формату
  // (плюс счётчики из банка для подсказки).
  const loadTaskNumbers = useCallback(
    async (
      subjectItem: SubjectItem,
      exam: ExamType,
      variant: MathVariant | null,
    ) => {
      // Сначала забираем range — он определяет, сколько номеров рисовать.
      let maxN = TASK_RANGE_FALLBACK;
      try {
        const params: Record<string, any> = {
          subject_id: subjectItem.id,
          exam_type: exam,
        };
        if (variant) params.math_variant = variant;
        const rangeRes = await api.get("/tests/task-range", { params });
        maxN = rangeRes.data.max_task_number ?? TASK_RANGE_FALLBACK;
      } catch {
        // Используем fallback и идём дальше
      }

      // Сразу показываем 1..maxN без счётчиков, потом домерживаем счётчики
      setTaskNumbers(
        Array.from({ length: maxN }, (_, i) => ({ task_number: i + 1, count: 0 }))
      );
      setStage("task");

      try {
        const res = await api.get("/tests/task-numbers", {
          params: { subject_id: subjectItem.id, exam_type: exam },
        });
        const counts: Record<number, number> = Object.fromEntries(
          (res.data as TaskNumberItem[]).map((t) => [t.task_number, t.count])
        );
        setTaskNumbers(
          Array.from({ length: maxN }, (_, i) => ({
            task_number: i + 1,
            count: counts[i + 1] || 0,
          }))
        );
      } catch {
        // молча — у нас уже есть статический список
      }
    },
    []
  );

  // Шаг: Выбор предмета → (AI: подбор тестов; Manual: math-variant для математики ЕГЭ или task)
  const pickSubject = useCallback(
    async (s: SubjectItem) => {
      if (!examType) return;
      setSubject(s);

      if (mode === "ai") {
        setLoading(true);
        try {
          // AI подбор — бэк сам решает сложность по фидбекам
          const res = await api.post("/tests/recommend", {
            subject_id: s.id,
            exam_type: examType,
            limit: 5,
          });
          setAiDifficulty(res.data.difficulty as Difficulty);
          setTests(res.data.tests);
          setStage("list");
        } catch {
          Alert.alert("Ошибка", "Не удалось подобрать тесты");
          setSubject(null);
        } finally {
          setLoading(false);
        }
        return;
      }

      // Manual: для математики ЕГЭ — отдельный шаг профиль/база (range у них разный)
      if (examType === "ege" && s.slug === "math") {
        setStage("math-variant");
        return;
      }

      await loadTaskNumbers(s, examType, null);
    },
    [examType, mode, loadTaskNumbers]
  );

  // Шаг: Выбор варианта математики (профильная / базовая) → загрузка номеров заданий
  const pickMathVariant = useCallback(
    async (v: MathVariant) => {
      if (!examType || !subject) return;
      setMathVariant(v);
      await loadTaskNumbers(subject, examType, v);
    },
    [examType, subject, loadTaskNumbers]
  );

  // Шаг: Выбор задания → переход к сложности
  const pickTaskNumber = useCallback((n: number | null) => {
    setTaskNumber(n);
    setStage("difficulty");
  }, []);

  // Шаг: Выбор сложности → переход к выбору количества вопросов
  const pickDifficulty = useCallback((d: Difficulty | null) => {
    setDifficulty(d);
    setStage("num-questions");
  }, []);

  // Шаг: Выбор количества вопросов → сначала пробуем банк (Решу ЕГЭ), потом AI
  const pickNumQuestions = useCallback(
    async (n: number) => {
      if (!examType || !subject) return;
      setLoading(true);
      setStage("loading");
      try {
        // Сначала ищем подходящие задания в банке (импорт со sdamgia).
        // Сложность не фильтруем здесь — банк размечен дефолтно как medium,
        // вариативность достигается рандомом по списку.
        const bankRes = await api.get<TestListItem[]>("/tests", {
          params: {
            subject_id: subject.id,
            exam_type: examType,
            ...(taskNumber !== null ? { task_number: taskNumber } : {}),
            limit: 50,
          },
        });
        const fromBank = bankRes.data.filter((t) => (t as any).from_bank);
        if (fromBank.length > 0) {
          // Случайный из банка — это реальное задание Решу ЕГЭ
          const pick = fromBank[Math.floor(Math.random() * fromBank.length)];
          const fullRes = await api.get<FullTest>(`/tests/${pick.id}`);
          setCurrentTest(fullRes.data);
          setAnswers({});
          setFeedbackSent(null);
          setElapsedSec(0);
          startedAtRef.current = Date.now();
          setStage("running");
          return;
        }

        // В банке пусто — AI-генерация
        const payload: Record<string, any> = {
          subject_id: subject.id,
          exam_type: examType,
          difficulty: difficulty || "medium",
          num_questions: n,
        };
        if (taskNumber !== null) payload.task_number = taskNumber;
        if (mathVariant) payload.math_variant = mathVariant;

        const res = await api.post<FullTest>("/tests/ai-generate", payload);
        setCurrentTest(res.data);
        setAnswers({});
        setFeedbackSent(null);
        setElapsedSec(0);
        startedAtRef.current = Date.now();
        setStage("running");
      } catch (e: any) {
        const msg = e?.response?.data?.detail || "Не удалось сгенерировать тест";
        Alert.alert("Ошибка", msg);
        setStage("num-questions");
      } finally {
        setLoading(false);
      }
    },
    [examType, subject, taskNumber, difficulty, mathVariant]
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
    if (stage !== "exam" && stage !== "mode" && mode === "ai") parts.push("AI");
    if (subject) parts.push(subject.name);
    if (mathVariant) parts.push(mathVariant === "profile" ? "Профильная" : "Базовая");
    if (taskNumber !== null) parts.push(`№${taskNumber}`);
    if (difficulty) parts.push(DIFFICULTY_LABELS[difficulty]);
    return parts.join(" · ");
  }, [examType, subject, mathVariant, taskNumber, difficulty, stage, mode]);

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

  // === Шаг 1.5: Выбор режима (AI-подбор или вручную) ===
  if (stage === "mode") {
    return (
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        <TouchableOpacity onPress={goBack}>
          <Text style={styles.backLink}>← Назад</Text>
        </TouchableOpacity>
        <Text style={styles.crumb}>{breadcrumb}</Text>
        <Text style={styles.title}>Как подобрать тесты?</Text>
        <Text style={styles.subtitle}>
          AI адаптирует сложность под ваши предыдущие фидбеки
        </Text>

        <TouchableOpacity
          style={[styles.bigCard, styles.aiCard]}
          onPress={() => pickMode("ai")}
        >
          <Text style={styles.bigCardTitle}>✨ AI-подбор</Text>
          <Text style={styles.bigCardHint}>
            Автоматически подберу 5 тестов под ваш уровень
          </Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.bigCard} onPress={() => pickMode("manual")}>
          <Text style={styles.bigCardTitle}>Выбрать вручную</Text>
          <Text style={styles.bigCardHint}>
            Предмет → номер задания → сложность
          </Text>
        </TouchableOpacity>
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

  // === Шаг 2.5: Профильная / Базовая (только для математики ЕГЭ) ===
  if (stage === "math-variant") {
    return (
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        <TouchableOpacity onPress={goBack}>
          <Text style={styles.backLink}>← Назад</Text>
        </TouchableOpacity>
        <Text style={styles.crumb}>{breadcrumb}</Text>
        <Text style={styles.title}>Профильная или базовая?</Text>
        <Text style={styles.subtitle}>
          У ЕГЭ по математике две версии — выберите свою
        </Text>

        <TouchableOpacity
          style={styles.bigCard}
          onPress={() => pickMathVariant("profile")}
        >
          <Text style={styles.bigCardTitle}>Профильная</Text>
          <Text style={styles.bigCardHint}>
            19 заданий — для технических и математических вузов
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.bigCard}
          onPress={() => pickMathVariant("base")}
        >
          <Text style={styles.bigCardTitle}>Базовая</Text>
          <Text style={styles.bigCardHint}>
            21 задание — для гуманитарных направлений
          </Text>
        </TouchableOpacity>
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
        <Text style={styles.subtitle}>
          AI сгенерирует рандомный тест по выбранному номеру
        </Text>

        <TouchableOpacity style={styles.row} onPress={() => pickTaskNumber(null)}>
          <Text style={styles.rowTitle}>Любое задание</Text>
          <Text style={styles.rowHint}>AI выберет тему сам</Text>
        </TouchableOpacity>

        {taskNumbers.map((t) => (
          <TouchableOpacity
            key={t.task_number}
            style={styles.row}
            onPress={() => pickTaskNumber(t.task_number)}
          >
            <Text style={styles.rowTitle}>Задание №{t.task_number}</Text>
            <Text style={styles.rowHint}>
              {t.count > 0
                ? `${t.count} в банке + AI-генерация`
                : "AI-генерация (в банке пока пусто)"}
            </Text>
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
        <Text style={styles.subtitle}>
          Дальше выберите количество вопросов в тесте
        </Text>

        <TouchableOpacity style={styles.row} onPress={() => pickDifficulty(null)}>
          <Text style={styles.rowTitle}>Средняя (по умолчанию)</Text>
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

  // === Шаг 4.5: Количество вопросов ===
  if (stage === "num-questions") {
    return (
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        <TouchableOpacity onPress={goBack}>
          <Text style={styles.backLink}>← Назад</Text>
        </TouchableOpacity>
        <Text style={styles.crumb}>{breadcrumb}</Text>
        <Text style={styles.title}>Сколько вопросов?</Text>
        <Text style={styles.subtitle}>
          После выбора AI сразу начнёт генерировать тест (10-30 секунд)
        </Text>

        {NUM_QUESTIONS_PRESETS.map((n) => (
          <TouchableOpacity
            key={n}
            style={styles.row}
            onPress={() => pickNumQuestions(n)}
          >
            <Text style={styles.rowTitle}>{n} вопросов</Text>
            <Text style={styles.rowHint}>
              {n <= 5
                ? "Быстрая проверка темы"
                : n <= 10
                ? "Стандартный объём"
                : "Полноценная тренировка"}
            </Text>
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

        {mode === "ai" && aiDifficulty && (
          <View style={styles.aiBadge}>
            <Text style={styles.aiBadgeText}>
              ✨ AI подобрал: {DIFFICULTY_LABELS[aiDifficulty]}
            </Text>
          </View>
        )}

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
        <Text style={styles.loadingText}>
          {mode === "manual" ? "AI генерирует тест..." : "Загрузка теста..."}
        </Text>
      </View>
    );
  }

  // === Прохождение теста ===
  if (stage === "running" && currentTest) {
    // Считаем заполненными только непустые ответы (для input — strip)
    const filledCount = currentTest.questions.filter(
      (q) => (answers[String(q.id)] || "").trim().length > 0
    ).length;
    const allAnswered = filledCount === currentTest.questions.length;
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

        {/* Бейдж источника — для заданий из банка Решу ЕГЭ */}
        {currentTest.from_bank && (
          <TouchableOpacity
            style={styles.sourceBadge}
            onPress={() =>
              currentTest.source_url && Linking.openURL(currentTest.source_url)
            }
            disabled={!currentTest.source_url}
          >
            <Text style={styles.sourceBadgeText}>
              📘 Реальное задание ФИПИ (Решу ЕГЭ)
            </Text>
          </TouchableOpacity>
        )}

        {/* Графики/чертежи — общие для всего теста */}
        {currentTest.image_urls?.map((url, i) => (
          <Image
            key={i}
            source={{ uri: absUrl(url) }}
            style={styles.questionImage}
            resizeMode="contain"
          />
        ))}

        {currentTest.questions.map((q, qIdx) => {
          const isInput = q.type === "input";
          // Используем индекс в key — AI/банк могут вернуть дубли q.id или дубли вариантов
          return (
            <View key={`q-${qIdx}-${q.id}`} style={styles.questionCard}>
              <Text style={styles.questionText}>
                {q.id}. {cleanQuestionText(q.question)}
              </Text>
              {isInput ? (
                <TextInput
                  style={styles.answerInput}
                  placeholder="Введите ответ"
                  placeholderTextColor={Colors.textSecondary}
                  value={answers[String(q.id)] || ""}
                  onChangeText={(text) =>
                    setAnswers((prev) => ({ ...prev, [String(q.id)]: text }))
                  }
                  keyboardType="default"
                  autoCapitalize="none"
                  autoCorrect={false}
                />
              ) : (
                q.options?.map((opt, optIdx) => (
                  <TouchableOpacity
                    key={`q${qIdx}-opt${optIdx}`}
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
                        answers[String(q.id)] === opt &&
                          styles.optionTextSelected,
                      ]}
                    >
                      {opt}
                    </Text>
                  </TouchableOpacity>
                ))
              )}
            </View>
          );
        })}

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
              : `Ответьте на все вопросы (${filledCount}/${currentTest.questions.length})`}
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
              {i + 1}. {cleanQuestionText(d.question)}
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
  aiCard: {
    backgroundColor: Colors.primary + "10",
    borderColor: Colors.primary,
  },
  aiBadge: {
    backgroundColor: Colors.primary + "18",
    borderRadius: 10,
    paddingVertical: 10,
    paddingHorizontal: 14,
    marginBottom: 12,
  },
  aiBadgeText: { color: Colors.primary, fontSize: 13, fontWeight: "700" },
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
  answerInput: {
    backgroundColor: Colors.inputBg,
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    color: Colors.text,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  questionImage: {
    width: "100%",
    height: 220,
    backgroundColor: Colors.inputBg,
    borderRadius: 8,
    marginBottom: 12,
  },
  sourceBadge: {
    backgroundColor: "#E0F2FE",
    borderColor: "#0284C7",
    borderWidth: 1,
    borderRadius: 8,
    padding: 10,
    marginBottom: 12,
  },
  sourceBadgeText: {
    color: "#0369A1",
    fontSize: 13,
    fontWeight: "600",
    textAlign: "center",
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
