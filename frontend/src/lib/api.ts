import { lemmaClient } from '../lemma-client'

export type Row = Record<string, any>

export class ApiError extends Error {
  code: string
  status: number
  constructor(code: string, message: string, status = 400) {
    super(message)
    this.code = code
    this.status = status
  }
}

/** Session token lives here (not in a prop chain) so every call is authenticated. */
let authToken: string | null = null
export const setAuthToken = (token: string | null) => { authToken = token }
export const getAuthToken = () => authToken

function normaliseError(raw: any): ApiError {
  const message = raw?.message ?? String(raw)
  const match = /\[(\d+)\]\s*([A-Z_]+):\s*([^\n(]+)/.exec(message)
  if (match) return new ApiError(match[2], match[3].trim(), Number(match[1]))
  return new ApiError('request_failed', message.replace(/\(request_id=[^)]+\)/, '').trim(), 500)
}

/**
 * Call one AffinityAI service function. Every call goes through the pod function
 * runtime, which owns validation, authorisation and the ML engine — the browser
 * never computes a compatibility score or trusts its own identity.
 */
export async function call<T = Row>(fn: string, action: string, payload: Row = {}, token?: string | null): Promise<T> {
  let response: any
  try {
    response = await lemmaClient.functions.run(fn, {
      input: { action, token: token === undefined ? authToken : token, payload },
    })
  } catch (error) {
    throw normaliseError(error)
  }
  const output = response?.output_data ?? response?.outputData ?? null
  if (!output) throw new ApiError('empty_response', 'The service returned no data. Try again.', 502)
  if (!output.ok) {
    const err = output.error ?? {}
    throw new ApiError(err.code ?? 'request_failed', err.message ?? 'Something went wrong.', err.status ?? 400)
  }
  return output.data as T
}

export const api = {
  register: (payload: Row) => call('aa_auth', 'register', payload),
  login: (payload: Row) => call('aa_auth', 'login', payload),
  logout: () => call('aa_auth', 'logout'),
  me: (token?: string | null) => call('aa_auth', 'me', {}, token),
  changePassword: (payload: Row) => call('aa_auth', 'change_password', payload),
  deleteAccount: (payload: Row) => call('aa_auth', 'delete_account', payload),

  profile: () => call('aa_profile', 'get'),
  updateProfile: (payload: Row) => call('aa_profile', 'update', payload),
  publicProfile: (account_id: string) => call('aa_profile', 'public', { account_id }),
  catalog: () => call('aa_profile', 'catalog'),
  resetPersonalisation: () => call('aa_profile', 'reset_personalization'),

  onboarding: () => call('aa_onboarding', 'status'),
  saveProfileStep: (payload: Row) => call('aa_onboarding', 'save_profile', payload),
  saveInterests: (interests: string[]) => call('aa_onboarding', 'save_interests', { interests }),
  saveAnswers: (answers: Row) => call('aa_onboarding', 'save_answers', { answers }),
  savePreferences: (payload: Row) => call('aa_onboarding', 'save_preferences', payload),
  completeOnboarding: (payload: Row) => call('aa_onboarding', 'complete', payload),
  previewProfile: () => call('aa_onboarding', 'preview'),

  recommendations: (payload: Row = {}) => call('aa_discovery', 'recommendations', payload),
  compatibility: (account_id: string) => call('aa_discovery', 'detail', { account_id }),
  feedback: (payload: Row) => call('aa_discovery', 'feedback', payload),
  starters: (account_id: string) => call('aa_discovery', 'starters', { account_id }),

  like: (account_id: string) => call('aa_interactions', 'like', { account_id }),
  pass: (account_id: string) => call('aa_interactions', 'pass', { account_id }),
  save: (account_id: string) => call('aa_interactions', 'save', { account_id }),
  unsave: (account_id: string) => call('aa_interactions', 'unsave', { account_id }),
  block: (account_id: string) => call('aa_interactions', 'block', { account_id }),
  unblock: (account_id: string) => call('aa_interactions', 'unblock', { account_id }),
  report: (payload: Row) => call('aa_interactions', 'report', payload),
  withdraw: (account_id: string) => call('aa_interactions', 'withdraw', { account_id }),
  collections: () => call('aa_interactions', 'summary'),

  matches: () => call('aa_matches', 'list'),
  match: (match_id: string) => call('aa_matches', 'get', { match_id }),
  withdrawMatch: (match_id: string) => call('aa_matches', 'withdraw', { match_id }),

  insights: () => call('aa_insights', 'summary'),
  evaluation: () => call('aa_eval', 'latest', {}),
  runEvaluation: (k = 5) => call('aa_eval', 'run', { k }),
  seedStatus: () => call('aa_seed', 'status', {}, null),
  seed: () => call('aa_seed', 'run'),
}
