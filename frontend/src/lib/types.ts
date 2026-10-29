export type Dimension = {
  key: string
  label: string
  description: string
  score: number | null
  percent: number | null
  available: boolean
  reason: string
  weight: number
  weight_percent: number
}

export type Split = { key: string; label: string; percent: number }

export type Difference = {
  key: string
  prompt: string
  similarity: number
  you: string | null
  them: string | null
  note?: string
}

export type Starter = { interest: string; text: string; source?: string }

export type Card = {
  account_id: string
  rank?: number | null
  display_name: string
  age: number | null
  city: string | null
  bio: string
  avatar_url: string | null
  initials: string
  is_demo: boolean
  connection_type?: string | null
  interests: string[]
  overall: number
  ranked_score?: number
  label?: string
  coverage_percent: number
  confidence: string
  dimensions: Dimension[]
  top_dimension: { key: string; label: string; percent: number } | null
  shared_interests: string[]
  interest_overlap_count: number
  highlights: string[]
  summary: string
  feedback_adjustment?: number
  missing: { key: string; label: string; reason: string }[]
}

export type Bucket = Omit<Card, 'dimensions' | 'top_dimension' | 'overall' | 'coverage_percent' | 'confidence' | 'shared_interests' | 'highlights' | 'summary' | 'missing' | 'rank'> & {
  shared_interests?: string[]
  discoverable?: boolean
}

export type ProfileBundle = {
  account: { account_id: string; email: string; is_demo: boolean; account_status: string }
  profile: {
    display_name: string
    birth_date: string | null
    age: number | null
    bio: string
    city: string
    avatar_url: string | null
    discoverable: boolean
    show_age: boolean
    show_city: boolean
    onboarding_step: number
    onboarding_completed: boolean
    connection_type: string
  }
  interests: string[]
  answers: Record<string, any>
  preferences: {
    connection_type: string
    min_age: number
    max_age: number
    weights: { shared_interests: number; semantic: number; communication: number; lifestyle: number }
    include_demo: boolean
  }
  completion: { percent: number; checks: { key: string; weight: number; done: boolean }[] }
  counts?: { outgoing_likes: number; saved: number; mutual_matches: number }
  token?: string
}

export type Question = {
  key: string
  dimension: string
  prompt: string
  kind: 'categorical' | 'ordinal' | 'multiselect'
  options: { value: string; label: string }[]
  scale_labels: Record<string, string> | null
  min_selected: number | null
  max_selected: number | null
  required: boolean
}

export type Evaluation = {
  latest: null | {
    run_id: string
    run_at: string
    dataset: string
    k: number
    notes: string
    metrics: Row
  }
  runs: { run_id: string; run_at: string; k: number; precision_at_k: number }[]
  note?: string
}
type Row = Record<string, any>
