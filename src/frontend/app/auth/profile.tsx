/**
 * Profile screen — login/register + user info.
 */
import { useState } from 'react';
import { View, Text, StyleSheet, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, borderRadius, fontSize, spacing } from '../../src/theme/tokens';
import { Button } from '../../src/components/Button';
import { Input } from '../../src/components/Input';
import { Card } from '../../src/components/Card';

export default function ProfileScreen() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [phone, setPhone] = useState('');
  const [code, setCode] = useState('');
  const [codeSent, setCodeSent] = useState(false);
  const [name, setName] = useState('');

  const handleSendCode = async () => {
    if (!phone) {
      Alert.alert('請輸入電話號碼');
      return;
    }
    // TODO: call API
    setCodeSent(true);
    Alert.alert('驗證碼已發送', '請檢查手機簡訊（開發模式：查看後端 console）');
  };

  const handleVerify = async () => {
    if (!code || code.length !== 6) {
      Alert.alert('請輸入 6 位驗證碼');
      return;
    }
    // TODO: call API and store token
    setIsLoggedIn(true);
    setName('使用者');
  };

  if (!isLoggedIn) {
    return (
      <View style={styles.container}>
        <View style={styles.loginBox}>
          <Ionicons name="person-circle-outline" size={80} color={colors.primary} />
          <Text style={styles.title}>登入 / 註冊</Text>
          <Text style={styles.subtitle}>用電話號碼快速登入，新用戶自動註冊</Text>

          <Input
            label="電話號碼"
            value={phone}
            onChangeText={setPhone}
            placeholder="+886912345678"
            keyboardType="phone-pad"
          />

          {!codeSent ? (
            <Button title="發送驗證碼" onPress={handleSendCode} size="lg" />
          ) : (
            <>
              <Input
                label="驗證碼（6 位數）"
                value={code}
                onChangeText={setCode}
                placeholder="123456"
                keyboardType="number-pad"
                maxLength={6}
              />
              <Button title="登入" onPress={handleVerify} size="lg" />
              <Button title="重新發送" variant="ghost" onPress={handleSendCode} />
            </>
          )}
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Card style={styles.profileCard}>
        <Ionicons name="person-circle" size={64} color={colors.primary} />
        <Text style={styles.name}>{name || '未設定姓名'}</Text>
        <Text style={styles.phone}>{phone}</Text>
      </Card>

      <Card>
        <Button title="編輯姓名" variant="outline" onPress={() => {}} />
      </Card>

      <Button
        title="登出"
        variant="ghost"
        onPress={() => {
          setIsLoggedIn(false);
          setCodeSent(false);
          setCode('');
        }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1, backgroundColor: colors.background,
    padding: spacing.xxl, gap: spacing.lg,
  },
  loginBox: {
    flex: 1, justifyContent: 'center', alignItems: 'center',
    gap: spacing.lg,
  },
  title: { fontSize: fontSize.xxl, fontWeight: '700', color: colors.text },
  subtitle: { fontSize: fontSize.md, color: colors.textSecondary, textAlign: 'center', marginBottom: spacing.md },
  profileCard: { alignItems: 'center', gap: spacing.md },
  name: { fontSize: fontSize.xl, fontWeight: '700', color: colors.text },
  phone: { fontSize: fontSize.md, color: colors.textSecondary },
});
