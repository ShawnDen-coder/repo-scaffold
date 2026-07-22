export interface ApiErrorItem {
  id?: string
  status?: number
  code?: number
  title?: string
  detail?: string
  source?: unknown
  meta?: unknown
}

export interface ApiErrorResponse {
  errors?: ApiErrorItem[]
}
