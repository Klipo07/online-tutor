// Экран помощи — гайды, FAQ, контакты поддержки
import { useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Linking,
} from "react-native";
import { Stack } from "expo-router";
import { Colors } from "../constants/theme";

type Guide = {
  icon: string;
  title: string;
  text: string;
};

const GUIDES: Guide[] = [
  {
    icon: "💬",
    title: "AI-чат",
    text: "Задайте любой вопрос персональному AI-тьютору. Выберите предмет на главной или прямо в чате — и AI будет отвечать строго в рамках него. Подходит для объяснения тем, помощи с домашкой, разбора ошибок.",
  },
  {
    icon: "📝",
    title: "Тесты",
    text: "Проверяйте свои знания на тестах по темам. Выбирайте уровень сложности, решайте задачи и получайте разбор ошибок от AI. По итогам тесты формируют статистику по слабым темам.",
  },
  {
    icon: "👨‍🏫",
    title: "Репетиторы",
    text: "Если AI не справляется — найдите живого репетитора. Сортируйте по предмету, рейтингу, цене. Записывайтесь на занятие через календарь в профиле репетитора.",
  },
  {
    icon: "📊",
    title: "Прогресс",
    text: "Следите за успехами: streak дней подряд, heatmap активности, прогресс по предметам, слабые темы. Нажимайте на слабую тему — и AI-чат откроется с уже заготовленным вопросом.",
  },
  {
    icon: "📅",
    title: "Мои занятия",
    text: "Все предстоящие и прошедшие занятия с репетиторами. За 10 минут до начала появляется кнопка присоединения к видеозвонку. Отмена без штрафа — не позднее чем за 24 часа.",
  },
];

type FaqItem = {
  q: string;
  a: string;
};

const FAQ: FaqItem[] = [
  {
    q: "Как сменить предмет в AI-чате?",
    a: "Вверху экрана чата — бейдж с предметом. Нажмите на крестик рядом с названием, чтобы сбросить. Или выберите другой предмет на главной.",
  },
  {
    q: "Почему AI отвечает медленно?",
    a: "Обычно ответ занимает 3–10 секунд. Если дольше — проверьте интернет-соединение. Серверы AI могут быть перегружены в часы пик.",
  },
  {
    q: "Как сменить пароль?",
    a: "Профиль → Настройки → Смена пароля. Введите текущий пароль и новый (минимум 6 символов, 1 заглавная буква).",
  },
  {
    q: "Как загрузить аватарку?",
    a: "Профиль → Настройки → нажмите на круг с инициалами или «Загрузить фото». Разрешите доступ к галерее.",
  },
  {
    q: "Как отменить занятие с репетитором?",
    a: "Профиль → Мои занятия → откройте занятие → Отменить. Доступно не позднее чем за 24 часа до начала.",
  },
  {
    q: "Что такое streak?",
    a: "Количество дней подряд, когда вы занимались — решали тесты, переписывались с AI или посещали занятия. Прерывается, если пропустить сутки.",
  },
];

function FaqRow({ item }: { item: FaqItem }) {
  const [open, setOpen] = useState(false);
  return (
    <TouchableOpacity
      style={styles.faqCard}
      onPress={() => setOpen((v) => !v)}
      activeOpacity={0.7}
    >
      <View style={styles.faqHeader}>
        <Text style={styles.faqQ}>{item.q}</Text>
        <Text style={styles.faqChevron}>{open ? "−" : "+"}</Text>
      </View>
      {open && <Text style={styles.faqA}>{item.a}</Text>}
    </TouchableOpacity>
  );
}

export default function HelpScreen() {
  const openTelegram = () => Linking.openURL("https://t.me/ai_tutor_support");
  const openMail = () => Linking.openURL("mailto:support@ai-tutor.ru");

  return (
    <>
      <Stack.Screen options={{ title: "Помощь" }} />
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        {/* Гайды */}
        <Text style={styles.sectionTitle}>Что умеет приложение</Text>
        {GUIDES.map((g, i) => (
          <View key={i} style={styles.guideCard}>
            <Text style={styles.guideIcon}>{g.icon}</Text>
            <View style={{ flex: 1 }}>
              <Text style={styles.guideTitle}>{g.title}</Text>
              <Text style={styles.guideText}>{g.text}</Text>
            </View>
          </View>
        ))}

        {/* FAQ */}
        <Text style={[styles.sectionTitle, { marginTop: 16 }]}>Частые вопросы</Text>
        {FAQ.map((item, i) => (
          <FaqRow key={i} item={item} />
        ))}

        {/* Контакты */}
        <Text style={[styles.sectionTitle, { marginTop: 16 }]}>Связаться с нами</Text>
        <TouchableOpacity style={styles.contactCard} onPress={openTelegram}>
          <Text style={styles.contactIcon}>✈️</Text>
          <View style={{ flex: 1 }}>
            <Text style={styles.contactTitle}>Telegram</Text>
            <Text style={styles.contactText}>@ai_tutor_support</Text>
          </View>
        </TouchableOpacity>
        <TouchableOpacity style={styles.contactCard} onPress={openMail}>
          <Text style={styles.contactIcon}>✉️</Text>
          <View style={{ flex: 1 }}>
            <Text style={styles.contactTitle}>Email</Text>
            <Text style={styles.contactText}>support@ai-tutor.ru</Text>
          </View>
        </TouchableOpacity>
      </ScrollView>
    </>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  content: { padding: 16, paddingBottom: 40 },
  sectionTitle: {
    fontSize: 17,
    fontWeight: "700",
    color: Colors.text,
    marginBottom: 12,
  },
  guideCard: {
    flexDirection: "row",
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: Colors.border,
    gap: 12,
  },
  guideIcon: { fontSize: 28 },
  guideTitle: { fontSize: 15, fontWeight: "700", color: Colors.text, marginBottom: 4 },
  guideText: { fontSize: 13, color: Colors.textSecondary, lineHeight: 19 },

  faqCard: {
    backgroundColor: Colors.surface,
    borderRadius: 10,
    padding: 14,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  faqHeader: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  faqQ: { flex: 1, fontSize: 14, fontWeight: "600", color: Colors.text, paddingRight: 10 },
  faqChevron: { fontSize: 20, fontWeight: "700", color: Colors.primary, width: 20, textAlign: "center" },
  faqA: { fontSize: 13, color: Colors.textSecondary, lineHeight: 19, marginTop: 8 },

  contactCard: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: Colors.border,
    gap: 12,
  },
  contactIcon: { fontSize: 22 },
  contactTitle: { fontSize: 14, fontWeight: "600", color: Colors.text },
  contactText: { fontSize: 13, color: Colors.primary, marginTop: 2 },
});
