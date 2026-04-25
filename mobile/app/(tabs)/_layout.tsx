// Layout с нижними вкладками — набор зависит от роли пользователя
import { Redirect, Tabs } from "expo-router";
import { Text } from "react-native";
import { Colors } from "../../constants/theme";
import { useAuthStore } from "../../store/authStore";

// Простые текстовые иконки (без внешних зависимостей)
function TabIcon({ label, focused }: { label: string; focused: boolean }) {
  return (
    <Text style={{ fontSize: 20, opacity: focused ? 1 : 0.5 }}>{label}</Text>
  );
}

export default function TabLayout() {
  const user = useAuthStore((s) => s.user);
  const isAuth = useAuthStore((s) => s.isAuth);
  // После logout user=null / isAuth=false — нельзя продолжать рендерить табы
  // (ветвление по роли отвалится и вкладка тьютора крашнет приложение).
  // Отправляем сразу в auth-группу.
  if (!isAuth || !user) {
    return <Redirect href="/(auth)/login" />;
  }
  const isTutor = user.role === "tutor";

  // Утилита: `href: null` скрывает таб в expo-router
  const hide = (cond: boolean) => (cond ? { href: null as any } : {});

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: Colors.primary,
        tabBarInactiveTintColor: Colors.textSecondary,
        tabBarStyle: {
          backgroundColor: Colors.surface,
          borderTopColor: Colors.border,
          height: 60,
          paddingBottom: 8,
        },
        headerStyle: { backgroundColor: Colors.surface },
        headerTintColor: Colors.text,
        headerTitleStyle: { fontWeight: "700" },
      }}
    >
      {/* Главная — общая для всех, но содержимое разное по роли */}
      <Tabs.Screen
        name="index"
        options={{
          title: "Главная",
          tabBarIcon: ({ focused }) => <TabIcon label="🏠" focused={focused} />,
        }}
      />

      {/* Только ученику */}
      <Tabs.Screen
        name="chat"
        options={{
          title: "AI Чат",
          tabBarIcon: ({ focused }) => <TabIcon label="💬" focused={focused} />,
          ...hide(isTutor),
        }}
      />
      <Tabs.Screen
        name="tests"
        options={{
          title: "Тесты",
          tabBarIcon: ({ focused }) => <TabIcon label="📝" focused={focused} />,
          ...hide(isTutor),
        }}
      />
      <Tabs.Screen
        name="tutors"
        options={{
          title: "Репетиторы",
          tabBarIcon: ({ focused }) => <TabIcon label="👨‍🏫" focused={focused} />,
          ...hide(isTutor),
        }}
      />

      {/* Только репетитору */}
      <Tabs.Screen
        name="t-sessions"
        options={{
          title: "Занятия",
          tabBarIcon: ({ focused }) => <TabIcon label="📅" focused={focused} />,
          ...hide(!isTutor),
        }}
      />
      <Tabs.Screen
        name="t-schedule"
        options={{
          title: "Расписание",
          tabBarIcon: ({ focused }) => <TabIcon label="🕘" focused={focused} />,
          ...hide(!isTutor),
        }}
      />

      {/* Профиль — общий */}
      <Tabs.Screen
        name="profile"
        options={{
          title: "Профиль",
          tabBarIcon: ({ focused }) => <TabIcon label="👤" focused={focused} />,
        }}
      />
    </Tabs>
  );
}
