// Начальный экран — редирект
import { Redirect } from "expo-router";
import { useAuthStore } from "../store/authStore";

export default function Index() {
  const isAuth = useAuthStore((s) => s.isAuth);
  return <Redirect href={isAuth ? "/(tabs)" : "/(auth)/login"} />;
}
