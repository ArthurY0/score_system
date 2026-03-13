/**
 * TDD - Tests written FIRST.
 * User Journey: As a user, I want to log in and have my session persisted,
 * so that I don't need to log in again on page refresh.
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'

describe('Auth Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  it('is not logged in by default when no token in storage', () => {
    const store = useAuthStore()
    expect(store.isLoggedIn).toBe(false)
  })

  it('is logged in after setting a token', () => {
    const store = useAuthStore()
    store.setToken('test-jwt-token')
    expect(store.isLoggedIn).toBe(true)
  })

  it('persists token to localStorage', () => {
    const store = useAuthStore()
    store.setToken('test-jwt-token')
    expect(localStorage.getItem('token')).toBe('test-jwt-token')
  })

  it('sets user correctly', () => {
    const store = useAuthStore()
    store.setUser({ id: 1, username: 'admin', name: '管理员', role: 'admin' })
    expect(store.user?.name).toBe('管理员')
    expect(store.user?.role).toBe('admin')
  })

  it('clears token and user on logout', () => {
    const store = useAuthStore()
    store.setToken('test-jwt-token')
    store.setUser({ id: 1, username: 'admin', name: '管理员', role: 'admin' })
    store.logout()
    expect(store.isLoggedIn).toBe(false)
    expect(store.user).toBeNull()
    expect(localStorage.getItem('token')).toBeNull()
  })

  it('restores login state from localStorage on store init', () => {
    localStorage.setItem('token', 'persisted-token')
    const store = useAuthStore()
    expect(store.isLoggedIn).toBe(true)
  })
})
