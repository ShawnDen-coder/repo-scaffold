import { logger } from '@logger'
import { AuthService, AuthServiceError } from '@auth'
import type {
  AuthCredentials,
  AuthTokens,
  ApiClientOptions,
  ApiErrorResponse,
} from '@types'
import { ApiClientError } from '@types'
import axios, { AxiosError, type AxiosInstance } from 'axios'

export class ApiClient {
  private readonly authService: AuthService
  private readonly httpClient: AxiosInstance
  private readonly credentials: AuthCredentials
  private readonly leewayMs: number
  private tokens: AuthTokens | null = null

  constructor(options: ApiClientOptions) {
    const normalizedBaseUrl = ApiClient.normalizeBaseUrl(options.baseUrl)
    const apiVersion = options.apiVersion ?? 'v1'
    this.leewayMs = options.leewayMs ?? 30_000
    this.credentials = options.credentials

    this.httpClient = axios.create({
      baseURL: `${normalizedBaseUrl}/api/${apiVersion}`,
      timeout: options.timeoutMs ?? 15_000,
      headers: { Accept: 'application/json' },
    })

    this.authService = new AuthService({
      baseUrl: options.baseUrl,
      apiVersion: options.apiVersion,
      timeoutMs: options.timeoutMs,
      maxRetries: options.maxRetries,
      retryBaseDelayMs: options.retryBaseDelayMs,
      httpClient: this.httpClient,
    })
  }

  async get<T>(path: string, params?: Record<string, unknown>): Promise<T> {
    return this.request<T>('GET', path, { params })
  }

  async post<T>(path: string, body?: unknown, params?: Record<string, unknown>): Promise<T> {
    return this.request<T>('POST', path, { data: body, params })
  }

  async put<T>(path: string, body?: unknown, params?: Record<string, unknown>): Promise<T> {
    return this.request<T>('PUT', path, { data: body, params })
  }

  async delete<T>(path: string, params?: Record<string, unknown>): Promise<T> {
    return this.request<T>('DELETE', path, { params })
  }

  private async ensureValidToken(): Promise<string> {
    if (this.tokens === null) {
      logger.info('ApiClient: no token cached, authenticating', {
        grantType: this.credentials.grantType,
      })
      this.tokens = await ApiClient.acquireTokens(() =>
        this.authService.authenticate(this.credentials),
      )
      return this.tokens.accessToken
    }

    if (this.tokens.expiresAt - this.leewayMs < Date.now()) {
      logger.info('ApiClient: token near expiry, attempting refresh')
      try {
        this.tokens = await this.authService.refresh(this.tokens.refreshToken)
      } catch (error) {
        logger.warn('ApiClient: refresh failed, falling back to full auth', {
          error: ApiClient.getErrorMessage(error),
        })
        this.tokens = await ApiClient.acquireTokens(() =>
          this.authService.authenticate(this.credentials),
        )
      }
    }

    return this.tokens.accessToken
  }

  private async request<T>(
    method: string,
    path: string,
    options?: { data?: unknown; params?: Record<string, unknown>; contentType?: string },
  ): Promise<T> {
    const accessToken = await this.ensureValidToken()

    try {
      const response = await this.httpClient.request<T>({
        method,
        url: path,
        params: options?.params,
        data: options?.data,
        headers: {
          Authorization: `Bearer ${accessToken}`,
          ...(options?.contentType ? { 'Content-Type': options.contentType } : {}),
        },
      })
      return response.data
    } catch (error) {
      throw ApiClient.toClientError(error)
    }
  }

  private static async acquireTokens(fn: () => Promise<AuthTokens>): Promise<AuthTokens> {
    try {
      return await fn()
    } catch (error) {
      if (error instanceof AuthServiceError) {
        throw new ApiClientError(error.message, {
          kind: 'auth_failed',
          status: error.status,
          code: error.code,
          title: error.title,
          detail: error.detail,
          cause: error,
        })
      }
      throw new ApiClientError('Authentication failed.', {
        kind: 'auth_failed',
        cause: error,
      })
    }
  }

  private static toClientError(error: unknown): ApiClientError {
    if (error instanceof AxiosError) {
      const status = error.response?.status
      const errorPayload = error.response?.data as ApiErrorResponse | undefined
      const firstError = errorPayload?.errors?.[0]

      const detail = firstError?.detail
      const title = firstError?.title
      const code = firstError?.code

      const message = detail ?? title ?? error.message ?? 'API request failed.'

      return new ApiClientError(message, {
        kind: 'http_error',
        status,
        code,
        title,
        detail,
        cause: error,
      })
    }

    return new ApiClientError(ApiClient.getErrorMessage(error), {
      kind: 'unexpected',
      cause: error,
    })
  }

  private static normalizeBaseUrl(baseUrl: string): string {
    return baseUrl.replace(/\/+$/, '')
  }

  private static getErrorMessage(error: unknown): string {
    if (error instanceof Error) {
      return error.message
    }
    return 'Unknown error'
  }
}
