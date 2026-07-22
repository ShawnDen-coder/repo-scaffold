import type { AuthCredentials } from './auth-grants'

export interface ApiClientOptions {
  baseUrl: string
  credentials: AuthCredentials
  apiVersion?: string
  timeoutMs?: number
  maxRetries?: number
  retryBaseDelayMs?: number
  leewayMs?: number
}
