// Стор авторизации — хранит токены и данные пользователя
import { create } from "zustand";
import AsyncStorage from "@react-native-async-storage/async-storage";
import api from "../services/api";

type User = {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: string;
  avatar_url: string | null;
  bio?: string | null;
  phone?: string | null;
  email_verified?: boolean;
  email_verified_at?: string | null;
};

// Поля регистрации. Для tutor добавляются поля профиля.
export type RegisterPayload =
  | {
      role: "student" | "parent";
      email: string;
      password: string;
      first_name: string;
      last_name: string;
    }
  | {
      role: "tutor";
      email: string;
      password: string;
      first_name: string;
      last_name: string;
      subjects: string[];
      price_per_hour: number;
      experience_years: number;
      bio?: string;
      education?: string;
    };

type AuthState = {
  user: User | null;
  isLoading: boolean;
  isAuth: boolean;
  onboardingDone: boolean | null;

  register: (payload: RegisterPayload) => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  setUser: (user: User) => void;
  loadOnboardingFlag: () => Promise<void>;
  markOnboardingDone: () => Promise<void>;
  resetOnboarding: () => Promise<void>;
};

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: true,
  isAuth: false,
  onboardingDone: null,

  register: async (payload) => {
    const res = await api.post("/auth/register", payload);
    const { user, tokens } = res.data;
    await AsyncStorage.setItem("access_token", tokens.access_token);
    await AsyncStorage.setItem("refresh_token", tokens.refresh_token);
    set({ user, isAuth: true });
  },

  login: async (email, password) => {
    const res = await api.post("/auth/login", { email, password });
    const { user, tokens } = res.data;
    await AsyncStorage.setItem("access_token", tokens.access_token);
    await AsyncStorage.setItem("refresh_token", tokens.refresh_token);
    set({ user, isAuth: true });
  },

  logout: async () => {
    await AsyncStorage.multiRemove(["access_token", "refresh_token"]);
    set({ user: null, isAuth: false });
  },

  setUser: (user) => set({ user }),

  loadOnboardingFlag: async () => {
    const value = await AsyncStorage.getItem("onboarding_completed");
    set({ onboardingDone: value === "1" });
  },

  markOnboardingDone: async () => {
    await AsyncStorage.setItem("onboarding_completed", "1");
    set({ onboardingDone: true });
  },

  resetOnboarding: async () => {
    await AsyncStorage.removeItem("onboarding_completed");
    set({ onboardingDone: false });
  },

  checkAuth: async () => {
    try {
      const token = await AsyncStorage.getItem("access_token");
      if (!token) {
        set({ isLoading: false });
        return;
      }
      const res = await api.get("/users/me");
      set({ user: res.data, isAuth: true, isLoading: false });
    } catch {
      await AsyncStorage.multiRemove(["access_token", "refresh_token"]);
      set({ user: null, isAuth: false, isLoading: false });
    }
  },
}));
