/**
 * Application configuration
 * Environment-aware configuration for development, staging, and production
 */

export interface AppConfig {
  apiUrl: string
  environment: string
  isDevelopment: boolean
  isProduction: boolean
  apiTimeout: number
}

const getApiUrl = (): string => {
  // Development (hot reload from Vite)
  if (import.meta.env.DEV) {
    return import.meta.env.VITE_API_URL || 'http://localhost:5000'
  }

  // Production (API URL set at build time)
  const viteUrl = import.meta.env.VITE_API_URL
  if (viteUrl) {
    return viteUrl
  }

  // Fallback: same origin (when frontend and backend are on same domain)
  return `${window.location.origin}`
}

export const config: AppConfig = {
  apiUrl: getApiUrl(),
  environment: import.meta.env.MODE,
  isDevelopment: import.meta.env.DEV,
  isProduction: import.meta.env.PROD,
  apiTimeout: 30000, // 30 seconds
}

/**
 * API client with configuration
 */
export class ApiClient {
  private baseUrl: string

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || config.apiUrl
  }

  async request<T = any>(
    endpoint: string,
    options: RequestInit & { timeout?: number } = {}
  ): Promise<T> {
    const { timeout = config.apiTimeout, ...fetchOptions } = options
    const url = `${this.baseUrl}${endpoint}`

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), timeout)

    try {
      const response = await fetch(url, {
        ...fetchOptions,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...fetchOptions.headers,
        },
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      return response.json() as Promise<T>
    } catch (error) {
      if (error instanceof TypeError && error.message === 'Failed to fetch') {
        throw new Error(`Failed to connect to API: ${this.baseUrl}`)
      }
      throw error
    } finally {
      clearTimeout(timeoutId)
    }
  }

  get<T = any>(endpoint: string, options?: RequestInit) {
    return this.request<T>(endpoint, { ...options, method: 'GET' })
  }

  post<T = any>(endpoint: string, body?: any, options?: RequestInit) {
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    })
  }

  put<T = any>(endpoint: string, body?: any, options?: RequestInit) {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    })
  }

  patch<T = any>(endpoint: string, body?: any, options?: RequestInit) {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined,
    })
  }

  delete<T = any>(endpoint: string, options?: RequestInit) {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' })
  }
}

export const api = new ApiClient()
