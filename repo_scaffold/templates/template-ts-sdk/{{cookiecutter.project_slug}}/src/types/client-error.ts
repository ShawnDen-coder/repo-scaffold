export type ApiClientErrorKind = 'auth_failed' | 'http_error' | 'unexpected'

export class ApiClientError extends Error {
  readonly kind: ApiClientErrorKind
  readonly status?: number
  readonly code?: number
  readonly title?: string
  readonly detail?: string
  readonly cause?: unknown

  constructor(
    message: string,
    options: {
      kind: ApiClientErrorKind
      status?: number
      code?: number
      title?: string
      detail?: string
      cause?: unknown
    },
  ) {
    super(message)
    this.name = 'ApiClientError'
    this.kind = options.kind
    this.status = options.status
    this.code = options.code
    this.title = options.title
    this.detail = options.detail
    this.cause = options.cause
  }
}
