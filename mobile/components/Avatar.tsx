// Переиспользуемый аватар с инициалами или картинкой
import { memo, useMemo } from "react";
import { View, Text, StyleSheet } from "react-native";
import { Image } from "expo-image";
import { Colors, API_URL } from "../constants/theme";

type Props = {
  name: string;
  url?: string | null;
  size?: number;
  fontSize?: number;
};

const API_HOST = API_URL.replace(/\/api\/v1\/?$/, "");

function getInitials(name: string): string {
  return name
    .split(" ")
    .filter(Boolean)
    .map((n) => n[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

function resolveAvatarUrl(url?: string | null): string | null {
  if (!url) return null;
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  return `${API_HOST}${url}`;
}

function AvatarComponent({ name, url, size = 48, fontSize }: Props) {
  const initials = useMemo(() => getInitials(name), [name]);
  const src = useMemo(() => resolveAvatarUrl(url), [url]);
  const textSize = fontSize ?? Math.round(size / 3);
  const wrap = [styles.avatar, { width: size, height: size, borderRadius: size / 2 }];
  if (src) {
    return (
      <View style={wrap}>
        <Image
          source={{ uri: src }}
          style={{ width: size, height: size, borderRadius: size / 2 }}
          contentFit="cover"
          cachePolicy="memory-disk"
          transition={150}
        />
      </View>
    );
  }
  return (
    <View style={wrap}>
      <Text style={[styles.text, { fontSize: textSize }]}>{initials}</Text>
    </View>
  );
}

export const Avatar = memo(AvatarComponent);

const styles = StyleSheet.create({
  avatar: {
    backgroundColor: Colors.primary,
    justifyContent: "center",
    alignItems: "center",
    overflow: "hidden",
  },
  text: { color: "#fff", fontWeight: "700" },
});
