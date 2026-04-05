/**
 * Search History Screen — view past searches, bookmark important ones.
 * US-1 extension: history + save/bookmark feature
 */
import { useState } from 'react';
import { View, Text, ScrollView, StyleSheet, Pressable, Alert, TextInput } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, borderRadius, fontSize, spacing } from '../../src/theme/tokens';
import { Button } from '../../src/components/Button';
import { SearchHistoryCard } from '../../src/components/SearchHistoryItem';
import { useSearchHistory, SearchHistoryItem } from '../../src/hooks/useSearchHistory';

type Filter = 'all' | 'saved';

export default function HistoryScreen() {
  const { history, savedOnly, loading, toggleSaved, updateNote, removeItem, clearUnsaved } = useSearchHistory();
  const [filter, setFilter] = useState<Filter>('all');
  const [editingNote, setEditingNote] = useState<string | null>(null);
  const [noteText, setNoteText] = useState('');

  const items = filter === 'saved' ? savedOnly : history;

  const handleStartEditNote = (item: SearchHistoryItem) => {
    setEditingNote(item.id);
    setNoteText(item.note);
  };

  const handleSaveNote = async () => {
    if (editingNote) {
      await updateNote(editingNote, noteText);
      setEditingNote(null);
      setNoteText('');
    }
  };

  const handleClear = () => {
    Alert.alert(
      '清除未標記紀錄',
      '確定要清除所有未標記的搜尋紀錄嗎？已標記（⭐）的紀錄會保留。',
      [
        { text: '取消', style: 'cancel' },
        { text: '確定清除', style: 'destructive', onPress: clearUnsaved },
      ],
    );
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <Text style={styles.emptyText}>載入中...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Filter tabs */}
      <View style={styles.filterRow}>
        <Pressable
          onPress={() => setFilter('all')}
          style={[styles.filterTab, filter === 'all' && styles.filterTabActive]}
        >
          <Text style={[styles.filterText, filter === 'all' && styles.filterTextActive]}>
            全部 ({history.length})
          </Text>
        </Pressable>
        <Pressable
          onPress={() => setFilter('saved')}
          style={[styles.filterTab, filter === 'saved' && styles.filterTabActive]}
        >
          <Ionicons
            name="bookmark"
            size={14}
            color={filter === 'saved' ? colors.primary : colors.textMuted}
          />
          <Text style={[styles.filterText, filter === 'saved' && styles.filterTextActive]}>
            已標記 ({savedOnly.length})
          </Text>
        </Pressable>

        {history.length > 0 && (
          <Pressable onPress={handleClear} style={styles.clearBtn}>
            <Ionicons name="trash-outline" size={16} color={colors.textMuted} />
            <Text style={styles.clearText}>清除</Text>
          </Pressable>
        )}
      </View>

      <ScrollView contentContainerStyle={styles.list}>
        {items.length === 0 ? (
          <View style={styles.center}>
            <Ionicons
              name={filter === 'saved' ? 'bookmark-outline' : 'search-outline'}
              size={48}
              color={colors.textMuted}
            />
            <Text style={styles.emptyText}>
              {filter === 'saved' ? '還沒有標記任何搜尋紀錄' : '還沒有搜尋紀錄'}
            </Text>
            <Text style={styles.emptyHint}>
              {filter === 'saved'
                ? '搜尋後點擊 🔖 可以標記重要的搜尋結果'
                : '去搜機票吧！搜尋結果會自動記錄在這裡'}
            </Text>
          </View>
        ) : (
          items.map(item => (
            <View key={item.id}>
              <SearchHistoryCard
                item={item}
                onPress={() => handleStartEditNote(item)}
                onToggleSaved={() => toggleSaved(item.id)}
                onDelete={() => removeItem(item.id)}
              />

              {/* Note editing inline */}
              {editingNote === item.id && (
                <View style={styles.noteEditor}>
                  <TextInput
                    style={styles.noteInput}
                    value={noteText}
                    onChangeText={setNoteText}
                    placeholder="加個備註（例如：這個組合轉機時間可接受）"
                    placeholderTextColor={colors.textMuted}
                    multiline
                  />
                  <View style={styles.noteActions}>
                    <Button title="取消" variant="ghost" size="sm" onPress={() => setEditingNote(null)} />
                    <Button title="儲存備註" size="sm" onPress={handleSaveNote} />
                  </View>
                </View>
              )}
            </View>
          ))
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  filterRow: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: spacing.lg,
    gap: spacing.sm,
  },
  filterTab: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.full,
    backgroundColor: colors.borderLight,
  },
  filterTabActive: { backgroundColor: colors.primaryLight },
  filterText: { fontSize: fontSize.sm, color: colors.textSecondary },
  filterTextActive: { color: colors.primaryDark, fontWeight: '600' },
  clearBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    marginLeft: 'auto',
    padding: spacing.sm,
  },
  clearText: { fontSize: fontSize.xs, color: colors.textMuted },
  list: { paddingHorizontal: spacing.lg, paddingBottom: 100 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', paddingTop: 80, gap: spacing.md },
  emptyText: { fontSize: fontSize.lg, color: colors.textSecondary, fontWeight: '600' },
  emptyHint: { fontSize: fontSize.sm, color: colors.textMuted, textAlign: 'center', paddingHorizontal: spacing.xxl },
  noteEditor: {
    backgroundColor: colors.surface,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    marginTop: -spacing.xs,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.primary,
  },
  noteInput: {
    fontSize: fontSize.md,
    color: colors.text,
    minHeight: 60,
    textAlignVertical: 'top',
  },
  noteActions: { flexDirection: 'row', justifyContent: 'flex-end', gap: spacing.sm, marginTop: spacing.sm },
});
