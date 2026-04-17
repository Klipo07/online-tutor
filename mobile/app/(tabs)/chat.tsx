// Экран AI-чата с тьютором
import { memo, useState, useRef, useCallback, useEffect } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  FlatList,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useBottomTabBarHeight } from "@react-navigation/bottom-tabs";
import { useHeaderHeight } from "@react-navigation/elements";
import api from "../../services/api";
import { Colors } from "../../constants/theme";
import { Avatar } from "../../components/Avatar";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

type TutorRecommendation = {
  id: number;
  full_name: string;
  subjects: string[];
  price_per_hour: number;
  rating: number;
  reviews_count: number;
  experience_years: number;
  avatar_url: string | null;
};

const SUBJECT_ICONS: Record<string, string> = {
  "Математика": "📐",
  "Русский язык": "📖",
  "Физика": "⚡",
  "Химия": "🧪",
  "Биология": "🧬",
  "История": "🏛️",
  "Обществознание": "⚖️",
  "Английский": "🇬🇧",
  "Английский язык": "🇬🇧",
  "Информатика": "💻",
  "География": "🌍",
  "Литература": "📚",
};

const buildWelcome = (subject?: string): Message => ({
  id: "welcome",
  role: "assistant",
  content: subject
    ? `Привет! Я AI-тьютор по предмету «${subject}». Задавай любой вопрос — помогу разобраться!`
    : "Привет! Я твой персональный AI-тьютор. Выбери предмет на главной или просто задай вопрос!",
});

const MessageBubble = memo(function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  return (
    <View style={[styles.messageBubble, isUser ? styles.userBubble : styles.aiBubble]}>
      {!isUser && <Text style={styles.aiLabel}>AI Тьютор</Text>}
      <Text style={[styles.messageText, isUser && styles.userText]}>{message.content}</Text>
    </View>
  );
});

// Карточка-рекомендация живого репетитора — показывается после 3-го сообщения
const TutorRecommendationCard = memo(function TutorRecommendationCard({
  tutor,
  onBook,
  onDismiss,
}: {
  tutor: TutorRecommendation;
  onBook: () => void;
  onDismiss: () => void;
}) {
  return (
    <View style={styles.recommendCard}>
      <View style={styles.recommendHeader}>
        <Text style={styles.recommendLabel}>💡 Нужна помощь человека?</Text>
        <TouchableOpacity onPress={onDismiss} hitSlop={8}>
          <Text style={styles.recommendClose}>×</Text>
        </TouchableOpacity>
      </View>
      <Text style={styles.recommendSubtitle}>
        Вижу, ты разбираешь тему всерьёз. Есть отличный живой репетитор:
      </Text>
      <View style={styles.recommendBody}>
        <Avatar name={tutor.full_name} size={48} />
        <View style={styles.recommendInfo}>
          <Text style={styles.recommendName}>{tutor.full_name}</Text>
          <Text style={styles.recommendSubjects} numberOfLines={1}>
            {tutor.subjects.join(", ")}
          </Text>
          <Text style={styles.recommendMeta}>
            {"\u2B50"} {tutor.rating.toFixed(1)} · {tutor.experience_years} лет · {tutor.price_per_hour}₽/час
          </Text>
        </View>
      </View>
      <TouchableOpacity style={styles.recommendButton} onPress={onBook}>
        <Text style={styles.recommendButtonText}>Посмотреть профиль</Text>
      </TouchableOpacity>
    </View>
  );
});

export default function ChatScreen() {
  const { subject: subjectParam } = useLocalSearchParams<{ subject?: string }>();
  const router = useRouter();
  const tabBarHeight = useBottomTabBarHeight();
  const headerHeight = useHeaderHeight();
  const [subject, setSubject] = useState<string | undefined>(subjectParam);
  const [messages, setMessages] = useState<Message[]>([buildWelcome(subjectParam)]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [userMsgCount, setUserMsgCount] = useState(0);
  const [recommendedTutor, setRecommendedTutor] = useState<TutorRecommendation | null>(null);
  const [recommendDismissed, setRecommendDismissed] = useState(false);
  const flatListRef = useRef<FlatList>(null);

  // При смене предмета через навигацию — стартуем новую сессию, чтобы AI не путался
  useEffect(() => {
    if (subjectParam !== subject) {
      setSubject(subjectParam);
      setSessionId(null);
      setMessages([buildWelcome(subjectParam)]);
      setUserMsgCount(0);
      setRecommendedTutor(null);
      setRecommendDismissed(false);
    }
  }, [subjectParam]);

  const clearSubject = useCallback(() => {
    setSubject(undefined);
    setSessionId(null);
    setMessages([buildWelcome(undefined)]);
    setUserMsgCount(0);
    setRecommendedTutor(null);
    setRecommendDismissed(false);
  }, []);

  // Подгружаем топ-репетитора по текущему предмету для рекомендации
  const loadRecommendation = useCallback(async () => {
    if (recommendDismissed || recommendedTutor) return;
    try {
      const params: Record<string, string | number> = { page: 1, per_page: 1 };
      if (subject) params.subject = subject;
      const res = await api.get("/tutors", { params });
      const tutor = (res.data.tutors ?? [])[0];
      if (tutor) setRecommendedTutor(tutor);
    } catch {
      // рекомендация — второстепенно, ошибку не показываем
    }
  }, [subject, recommendDismissed, recommendedTutor]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: text,
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    // Счётчик пользовательских сообщений — на 3-м триггерим рекомендацию
    const newCount = userMsgCount + 1;
    setUserMsgCount(newCount);
    if (newCount === 3) {
      loadRecommendation();
    }

    try {
      const res = await api.post("/ai/chat", {
        message: text,
        session_id: sessionId,
        subject: subject || "Общий",
        topic: "Свободная тема",
      });

      if (!sessionId) {
        setSessionId(res.data.session_id);
      }

      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: res.data.content,
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (e: any) {
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Ошибка подключения к AI. Проверьте соединение с сервером.",
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const renderMessage = useCallback(
    ({ item }: { item: Message }) => <MessageBubble message={item} />,
    [],
  );
  const keyExtractor = useCallback((item: Message) => item.id, []);
  const scrollToEnd = useCallback(
    () => flatListRef.current?.scrollToEnd({ animated: true }),
    [],
  );

  const placeholder = subject
    ? `Задайте любой вопрос по предмету «${subject}»`
    : "Задайте вопрос...";

  const openTutorTab = useCallback(() => {
    router.push("/(tabs)/tutors");
  }, [router]);

  const dismissRecommendation = useCallback(() => {
    setRecommendedTutor(null);
    setRecommendDismissed(true);
  }, []);

  const showRecommendation =
    recommendedTutor !== null && !recommendDismissed && userMsgCount >= 3;

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
      keyboardVerticalOffset={headerHeight + tabBarHeight}
    >
      {subject && (
        <View style={styles.subjectBar}>
          <View style={styles.subjectBadge}>
            <Text style={styles.subjectIcon}>{SUBJECT_ICONS[subject] ?? "📚"}</Text>
            <Text style={styles.subjectText}>{subject}</Text>
            <TouchableOpacity onPress={clearSubject} hitSlop={8} style={styles.clearBtn}>
              <Text style={styles.clearText}>×</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      <FlatList
        ref={flatListRef}
        data={messages}
        renderItem={renderMessage}
        keyExtractor={keyExtractor}
        contentContainerStyle={styles.messagesList}
        onContentSizeChange={scrollToEnd}
        ListFooterComponent={
          showRecommendation && recommendedTutor ? (
            <TutorRecommendationCard
              tutor={recommendedTutor}
              onBook={openTutorTab}
              onDismiss={dismissRecommendation}
            />
          ) : null
        }
      />

      {loading && (
        <View style={styles.typingIndicator}>
          <ActivityIndicator size="small" color={Colors.primary} />
          <Text style={styles.typingText}>AI думает...</Text>
        </View>
      )}

      <View style={styles.inputContainer}>
        <TextInput
          style={styles.input}
          placeholder={placeholder}
          placeholderTextColor={Colors.textSecondary}
          value={input}
          onChangeText={setInput}
          multiline
          maxLength={2000}
        />
        <TouchableOpacity
          style={[styles.sendButton, (!input.trim() || loading) && styles.sendDisabled]}
          onPress={sendMessage}
          disabled={!input.trim() || loading}
        >
          <Text style={styles.sendText}>→</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  messagesList: {
    padding: 16,
    paddingBottom: 8,
  },
  subjectBar: {
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 4,
    backgroundColor: Colors.background,
  },
  subjectBadge: {
    alignSelf: "flex-start",
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.primary,
    borderRadius: 20,
    paddingVertical: 6,
    paddingLeft: 10,
    paddingRight: 6,
    gap: 6,
  },
  subjectIcon: {
    fontSize: 15,
  },
  subjectText: {
    fontSize: 13,
    fontWeight: "600",
    color: Colors.primary,
  },
  clearBtn: {
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: Colors.primary,
    justifyContent: "center",
    alignItems: "center",
    marginLeft: 2,
  },
  clearText: {
    color: "#fff",
    fontSize: 16,
    lineHeight: 18,
    fontWeight: "700",
  },
  messageBubble: {
    maxWidth: "80%",
    borderRadius: 16,
    padding: 12,
    marginBottom: 8,
  },
  userBubble: {
    backgroundColor: Colors.primary,
    alignSelf: "flex-end",
    borderBottomRightRadius: 4,
  },
  aiBubble: {
    backgroundColor: Colors.surface,
    alignSelf: "flex-start",
    borderBottomLeftRadius: 4,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  aiLabel: {
    fontSize: 11,
    color: Colors.primary,
    fontWeight: "600",
    marginBottom: 4,
  },
  messageText: {
    fontSize: 15,
    color: Colors.text,
    lineHeight: 22,
  },
  userText: {
    color: "#fff",
  },
  typingIndicator: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 20,
    paddingVertical: 8,
    gap: 8,
  },
  typingText: {
    fontSize: 13,
    color: Colors.textSecondary,
  },
  inputContainer: {
    flexDirection: "row",
    alignItems: "flex-end",
    padding: 12,
    backgroundColor: Colors.surface,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  input: {
    flex: 1,
    backgroundColor: Colors.inputBg,
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    fontSize: 15,
    color: Colors.text,
    maxHeight: 100,
  },
  sendButton: {
    backgroundColor: Colors.primary,
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: "center",
    alignItems: "center",
    marginLeft: 8,
  },
  sendDisabled: {
    opacity: 0.4,
  },
  sendText: {
    color: "#fff",
    fontSize: 20,
    fontWeight: "700",
  },

  // Карточка-рекомендация репетитора
  recommendCard: {
    backgroundColor: Colors.surface,
    borderRadius: 16,
    padding: 16,
    marginTop: 8,
    marginBottom: 4,
    borderWidth: 1,
    borderColor: Colors.primary + "40",
  },
  recommendHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  recommendLabel: {
    fontSize: 13,
    fontWeight: "700",
    color: Colors.primary,
    textTransform: "uppercase",
    letterSpacing: 0.3,
  },
  recommendClose: {
    fontSize: 20,
    color: Colors.textSecondary,
    fontWeight: "700",
    paddingHorizontal: 4,
  },
  recommendSubtitle: {
    fontSize: 14,
    color: Colors.text,
    marginTop: 6,
    lineHeight: 20,
  },
  recommendBody: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 12,
    gap: 12,
  },
  recommendInfo: {
    flex: 1,
  },
  recommendName: {
    fontSize: 15,
    fontWeight: "700",
    color: Colors.text,
  },
  recommendSubjects: {
    fontSize: 12,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  recommendMeta: {
    fontSize: 12,
    color: Colors.textSecondary,
    marginTop: 4,
  },
  recommendButton: {
    backgroundColor: Colors.primary,
    borderRadius: 12,
    paddingVertical: 12,
    alignItems: "center",
    marginTop: 12,
  },
  recommendButtonText: {
    color: "#fff",
    fontSize: 14,
    fontWeight: "700",
  },
});
