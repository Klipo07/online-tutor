// HTTP клиент для работы с backend API
import axios from "axios";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { API_URL } from "../constants/theme";

const api = axios.create({
  baseURL: API_URL,
  timeout: 15000,
  headers: { "Content-Type": "application/json" },
});

// Автоматически добавляем токен к запросам
api.interceptors.request.use(async (config) => {
  const token = await AsyncStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// При 401 — пробуем обновить токен (один раз; если уже пробовали — не зацикливаемся)
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && original && !original._retry) {
      original._retry = true;
      const refreshToken = await AsyncStorage.getItem("refresh_token");
      if (!refreshToken) {
        // Токена нет — значит уже разлогинились, тихо отдаём ошибку
        return Promise.reject(error);
      }
      try {
        const res = await axios.post(`${API_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });
        const { access_token, refresh_token } = res.data;
        await AsyncStorage.setItem("access_token", access_token);
        await AsyncStorage.setItem("refresh_token", refresh_token);
        original.headers.Authorization = `Bearer ${access_token}`;
        return api(original);
      } catch {
        await AsyncStorage.multiRemove(["access_token", "refresh_token"]);
      }
    }
    return Promise.reject(error);
  }
);

export default api;
