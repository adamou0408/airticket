/**
 * Search history with bookmark/save support.
 * Stored locally on device via AsyncStorage.
 */
import { useCallback, useEffect, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

const HISTORY_KEY = 'ticket_search_history';
const MAX_HISTORY = 50;

export interface SearchHistoryItem {
  id: string;
  origin: string;
  destination: string;
  departure_date: string;
  return_date: string;
  passengers: number;
  best_price: number | null;
  direct_price: number | null;
  result_count: number;
  saved: boolean;       // ⭐ 使用者標記的重要搜尋
  searched_at: string;
  note: string;         // 使用者自訂備註
}

export function useSearchHistory() {
  const [history, setHistory] = useState<SearchHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Load history on mount
  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const raw = await AsyncStorage.getItem(HISTORY_KEY);
      if (raw) setHistory(JSON.parse(raw));
    } catch {
      // Ignore
    } finally {
      setLoading(false);
    }
  };

  const saveHistory = async (items: SearchHistoryItem[]) => {
    setHistory(items);
    await AsyncStorage.setItem(HISTORY_KEY, JSON.stringify(items));
  };

  const addSearch = useCallback(async (item: Omit<SearchHistoryItem, 'id' | 'saved' | 'searched_at' | 'note'>) => {
    const newItem: SearchHistoryItem = {
      ...item,
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      saved: false,
      searched_at: new Date().toISOString(),
      note: '',
    };
    const updated = [newItem, ...history].slice(0, MAX_HISTORY);
    await saveHistory(updated);
    return newItem;
  }, [history]);

  const toggleSaved = useCallback(async (id: string) => {
    const updated = history.map(h =>
      h.id === id ? { ...h, saved: !h.saved } : h
    );
    await saveHistory(updated);
  }, [history]);

  const updateNote = useCallback(async (id: string, note: string) => {
    const updated = history.map(h =>
      h.id === id ? { ...h, note } : h
    );
    await saveHistory(updated);
  }, [history]);

  const removeItem = useCallback(async (id: string) => {
    const updated = history.filter(h => h.id !== id);
    await saveHistory(updated);
  }, [history]);

  const clearUnsaved = useCallback(async () => {
    const updated = history.filter(h => h.saved);
    await saveHistory(updated);
  }, [history]);

  const savedOnly = history.filter(h => h.saved);

  return {
    history, savedOnly, loading,
    addSearch, toggleSaved, updateNote, removeItem, clearUnsaved,
  };
}
