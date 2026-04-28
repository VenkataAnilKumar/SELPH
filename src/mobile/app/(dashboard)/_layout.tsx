/**
 * Dashboard group layout
 */

import { Stack } from 'expo-router'

export default function DashboardLayout() {
  return (
    <Stack
      screenOptions={{
        headerShown: false,
      }}
    >
      <Stack.Screen 
        name="index" 
        options={{
          title: 'Dashboard',
        }}
      />
    </Stack>
  )
}
