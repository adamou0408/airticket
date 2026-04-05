/**
 * Search history list item — with save/bookmark toggle.
 */
import { View, Text, StyleSheet, Pressable } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, borderRadius, fontSize, spacing, touchTarget } from '../theme/tokens';
import type { SearchHistoryItem as HistoryItem } from '../hooks/useSearchHistory';

interface Props {
  item: HistoryItem;
  onPress: () => void;
  onToggleSaved: () => void;
  onDelete: () => void;
}

export function SearchHistoryCard({ item, onPress, onToggleSaved, onDelete }: Props) {
  const date = new Date(item.searched_at);
  const dateStr = `${date.getMonth() + 1}/${date.getDate()} ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`;

  return (
    <Pressable onPress={onPress} style={({ pressed }) => [styles.container, pressed && styles.pressed]}>
      <View style={styles.content}>
        <View style={styles.routeRow}>
          <Text style={styles.route}>{item.origin} → {item.destination}</Text>
          <Text style={styles.date}>{dateStr}</Text>
        </View>

        <Text style={styles.dates}>
          {item.departure_date} ~ {item.return_date} · {item.passengers}人
        </Text>

        <View style={styles.resultRow}>
          {item.best_price != null && (
            <Text style={styles.price}>最低 ${item.best_price.toLocaleString()}</Text>
          )}
          <Text style={styles.count}>{item.result_count} 個組合</Text>
          {item.note ? (
            <Text style={styles.note} numberOfLines={1}>📝 {item.note}</Text>
          ) : null}
        </View>
      </View>

      <View style={styles.actions}>
        <Pressable onPress={onToggleSaved} hitSlop={12} style={styles.actionBtn}>
          <Ionicons
            name={item.saved ? 'bookmark' : 'bookmark-outline'}
            size={22}
            color={item.saved ? colors.saved : colors.textMuted}
          />
        </Pressable>
        <Pressable onPress={onDelete} hitSlop={12} style={styles.actionBtn}>
          <Ionicons name="close-circle-outline" size={20} color={colors.textMuted} />
        </Pressable>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderRadius: borderRadius.md,
    padding: spacing.lg,
    marginBottom: spacing.sm,
    borderWidth: 1,
    borderColor: colors.borderLight,
  },
  pressed: { backgroundColor: colors.primaryLight },
  content: { flex: 1, gap: spacing.xs },
  routeRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  route: { fontSize: fontSize.lg, fontWeight: '700', color: colors.text },
  date: { fontSize: fontSize.xs, color: colors.textMuted },
  dates: { fontSize: fontSize.sm, color: colors.textSecondary },
  resultRow: { flexDirection: 'row', gap: spacing.md, alignItems: 'center', flexWrap: 'wrap' },
  price: { fontSize: fontSize.sm, fontWeight: '600', color: colors.primary },
  count: { fontSize: fontSize.xs, color: colors.textMuted },
  note: { fontSize: fontSize.xs, color: colors.secondary, flex: 1 },
  actions: { gap: spacing.md, alignItems: 'center', paddingLeft: spacing.md },
  actionBtn: { minHeight: touchTarget.min, justifyContent: 'center' },
});
