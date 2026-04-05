/**
 * Ticket Search Screen — 🎯 First priority feature.
 * US-1: Outstation ticket quick search
 * US-2: Outstation ticket concept explanation
 *
 * Mobile UX focus:
 * - Large input fields, clear CTAs
 * - Swap button for origin/destination
 * - Results sorted by price with savings badge
 * - First-time explanation of outstation tickets
 */
import { useState, useCallback } from 'react';
import {
  View, Text, ScrollView, StyleSheet, Alert,
  KeyboardAvoidingView, Platform, Pressable, Modal,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, borderRadius, fontSize, spacing } from '../src/theme/tokens';
import { Button } from '../src/components/Button';
import { Input } from '../src/components/Input';
import { TicketResultCard } from '../src/components/TicketResultCard';
import { useSearchHistory } from '../src/hooks/useSearchHistory';
import { mockSearchTickets } from '../src/api/mock';
import type { TicketSearchResponse, OutstationTicket } from '../src/api/tickets';

// Popular airports for quick selection
const POPULAR_AIRPORTS = [
  { code: 'TPE', label: '台北桃園' },
  { code: 'NRT', label: '東京成田' },
  { code: 'KIX', label: '大阪關西' },
  { code: 'ICN', label: '首爾仁川' },
  { code: 'BKK', label: '曼谷' },
  { code: 'SIN', label: '新加坡' },
  { code: 'HKG', label: '香港' },
  { code: 'CDG', label: '巴黎' },
  { code: 'LHR', label: '倫敦' },
  { code: 'LAX', label: '洛杉磯' },
];

export default function TicketSearchScreen() {
  const [origin, setOrigin] = useState('TPE');
  const [destination, setDestination] = useState('');
  const [departureDate, setDepartureDate] = useState('');
  const [returnDate, setReturnDate] = useState('');
  const [passengers, setPassengers] = useState('1');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<OutstationTicket[]>([]);
  const [directPrice, setDirectPrice] = useState<number | null>(null);
  const [showExplanation, setShowExplanation] = useState(false);
  const [sortBy, setSortBy] = useState<'price' | 'transit_time'>('price');
  const { addSearch } = useSearchHistory();

  const swapCities = () => {
    setOrigin(destination);
    setDestination(origin);
  };

  const handleSearch = useCallback(async () => {
    if (!origin || !destination || !departureDate || !returnDate) {
      Alert.alert('請填寫完整', '出發地、目的地、去程和回程日期都要填喔');
      return;
    }

    setLoading(true);
    try {
      let data: TicketSearchResponse;
      const pax = parseInt(passengers) || 1;

      try {
        // Try real backend first
        const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000/api';
        const res = await fetch(`${API_URL}/tickets/search`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            origin, destination,
            departure_date: departureDate,
            return_date: returnDate,
            passengers: pax,
            sort_by: sortBy,
          }),
        });
        if (!res.ok) throw new Error('API error');
        data = await res.json();
      } catch {
        // Fallback to demo mode
        data = mockSearchTickets(origin, destination, departureDate, returnDate, pax, sortBy);
      }

      setResults(data.results);
      setDirectPrice(data.direct_price);

      // Save to history
      const bestPrice = data.results.length > 0
        ? Math.min(...data.results.map(r => r.total_price))
        : null;
      await addSearch({
        origin, destination,
        departure_date: departureDate,
        return_date: returnDate,
        passengers: pax,
        best_price: bestPrice,
        direct_price: data.direct_price,
        result_count: data.result_count,
      });
    } catch (err: any) {
      Alert.alert('搜尋失敗', err.message || '請稍後再試');
    } finally {
      setLoading(false);
    }
  }, [origin, destination, departureDate, returnDate, passengers, sortBy, addSearch]);

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
        {/* What is outstation ticket? */}
        <Pressable onPress={() => setShowExplanation(true)} style={styles.explainBanner}>
          <Ionicons name="help-circle-outline" size={18} color={colors.secondary} />
          <Text style={styles.explainText}>什麼是外站票（四段票）？為什麼比較便宜？</Text>
          <Ionicons name="chevron-forward" size={16} color={colors.textMuted} />
        </Pressable>

        {/* Search form */}
        <View style={styles.form}>
          {/* Origin + Destination with swap */}
          <View style={styles.cityRow}>
            <View style={styles.cityInput}>
              <Input
                label="出發地"
                value={origin}
                onChangeText={setOrigin}
                placeholder="TPE"
                autoCapitalize="characters"
              />
            </View>
            <Pressable onPress={swapCities} style={styles.swapBtn}>
              <Ionicons name="swap-horizontal" size={24} color={colors.primary} />
            </Pressable>
            <View style={styles.cityInput}>
              <Input
                label="目的地"
                value={destination}
                onChangeText={setDestination}
                placeholder="NRT"
                autoCapitalize="characters"
              />
            </View>
          </View>

          {/* Quick airport selection */}
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.quickPick}>
            {POPULAR_AIRPORTS.filter(a => a.code !== origin).map(airport => (
              <Pressable
                key={airport.code}
                onPress={() => setDestination(airport.code)}
                style={[styles.chip, destination === airport.code && styles.chipActive]}
              >
                <Text style={[styles.chipText, destination === airport.code && styles.chipTextActive]}>
                  {airport.label}
                </Text>
              </Pressable>
            ))}
          </ScrollView>

          {/* Dates */}
          <View style={styles.dateRow}>
            <View style={{ flex: 1 }}>
              <Input
                label="去程日期"
                value={departureDate}
                onChangeText={setDepartureDate}
                placeholder="2026-07-01"
              />
            </View>
            <View style={{ flex: 1 }}>
              <Input
                label="回程日期"
                value={returnDate}
                onChangeText={setReturnDate}
                placeholder="2026-07-10"
              />
            </View>
          </View>

          {/* Passengers */}
          <View style={styles.passengerRow}>
            <Input
              label="人數"
              value={passengers}
              onChangeText={setPassengers}
              keyboardType="number-pad"
              style={{ textAlign: 'center', width: 60 }}
            />

            {/* Sort toggle */}
            <View style={styles.sortToggle}>
              <Text style={styles.sortLabel}>排序</Text>
              <View style={styles.sortBtns}>
                <Pressable
                  onPress={() => setSortBy('price')}
                  style={[styles.sortBtn, sortBy === 'price' && styles.sortBtnActive]}
                >
                  <Text style={[styles.sortBtnText, sortBy === 'price' && styles.sortBtnTextActive]}>
                    💰 價格
                  </Text>
                </Pressable>
                <Pressable
                  onPress={() => setSortBy('transit_time')}
                  style={[styles.sortBtn, sortBy === 'transit_time' && styles.sortBtnActive]}
                >
                  <Text style={[styles.sortBtnText, sortBy === 'transit_time' && styles.sortBtnTextActive]}>
                    ⏱️ 轉機
                  </Text>
                </Pressable>
              </View>
            </View>
          </View>

          <Button
            title="🔍 搜尋外站票"
            onPress={handleSearch}
            loading={loading}
            size="lg"
          />
        </View>

        {/* Results */}
        {results.length > 0 && (
          <View style={styles.results}>
            <View style={styles.resultsHeader}>
              <Text style={styles.resultsTitle}>
                找到 {results.length} 個外站票組合
              </Text>
              {directPrice && (
                <Text style={styles.directInfo}>
                  直飛參考價：${directPrice.toLocaleString()}
                </Text>
              )}
            </View>
            {results.map((ticket, i) => (
              <TicketResultCard
                key={i}
                ticket={ticket}
                passengers={parseInt(passengers) || 1}
              />
            ))}
          </View>
        )}

        {/* Explanation modal */}
        <Modal visible={showExplanation} animationType="slide" transparent>
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <Text style={styles.modalTitle}>什麼是外站票（四段票）？</Text>

              <Text style={styles.modalText}>
                外站票是一種省錢的機票買法。不直接買「台北→東京」來回票，
                而是買「從另一個城市出發」的來回票，總共會有四段航程：
              </Text>

              <View style={styles.modalRoute}>
                <Text style={styles.modalLeg}>1️⃣ 香港 → 台北（你先飛到出發地）</Text>
                <Text style={styles.modalLeg}>2️⃣ 台北 → 東京（去程）</Text>
                <Text style={styles.modalLeg}>3️⃣ 東京 → 台北（回程）</Text>
                <Text style={styles.modalLeg}>4️⃣ 台北 → 香港（飛回外站城市）</Text>
              </View>

              <Text style={styles.modalText}>
                💡 為什麼比較便宜？{'\n'}
                因為航空公司在不同城市的定價不同，從某些城市出發的票價可能比台北出發便宜很多，
                即使加上往返外站城市的費用，總價還是更低！
              </Text>

              <Button title="了解了！" onPress={() => setShowExplanation(false)} size="lg" />
            </View>
          </View>
        </Modal>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  scroll: { padding: spacing.lg, paddingBottom: 100 },
  explainBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    backgroundColor: colors.secondaryLight,
    padding: spacing.md,
    borderRadius: borderRadius.md,
    marginBottom: spacing.lg,
  },
  explainText: { flex: 1, fontSize: fontSize.sm, color: colors.secondary },
  form: { gap: spacing.lg, marginBottom: spacing.xxl },
  cityRow: { flexDirection: 'row', alignItems: 'flex-end', gap: spacing.sm },
  cityInput: { flex: 1 },
  swapBtn: {
    width: 44, height: 44, borderRadius: 22,
    backgroundColor: colors.primaryLight,
    justifyContent: 'center', alignItems: 'center',
    marginBottom: 2,
  },
  quickPick: { marginTop: -spacing.sm },
  chip: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.full,
    backgroundColor: colors.borderLight,
    marginRight: spacing.sm,
  },
  chipActive: { backgroundColor: colors.primary },
  chipText: { fontSize: fontSize.sm, color: colors.textSecondary },
  chipTextActive: { color: colors.textOnPrimary, fontWeight: '600' },
  dateRow: { flexDirection: 'row', gap: spacing.md },
  passengerRow: { flexDirection: 'row', alignItems: 'flex-end', gap: spacing.lg },
  sortToggle: { flex: 1 },
  sortLabel: { fontSize: fontSize.sm, fontWeight: '600', color: colors.text, marginBottom: spacing.xs, marginLeft: spacing.xs },
  sortBtns: { flexDirection: 'row', gap: spacing.sm },
  sortBtn: {
    flex: 1, paddingVertical: spacing.md,
    borderRadius: borderRadius.md,
    borderWidth: 1.5, borderColor: colors.border,
    alignItems: 'center',
  },
  sortBtnActive: { borderColor: colors.primary, backgroundColor: colors.primaryLight },
  sortBtnText: { fontSize: fontSize.sm, color: colors.textSecondary },
  sortBtnTextActive: { color: colors.primaryDark, fontWeight: '600' },
  results: { gap: spacing.sm },
  resultsHeader: { marginBottom: spacing.md },
  resultsTitle: { fontSize: fontSize.lg, fontWeight: '700', color: colors.text },
  directInfo: { fontSize: fontSize.sm, color: colors.textSecondary, marginTop: spacing.xs },
  modalOverlay: {
    flex: 1, backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: colors.surface,
    borderTopLeftRadius: borderRadius.xl,
    borderTopRightRadius: borderRadius.xl,
    padding: spacing.xxl,
    gap: spacing.lg,
    maxHeight: '85%',
  },
  modalTitle: { fontSize: fontSize.xxl, fontWeight: '700', color: colors.text },
  modalText: { fontSize: fontSize.md, color: colors.textSecondary, lineHeight: 24 },
  modalRoute: {
    backgroundColor: colors.primaryLight,
    padding: spacing.lg,
    borderRadius: borderRadius.md,
    gap: spacing.sm,
  },
  modalLeg: { fontSize: fontSize.md, color: colors.text },
});
