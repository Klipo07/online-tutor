// Экран маркетплейса репетиторов с поиском и фильтрами
import { memo, useState, useEffect, useCallback } from "react";
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  Modal,
  ScrollView,
  Alert,
} from "react-native";
import { useRouter } from "expo-router";
import api from "../../services/api";
import { Colors } from "../../constants/theme";
import { Avatar } from "../../components/Avatar";

type Tutor = {
  id: number;
  user_id: number;
  full_name: string;
  subjects: string[];
  price_per_hour: number;
  experience_years: number;
  bio: string | null;
  education: string | null;
  rating: number;
  reviews_count: number;
  is_verified: boolean;
  avatar_url: string | null;
};

type Review = {
  id: number;
  tutor_id: number;
  student_id: number;
  student_name: string;
  rating: number;
  comment: string;
};

type SlotTime = {
  time: string;
  datetime: string;
  available: boolean;
};

type SlotDay = {
  date: string;
  slots: SlotTime[];
};

type SubjectRef = { id: number; name: string };

type TutorCardProps = {
  tutor: Tutor;
  onPress: (t: Tutor) => void;
};

const TutorCard = memo(function TutorCard({ tutor, onPress }: TutorCardProps) {
  const handlePress = useCallback(() => onPress(tutor), [onPress, tutor]);
  return (
    <TouchableOpacity style={styles.card} onPress={handlePress}>
      <Avatar name={tutor.full_name} size={48} />
      <View style={styles.info}>
        <Text style={styles.name}>{tutor.full_name}</Text>
        <Text style={styles.subjects} numberOfLines={1}>
          {tutor.subjects.join(", ")}
        </Text>
        <View style={styles.meta}>
          <Text style={styles.rating}>
            {"\u2B50"} {tutor.rating.toFixed(1)} ({tutor.reviews_count})
          </Text>
          <Text style={styles.experience}>{tutor.experience_years} лет опыта</Text>
        </View>
      </View>
      <View style={styles.priceBox}>
        <Text style={styles.price}>{tutor.price_per_hour} ₽</Text>
        <Text style={styles.priceLabel}>/ час</Text>
      </View>
    </TouchableOpacity>
  );
});

export default function TutorsScreen() {
  const router = useRouter();
  const [tutors, setTutors] = useState<Tutor[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSubject, setSelectedSubject] = useState("Все");
  const [subjectFilters, setSubjectFilters] = useState<string[]>(["Все"]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loadingMore, setLoadingMore] = useState(false);

  // Модальное окно профиля репетитора
  const [selectedTutor, setSelectedTutor] = useState<Tutor | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [reviewsLoading, setReviewsLoading] = useState(false);

  // Форма отзыва
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [reviewRating, setReviewRating] = useState(5);
  const [reviewComment, setReviewComment] = useState("");
  const [submittingReview, setSubmittingReview] = useState(false);

  // Бронирование
  const [bookingOpen, setBookingOpen] = useState(false);
  const [slots, setSlots] = useState<SlotDay[]>([]);
  const [slotsLoading, setSlotsLoading] = useState(false);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [selectedSlot, setSelectedSlot] = useState<string | null>(null);
  const [subjectCatalog, setSubjectCatalog] = useState<SubjectRef[]>([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState<number | null>(null);
  const [bookingLoading, setBookingLoading] = useState(false);

  const loadTutors = useCallback(async (pageNum: number, reset: boolean) => {
    if (reset) setLoading(true);
    else setLoadingMore(true);

    try {
      const params: Record<string, string | number> = {
        page: pageNum,
        per_page: 20,
      };
      if (selectedSubject !== "Все") {
        params.subject = selectedSubject;
      }

      const res = await api.get("/tutors", { params });
      const data = res.data;

      if (reset) {
        setTutors(data.tutors);
      } else {
        setTutors((prev) => [...prev, ...data.tutors]);
      }
      setTotal(data.total);
      setPage(pageNum);
    } catch {
      Alert.alert("Ошибка", "Не удалось загрузить список репетиторов");
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, [selectedSubject]);

  useEffect(() => {
    loadTutors(1, true);
  }, [loadTutors]);

  // Загружаем список предметов из API один раз — для чипов-фильтров
  useEffect(() => {
    api.get("/subjects")
      .then((res) => {
        const names = (res.data as SubjectRef[]).map((s) => s.name);
        setSubjectFilters(["Все", ...names]);
        setSubjectCatalog(res.data);
      })
      .catch(() => {});
  }, []);

  // Загрузка профиля и отзывов репетитора
  const openTutorProfile = useCallback(async (tutor: Tutor) => {
    setSelectedTutor(tutor);
    setReviewsLoading(true);
    try {
      const res = await api.get(`/tutors/${tutor.id}/reviews`);
      setReviews(res.data);
    } catch {
      setReviews([]);
    } finally {
      setReviewsLoading(false);
    }
  }, []);

  // Отправка отзыва
  const submitReview = async () => {
    if (!selectedTutor || !reviewComment.trim()) return;
    setSubmittingReview(true);

    try {
      await api.post(`/tutors/${selectedTutor.id}/review`, {
        rating: reviewRating,
        comment: reviewComment.trim(),
      });

      // Обновляем отзывы
      const res = await api.get(`/tutors/${selectedTutor.id}/reviews`);
      setReviews(res.data);

      // Обновляем данные репетитора в списке
      const tutorRes = await api.get(`/tutors/${selectedTutor.id}`);
      setSelectedTutor(tutorRes.data);
      setTutors((prev) =>
        prev.map((t) => (t.id === selectedTutor.id ? tutorRes.data : t))
      );

      setShowReviewForm(false);
      setReviewComment("");
      setReviewRating(5);
      Alert.alert("Готово", "Отзыв успешно отправлен!");
    } catch (e: any) {
      const msg = e.response?.data?.detail || "Не удалось отправить отзыв";
      Alert.alert("Ошибка", msg);
    } finally {
      setSubmittingReview(false);
    }
  };

  // Открыть форму записи — закрываем профиль и подгружаем слоты
  const openBooking = useCallback(async () => {
    if (!selectedTutor) return;
    setShowReviewForm(false);
    setBookingOpen(true);
    setSelectedDate(null);
    setSelectedSlot(null);
    setSlots([]);
    setSlotsLoading(true);
    try {
      const [slotsRes, subjRes] = await Promise.all([
        api.get(`/tutors/${selectedTutor.id}/slots`, { params: { days: 14 } }),
        subjectCatalog.length ? Promise.resolve({ data: subjectCatalog }) : api.get("/subjects"),
      ]);
      const slotsData: SlotDay[] = slotsRes.data;
      setSlots(slotsData);
      if (slotsData.length) setSelectedDate(slotsData[0].date);

      if (!subjectCatalog.length) {
        setSubjectCatalog(subjRes.data);
      }
      // Подставляем первый предмет репетитора, которому соответствует Subject из каталога
      const catalog: SubjectRef[] = subjectCatalog.length ? subjectCatalog : subjRes.data;
      const matched = catalog.find((s) => selectedTutor.subjects.includes(s.name));
      setSelectedSubjectId(matched?.id ?? catalog[0]?.id ?? null);
    } catch {
      Alert.alert("Ошибка", "Не удалось загрузить расписание репетитора");
      setBookingOpen(false);
    } finally {
      setSlotsLoading(false);
    }
  }, [selectedTutor, subjectCatalog]);

  // Подтвердить запись
  const confirmBooking = async () => {
    if (!selectedTutor || !selectedSlot || !selectedSubjectId) return;
    setBookingLoading(true);
    try {
      const res = await api.post("/sessions", {
        tutor_id: selectedTutor.id,
        subject_id: selectedSubjectId,
        scheduled_at: selectedSlot,
        duration_minutes: 60,
      });
      const dt = new Date(selectedSlot);
      Alert.alert(
        "Занятие забронировано!",
        `${selectedTutor.full_name}\n${dt.toLocaleDateString("ru-RU", {
          day: "numeric",
          month: "long",
        })} в ${dt.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" })}`,
        [
          {
            text: "Перейти к занятию",
            onPress: () => {
              setBookingOpen(false);
              setSelectedTutor(null);
              router.push(`/session/${res.data.id}`);
            },
          },
          {
            text: "Закрыть",
            onPress: () => {
              setBookingOpen(false);
              setSelectedTutor(null);
            },
          },
        ]
      );
    } catch (e: any) {
      const msg = e.response?.data?.detail || "Не удалось забронировать занятие";
      Alert.alert("Ошибка", msg);
    } finally {
      setBookingLoading(false);
    }
  };

  const loadMore = useCallback(() => {
    if (loadingMore || tutors.length >= total) return;
    loadTutors(page + 1, false);
  }, [loadingMore, tutors.length, total, page, loadTutors]);

  const renderTutor = useCallback(
    ({ item }: { item: Tutor }) => (
      <TutorCard tutor={item} onPress={openTutorProfile} />
    ),
    [openTutorProfile],
  );

  const keyExtractor = useCallback((item: Tutor) => item.id.toString(), []);

  return (
    <View style={styles.container}>
      {/* Фильтр по предметам */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.filterContainer}
        contentContainerStyle={styles.filterContent}
      >
        {subjectFilters.map((subject) => (
          <TouchableOpacity
            key={subject}
            style={[
              styles.filterChip,
              selectedSubject === subject && styles.filterChipActive,
            ]}
            onPress={() => setSelectedSubject(subject)}
          >
            <Text
              style={[
                styles.filterText,
                selectedSubject === subject && styles.filterTextActive,
              ]}
            >
              {subject}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Список репетиторов */}
      {loading ? (
        <View style={styles.centered}>
          <ActivityIndicator size="large" color={Colors.primary} />
          <Text style={styles.loadingText}>Загрузка репетиторов...</Text>
        </View>
      ) : tutors.length === 0 ? (
        <View style={styles.centered}>
          <Text style={styles.emptyIcon}>👨‍🏫</Text>
          <Text style={styles.emptyText}>Репетиторы не найдены</Text>
          <Text style={styles.emptySubtext}>Попробуйте выбрать другой предмет</Text>
        </View>
      ) : (
        <FlatList
          data={tutors}
          renderItem={renderTutor}
          keyExtractor={keyExtractor}
          contentContainerStyle={styles.listContent}
          onEndReached={loadMore}
          onEndReachedThreshold={0.5}
          ListFooterComponent={
            loadingMore ? (
              <ActivityIndicator
                size="small"
                color={Colors.primary}
                style={{ paddingVertical: 16 }}
              />
            ) : null
          }
        />
      )}

      {/* Модальное окно — профиль репетитора */}
      <Modal
        visible={selectedTutor !== null}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setSelectedTutor(null)}
      >
        {selectedTutor && (
          <ScrollView style={styles.modalContainer}>
            {/* Шапка профиля */}
            <View style={styles.modalHeader}>
              <TouchableOpacity onPress={() => { setSelectedTutor(null); setShowReviewForm(false); }}>
                <Text style={styles.closeButton}>Закрыть</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.profileHeader}>
              <View style={styles.profileAvatarWrap}>
                <Avatar name={selectedTutor.full_name} size={80} fontSize={28} />
              </View>
              <Text style={styles.profileName}>{selectedTutor.full_name}</Text>
              {selectedTutor.is_verified && (
                <Text style={styles.verifiedBadge}>Проверенный репетитор</Text>
              )}
            </View>

            {/* Статистика */}
            <View style={styles.statsRow}>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>
                  {"\u2B50"} {selectedTutor.rating.toFixed(1)}
                </Text>
                <Text style={styles.statLabel}>Рейтинг</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{selectedTutor.reviews_count}</Text>
                <Text style={styles.statLabel}>Отзывов</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{selectedTutor.experience_years}</Text>
                <Text style={styles.statLabel}>Лет опыта</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{selectedTutor.price_per_hour} ₽</Text>
                <Text style={styles.statLabel}>/ час</Text>
              </View>
            </View>

            {/* Предметы */}
            <View style={styles.profileSection}>
              <Text style={styles.sectionTitle}>Предметы</Text>
              <View style={styles.subjectTags}>
                {selectedTutor.subjects.map((s) => (
                  <View key={s} style={styles.subjectTag}>
                    <Text style={styles.subjectTagText}>{s}</Text>
                  </View>
                ))}
              </View>
            </View>

            {/* О репетиторе */}
            {selectedTutor.bio && (
              <View style={styles.profileSection}>
                <Text style={styles.sectionTitle}>О себе</Text>
                <Text style={styles.bioText}>{selectedTutor.bio}</Text>
              </View>
            )}

            {selectedTutor.education && (
              <View style={styles.profileSection}>
                <Text style={styles.sectionTitle}>Образование</Text>
                <Text style={styles.bioText}>{selectedTutor.education}</Text>
              </View>
            )}

            {/* Кнопка записи */}
            <TouchableOpacity style={styles.bookButton} onPress={openBooking}>
              <Text style={styles.bookButtonText}>Записаться на занятие</Text>
            </TouchableOpacity>

            {/* Отзывы */}
            <View style={styles.profileSection}>
              <View style={styles.reviewsHeader}>
                <Text style={styles.sectionTitle}>
                  Отзывы ({selectedTutor.reviews_count})
                </Text>
                <TouchableOpacity onPress={() => setShowReviewForm(!showReviewForm)}>
                  <Text style={styles.addReviewButton}>
                    {showReviewForm ? "Отмена" : "Написать отзыв"}
                  </Text>
                </TouchableOpacity>
              </View>

              {/* Форма отзыва */}
              {showReviewForm && (
                <View style={styles.reviewForm}>
                  <Text style={styles.reviewFormLabel}>Оценка</Text>
                  <View style={styles.ratingSelector}>
                    {[1, 2, 3, 4, 5].map((star) => (
                      <TouchableOpacity key={star} onPress={() => setReviewRating(star)}>
                        <Text
                          style={[
                            styles.ratingStar,
                            star <= reviewRating && styles.ratingStarActive,
                          ]}
                        >
                          {"\u2B50"}
                        </Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                  <TextInput
                    style={styles.reviewInput}
                    placeholder="Напишите отзыв..."
                    placeholderTextColor={Colors.textSecondary}
                    value={reviewComment}
                    onChangeText={setReviewComment}
                    multiline
                    maxLength={2000}
                  />
                  <TouchableOpacity
                    style={[
                      styles.submitReviewButton,
                      (!reviewComment.trim() || submittingReview) && { opacity: 0.5 },
                    ]}
                    onPress={submitReview}
                    disabled={!reviewComment.trim() || submittingReview}
                  >
                    {submittingReview ? (
                      <ActivityIndicator color="#fff" size="small" />
                    ) : (
                      <Text style={styles.submitReviewText}>Отправить отзыв</Text>
                    )}
                  </TouchableOpacity>
                </View>
              )}

              {/* Список отзывов */}
              {reviewsLoading ? (
                <ActivityIndicator
                  size="small"
                  color={Colors.primary}
                  style={{ marginTop: 16 }}
                />
              ) : reviews.length === 0 ? (
                <Text style={styles.noReviews}>Пока нет отзывов</Text>
              ) : (
                reviews.map((review) => (
                  <View key={review.id} style={styles.reviewCard}>
                    <View style={styles.reviewHeader}>
                      <Text style={styles.reviewAuthor}>{review.student_name}</Text>
                      <Text style={styles.reviewRating}>
                        {"\u2B50"} {review.rating}
                      </Text>
                    </View>
                    <Text style={styles.reviewText}>{review.comment}</Text>
                  </View>
                ))
              )}
            </View>
          </ScrollView>
        )}
      </Modal>

      {/* Модалка выбора слота для бронирования */}
      <Modal
        visible={bookingOpen}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setBookingOpen(false)}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={() => setBookingOpen(false)}>
              <Text style={styles.closeButton}>Закрыть</Text>
            </TouchableOpacity>
          </View>

          {slotsLoading ? (
            <View style={styles.centered}>
              <ActivityIndicator size="large" color={Colors.primary} />
            </View>
          ) : (
            <ScrollView contentContainerStyle={{ padding: 16 }}>
              <Text style={styles.bookingTitle}>Запись к {selectedTutor?.full_name ?? ""}</Text>

              {/* Предмет */}
              {selectedTutor && selectedTutor.subjects.length > 0 && (
                <>
                  <Text style={styles.bookingSection}>Предмет</Text>
                  <View style={styles.chipsRow}>
                    {subjectCatalog
                      .filter((s) => selectedTutor.subjects.includes(s.name))
                      .map((s) => (
                        <TouchableOpacity
                          key={s.id}
                          style={[
                            styles.chip,
                            selectedSubjectId === s.id && styles.chipActive,
                          ]}
                          onPress={() => setSelectedSubjectId(s.id)}
                        >
                          <Text
                            style={[
                              styles.chipText,
                              selectedSubjectId === s.id && styles.chipTextActive,
                            ]}
                          >
                            {s.name}
                          </Text>
                        </TouchableOpacity>
                      ))}
                  </View>
                </>
              )}

              {/* Дата */}
              <Text style={styles.bookingSection}>Дата</Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                <View style={{ flexDirection: "row", gap: 8 }}>
                  {slots.map((day) => {
                    const d = new Date(day.date);
                    const isSel = selectedDate === day.date;
                    return (
                      <TouchableOpacity
                        key={day.date}
                        style={[styles.dateChip, isSel && styles.dateChipActive]}
                        onPress={() => {
                          setSelectedDate(day.date);
                          setSelectedSlot(null);
                        }}
                      >
                        <Text
                          style={[
                            styles.dateDay,
                            isSel && { color: "#fff" },
                          ]}
                        >
                          {d.toLocaleDateString("ru-RU", { weekday: "short" })}
                        </Text>
                        <Text
                          style={[
                            styles.dateNum,
                            isSel && { color: "#fff" },
                          ]}
                        >
                          {d.getDate()}
                        </Text>
                      </TouchableOpacity>
                    );
                  })}
                </View>
              </ScrollView>

              {/* Время */}
              <Text style={styles.bookingSection}>Время</Text>
              <View style={styles.slotsGrid}>
                {(slots.find((d) => d.date === selectedDate)?.slots ?? []).map((s) => {
                  const isSel = selectedSlot === s.datetime;
                  return (
                    <TouchableOpacity
                      key={s.datetime}
                      disabled={!s.available}
                      onPress={() => setSelectedSlot(s.datetime)}
                      style={[
                        styles.slotChip,
                        !s.available && styles.slotChipDisabled,
                        isSel && styles.slotChipActive,
                      ]}
                    >
                      <Text
                        style={[
                          styles.slotText,
                          !s.available && styles.slotTextDisabled,
                          isSel && { color: "#fff" },
                        ]}
                      >
                        {s.time}
                      </Text>
                    </TouchableOpacity>
                  );
                })}
              </View>

              {/* Итог + цена */}
              {selectedTutor && (
                <View style={styles.bookingSummary}>
                  <Text style={styles.summaryLabel}>Стоимость</Text>
                  <Text style={styles.summaryPrice}>{selectedTutor.price_per_hour} ₽</Text>
                </View>
              )}

              <TouchableOpacity
                style={[
                  styles.bookButton,
                  (!selectedSlot || !selectedSubjectId || bookingLoading) && { opacity: 0.5 },
                ]}
                onPress={confirmBooking}
                disabled={!selectedSlot || !selectedSubjectId || bookingLoading}
              >
                {bookingLoading ? (
                  <ActivityIndicator color="#fff" size="small" />
                ) : (
                  <Text style={styles.bookButtonText}>Подтвердить запись</Text>
                )}
              </TouchableOpacity>
            </ScrollView>
          )}
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },

  // Фильтры
  filterContainer: { maxHeight: 56, backgroundColor: Colors.surface, borderBottomWidth: 1, borderBottomColor: Colors.border },
  filterContent: { paddingHorizontal: 16, paddingVertical: 10, gap: 8 },
  filterChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: Colors.inputBg,
    marginRight: 8,
  },
  filterChipActive: { backgroundColor: Colors.primary },
  filterText: { fontSize: 13, color: Colors.textSecondary, fontWeight: "500" },
  filterTextActive: { color: "#fff" },

  // Список
  listContent: { padding: 16 },
  centered: { flex: 1, justifyContent: "center", alignItems: "center" },
  loadingText: { marginTop: 12, color: Colors.textSecondary, fontSize: 14 },
  emptyIcon: { fontSize: 48, marginBottom: 12 },
  emptyText: { fontSize: 18, fontWeight: "600", color: Colors.text },
  emptySubtext: { fontSize: 14, color: Colors.textSecondary, marginTop: 4 },

  // Карточка репетитора
  card: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  info: { flex: 1, marginLeft: 12 },
  name: { fontSize: 15, fontWeight: "600", color: Colors.text },
  subjects: { fontSize: 13, color: Colors.textSecondary, marginTop: 2 },
  meta: { flexDirection: "row", gap: 12, marginTop: 4 },
  rating: { fontSize: 12, color: Colors.warning },
  experience: { fontSize: 12, color: Colors.textSecondary },
  priceBox: { alignItems: "center" },
  price: { fontSize: 16, fontWeight: "700", color: Colors.primary },
  priceLabel: { fontSize: 11, color: Colors.textSecondary },

  // Модальное окно — профиль
  modalContainer: { flex: 1, backgroundColor: Colors.background },
  modalHeader: { padding: 16, alignItems: "flex-end", backgroundColor: Colors.surface, borderBottomWidth: 1, borderBottomColor: Colors.border },
  closeButton: { fontSize: 16, color: Colors.primary, fontWeight: "600" },

  profileHeader: { alignItems: "center", paddingVertical: 24, backgroundColor: Colors.surface },
  profileAvatarWrap: { marginBottom: 12 },
  profileName: { fontSize: 22, fontWeight: "700", color: Colors.text },
  verifiedBadge: {
    marginTop: 8,
    fontSize: 12,
    color: Colors.secondary,
    fontWeight: "600",
    backgroundColor: Colors.secondary + "15",
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
    overflow: "hidden",
  },

  // Статистика
  statsRow: {
    flexDirection: "row",
    backgroundColor: Colors.surface,
    paddingVertical: 16,
    paddingHorizontal: 8,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  statItem: { flex: 1, alignItems: "center" },
  statValue: { fontSize: 16, fontWeight: "700", color: Colors.text },
  statLabel: { fontSize: 11, color: Colors.textSecondary, marginTop: 2 },

  // Секции профиля
  profileSection: { padding: 16, paddingTop: 20 },
  sectionTitle: { fontSize: 17, fontWeight: "700", color: Colors.text, marginBottom: 12 },
  subjectTags: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  subjectTag: {
    backgroundColor: Colors.primary + "15",
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 16,
  },
  subjectTagText: { color: Colors.primary, fontSize: 13, fontWeight: "500" },
  bioText: { fontSize: 14, color: Colors.text, lineHeight: 22 },

  // Кнопка записи
  bookButton: {
    marginHorizontal: 16,
    backgroundColor: Colors.primary,
    borderRadius: 12,
    padding: 16,
    alignItems: "center",
  },
  bookButtonText: { color: "#fff", fontSize: 16, fontWeight: "700" },

  // Отзывы
  reviewsHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 4 },
  addReviewButton: { color: Colors.primary, fontSize: 14, fontWeight: "600" },
  noReviews: { color: Colors.textSecondary, fontSize: 14, marginTop: 8 },
  reviewCard: {
    backgroundColor: Colors.surface,
    borderRadius: 10,
    padding: 14,
    marginTop: 10,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  reviewHeader: { flexDirection: "row", justifyContent: "space-between", marginBottom: 6 },
  reviewAuthor: { fontSize: 14, fontWeight: "600", color: Colors.text },
  reviewRating: { fontSize: 13, color: Colors.warning },
  reviewText: { fontSize: 13, color: Colors.text, lineHeight: 20 },

  // Форма отзыва
  reviewForm: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  reviewFormLabel: { fontSize: 14, fontWeight: "600", color: Colors.text, marginBottom: 8 },
  ratingSelector: { flexDirection: "row", gap: 8, marginBottom: 12 },
  ratingStar: { fontSize: 28, opacity: 0.3 },
  ratingStarActive: { opacity: 1 },
  reviewInput: {
    backgroundColor: Colors.inputBg,
    borderRadius: 10,
    padding: 12,
    fontSize: 14,
    color: Colors.text,
    minHeight: 80,
    textAlignVertical: "top",
  },
  submitReviewButton: {
    backgroundColor: Colors.primary,
    borderRadius: 10,
    padding: 12,
    alignItems: "center",
    marginTop: 12,
  },
  submitReviewText: { color: "#fff", fontSize: 14, fontWeight: "600" },

  // Бронирование — выбор слота
  bookingTitle: { fontSize: 18, fontWeight: "700", color: Colors.text, marginBottom: 4 },
  bookingSection: { fontSize: 13, fontWeight: "700", color: Colors.textSecondary, marginTop: 18, marginBottom: 8, textTransform: "uppercase", letterSpacing: 0.3 },
  chipsRow: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  chip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 18,
    backgroundColor: Colors.inputBg,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  chipActive: { backgroundColor: Colors.primary, borderColor: Colors.primary },
  chipText: { color: Colors.text, fontSize: 13, fontWeight: "500" },
  chipTextActive: { color: "#fff" },
  dateChip: {
    alignItems: "center",
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 12,
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.border,
    minWidth: 56,
  },
  dateChipActive: { backgroundColor: Colors.primary, borderColor: Colors.primary },
  dateDay: { fontSize: 11, color: Colors.textSecondary, textTransform: "uppercase" },
  dateNum: { fontSize: 18, fontWeight: "700", color: Colors.text, marginTop: 2 },
  slotsGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  slotChip: {
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 10,
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.border,
    minWidth: 70,
    alignItems: "center",
  },
  slotChipActive: { backgroundColor: Colors.primary, borderColor: Colors.primary },
  slotChipDisabled: { opacity: 0.35 },
  slotText: { fontSize: 14, fontWeight: "600", color: Colors.text },
  slotTextDisabled: { textDecorationLine: "line-through" },
  bookingSummary: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginTop: 24,
    padding: 14,
    backgroundColor: Colors.surface,
    borderRadius: 12,
  },
  summaryLabel: { fontSize: 14, color: Colors.textSecondary },
  summaryPrice: { fontSize: 20, fontWeight: "800", color: Colors.primary },
});
