// Стор авторизации — хранит токены и данные пользователя
import { create } from "zustand";
import AsyncStorage from "@react-native-async-storage/async-storage";
import api from "../services/api";

type User = {
  id: number;
  email: string;
  full_name: string;
  role: string;
  avatar_url: string | null;
};

type AuthState = {
  user: User | null;
  isLoading: boolean;
  isAuth: boolean;

  register: (email: string, password: string, fullName: string) => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
};

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: true,
  isAuth: false,

  register: async (email, password, fullName) => {
    const res = await api.post("/auth/register", {
      email,
      password,
      full_name: fullName,
      role: "student",
    });
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
