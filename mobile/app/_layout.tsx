// Корневой layout — проверка авторизации и маршрутизация
import { useEffect, useState } from "react";
import { Stack, useRouter, useSegments } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { ActivityIndicator, View } from "react-native";
import { KeyboardProvider } from "react-native-keyboard-controller";
import { useAuthStore } from "../store/authStore";
import { Colors } from "../constants/theme";
import { hasCompletedOnboarding } from "./onboarding";

export default function RootLayout() {
  const { isAuth, isLoading, checkAuth } = useAuthStore();
  const segments = useSegments();
  const router = useRouter();
  const [onboardingDone, setOnboardingDone] = useState<boolean | null>(null);

  useEffect(() => {
    checkAuth();
    hasCompletedOnboarding().then(setOnboardingDone);
  }, []);

  useEffect(() => {
    if (isLoading || onboardingDone === null) return;

    const inAuthGroup = segments[0] === "(auth)";
    const inOnboarding = segments[0] === "onboarding";

    if (!isAuth && !onboardingDone && !inOnboarding) {
      router.replace("/onboarding");
      return;
    }
    if (!isAuth && onboardingDone && !inAuthGroup) {
      router.replace("/(auth)/login");
    } else if (isAuth && (inAuthGroup || inOnboarding)) {
      router.replace("/(tabs)");
    }
  }, [isAuth, isLoading, onboardingDone, segments]);

  if (isLoading) {
    return (
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: Colors.background }}>
        <ActivityIndicator size="large" color={Colors.primary} />
      </View>
    );
  }

  return (
    <KeyboardProvider>
      <StatusBar style="dark" />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: Colors.surface },
          headerTintColor: Colors.text,
          headerTitleStyle: { fontWeight: "700" },
        }}
      >
        <Stack.Screen name="(auth)" options={{ headerShown: false }} />
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen name="settings" options={{ title: "Настройки" }} />
        <Stack.Screen name="my-sessions" options={{ title: "Мои занятия" }} />
        <Stack.Screen name="progress" options={{ title: "Мой прогресс" }} />
        <Stack.Screen name="help" options={{ title: "Помощь" }} />
        <Stack.Screen name="onboarding" options={{ headerShown: false }} />
      </Stack>
    </KeyboardProvider>
  );
}
