// Экран онбординга — показывается один раз при первом запуске
import { useRef, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  Dimensions,
  TouchableOpacity,
  FlatList,
  NativeScrollEvent,
  NativeSyntheticEvent,
} from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { Stack, useRouter } from "expo-router";
import { Colors } from "../constants/theme";

const { width } = Dimensions.get("window");

type Slide = {
  icon: string;
  title: string;
  text: string;
  color: string;
};

const SLIDES: Slide[] = [
  {
    icon: "🤖",
    title: "AI-тьютор всегда рядом",
    text: "Задавайте любые вопросы по школьным предметам, подготовке к ЕГЭ/ОГЭ или саморазвитию.",
    color: "#EEF2FF",
  },
  {
    icon: "📝",
    title: "Тесты и разбор ошибок",
    text: "Решайте задачи по темам, получайте мгновенный разбор от AI и отслеживайте слабые места.",
    color: "#ECFDF5",
  },
  {
    icon: "👨‍🏫",
    title: "Живые репетиторы",
    text: "Если нужен живой наставник — запишитесь на видеозанятие к проверенному репетитору.",
    color: "#FFF7ED",
  },
  {
    icon: "🔥",
    title: "Держите streak",
    text: "Занимайтесь каждый день и следите за прогрессом на графике активности.",
    color: "#FEF3C7",
  },
];

export async function hasCompletedOnboarding(): Promise<boolean> {
  return (await AsyncStorage.getItem("onboarding_completed")) === "1";
}

export default function OnboardingScreen() {
  const router = useRouter();
  const listRef = useRef<FlatList>(null);
  const [index, setIndex] = useState(0);

  const finish = async () => {
    await AsyncStorage.setItem("onboarding_completed", "1");
    router.replace("/(auth)/login");
  };

  const next = () => {
    if (index < SLIDES.length - 1) {
      listRef.current?.scrollToIndex({ index: index + 1 });
    } else {
      finish();
    }
  };

  const onScroll = (e: NativeSyntheticEvent<NativeScrollEvent>) => {
    const i = Math.round(e.nativeEvent.contentOffset.x / width);
    if (i !== index) setIndex(i);
  };

  return (
    <>
      <Stack.Screen options={{ headerShown: false }} />
      <View style={styles.container}>
        <TouchableOpacity style={styles.skip} onPress={finish}>
          <Text style={styles.skipText}>Пропустить</Text>
        </TouchableOpacity>

        <FlatList
          ref={listRef}
          data={SLIDES}
          horizontal
          pagingEnabled
          showsHorizontalScrollIndicator={false}
          keyExtractor={(_, i) => String(i)}
          onScroll={onScroll}
          scrollEventThrottle={16}
          renderItem={({ item }) => (
            <View style={[styles.slide, { width }]}>
              <View style={[styles.iconWrap, { backgroundColor: item.color }]}>
                <Text style={styles.icon}>{item.icon}</Text>
              </View>
              <Text style={styles.title}>{item.title}</Text>
              <Text style={styles.text}>{item.text}</Text>
            </View>
          )}
        />

        <View style={styles.dots}>
          {SLIDES.map((_, i) => (
            <View
              key={i}
              style={[styles.dot, i === index && styles.dotActive]}
            />
          ))}
        </View>

        <TouchableOpacity style={styles.nextBtn} onPress={next}>
          <Text style={styles.nextText}>
            {index === SLIDES.length - 1 ? "Начать" : "Далее"}
          </Text>
        </TouchableOpacity>
      </View>
    </>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  skip: {
    position: "absolute",
    top: 60,
    right: 20,
    zIndex: 10,
    padding: 8,
  },
  skipText: { color: Colors.textSecondary, fontSize: 15 },
  slide: { flex: 1, alignItems: "center", justifyContent: "center", paddingHorizontal: 32 },
  iconWrap: {
    width: 160,
    height: 160,
    borderRadius: 80,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 32,
  },
  icon: { fontSize: 72 },
  title: { fontSize: 24, fontWeight: "800", color: Colors.text, textAlign: "center", marginBottom: 12 },
  text: { fontSize: 15, color: Colors.textSecondary, textAlign: "center", lineHeight: 22 },
  dots: { flexDirection: "row", justifyContent: "center", marginBottom: 20 },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: Colors.border,
    marginHorizontal: 4,
  },
  dotActive: {
    width: 24,
    backgroundColor: Colors.primary,
  },
  nextBtn: {
    backgroundColor: Colors.primary,
    marginHorizontal: 32,
    marginBottom: 40,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: "center",
  },
  nextText: { color: "#fff", fontSize: 16, fontWeight: "700" },
});
