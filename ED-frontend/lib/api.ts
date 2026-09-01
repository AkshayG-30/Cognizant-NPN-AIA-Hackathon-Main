const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8001'

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`)
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`)
  return res.json()
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`)
  return res.json()
}

// ── Types ───────────────────────────────────────────────────────────────────
export type RiskLevel = 'High' | 'Medium' | 'Low'
export type Workspace = 'hospital' | 'insurance'

export interface Patient {
  id: string; bene_id: string; name: string; age: number; risk: number; level: RiskLevel
  ed: number; conditions: string; continuity: string; contact: string; event: string
  status: string; trend: string
  previous_risk?: number
  is_updated?: boolean
  last_updated_at?: string
  update_reason?: string
  phone_masked?: string
  is_demo_target?: boolean
}

export interface Member {
  id: string; patient_id: string; name: string; risk: number; opportunity: string
  impact: string; priority: number; utilization: string; cost: string; gap: string
  action: string; status: string; trajectory: string
  opportunity_score: number; impact_score: number
  avoidable_spend?: string
  financial_summary?: FinancialSummary
  age?: number
  conditions?: string
  continuity?: string
}

export interface FinancialSummary {
  total_journey_cost: number
  avoidable_cost: number
  necessary_cost: number
  avoidable_pct: number
  avoidable_count: number
  avg_encounter_cost: number
  projected_30d_cost: number
}

export interface JourneyEvent {
  event_id?: number
  date: string; type: string; source: string; description: string; status: string; meta: string
  cost?: number
  accumulated_cost?: number
  necessity_status?: string
  necessity_reason?: string
  days_gap?: number
}

export interface GroqAuditResult {
  overall_audit_summary: string
  unnecessary_care_flagged: boolean
  total_avoidable_spend: number
  primary_driver: string
  groq_payer_decision: string
  flagged_encounters: Array<{ encounter: string; cost: string; root_cause: string; preventable_alternative: string }>
  recommended_action_plan: string[]
  projected_savings_roi: string
}

export interface ShapFactor {
  label: string; value: number; description: string; raw_feature: string; raw_value: number
}

export interface Notification {
  id: string; title: string; patient: string; patient_id: string; time: string
  severity: string; action: string; message?: string; previous_risk?: number; current_risk?: number
}

export interface DashboardStats {
  total_patients: number; high_risk: number; medium_risk: number; needs_attention: number
  recent_ed_events: number; missed_appointments: number; high_pct: number; medium_pct: number
  low_pct: number
}

export interface InsuranceDashboardStats {
  total_members: number; high_priority: number; high_opportunity: number; high_impact: number
  active_interventions: number; estimated_impact: string; impact_note: string
  total_population_spend?: string
  avoidable_ed_spend?: string
  avg_journey_cost?: string
}

export interface TrendPoint { month: string; high: number; medium: number; low: number }
export interface UtilPoint { month: string; ed: number; hospital: number; outpatient: number }

// ── API functions ───────────────────────────────────────────────────────────
export const api = {
  health: () => get<{ status: string; model: string; patients: number }>('/api/health'),

  // Patients
  patients: (opts?: { risk?: string; q?: string; limit?: number; offset?: number }) => {
    const params = new URLSearchParams()
    if (opts?.risk && opts.risk !== 'All') params.set('risk', opts.risk)
    if (opts?.q) params.set('q', opts.q)
    if (opts?.limit) params.set('limit', String(opts.limit))
    if (opts?.offset) params.set('offset', String(opts.offset))
    const qs = params.toString()
    return get<{ patients: Patient[]; total: number; total_dataset?: number; top1000_cutoff_risk?: number }>(`/api/patients${qs ? `?${qs}` : ''}`)
  },
  patient: (id: string) => get<Patient>(`/api/patients/${id}`),
  createPatient: (data: { name: string; age: number; sex: string; conditions: string; initial_event_type: string; initial_event_description: string }) =>
    post<{ status: string; patient_id: string; name: string }>('/api/patients', data),
  explanation: (id: string) => get<{ patient_id: string; model: string; risk_score: number; factors: ShapFactor[]; note: string }>(`/api/patients/${id}/explanation`),
  journey: (id: string) => get<{ patient_id: string; events: JourneyEvent[]; financial_summary?: FinancialSummary }>(`/api/patients/${id}/journey`),
  predictRisk: (id: string) =>
    post<{ status: string; patient_id: string; patient_name: string; risk_score: number; previous_risk?: number; risk_level: RiskLevel; predicted_at: string; update_reason: string; factors: ShapFactor[] }>(`/api/patients/${id}/predict`, {}),
  addJourneyEvent: (id: string, event: { type: string; description: string; source?: string }) =>
    post<{ status: string; event: JourneyEvent; updated_risk: number }>(`/api/patients/${id}/journey`, event),
  uploadReport: async (id: string, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    const res = await fetch(`${API}/api/patients/${id}/upload-report`, {
      method: 'POST',
      body: formData,
    })
    if (!res.ok) throw new Error(`Upload failed: ${res.status}`)
    return res.json() as Promise<{ status: string; patient_id: string; event: JourneyEvent; updated_risk: number; updated_level: RiskLevel; factors: ShapFactor[] }>
  },
  uploadMemberReport: async (memberId: string, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    const res = await fetch(`${API}/api/members/${memberId}/upload-report`, {
      method: 'POST',
      body: formData,
    })
    if (!res.ok) throw new Error(`Upload failed: ${res.status}`)
    return res.json() as Promise<{ status: string; patient_id: string; event: JourneyEvent; updated_risk: number; updated_level: RiskLevel; factors: ShapFactor[] }>
  },

  // Alerts
  sendAlert: (id: string, data: { intervention_type: string; message?: string; phone_number?: string }) =>
    post<{ id: string; status: string; twilio_status?: string; provider?: string; masked_phone?: string; is_demo_override?: boolean; note?: string; journey_event?: JourneyEvent }>(`/api/patients/${id}/alert`, data),

  alerts: () => get<{ alerts: Array<{ id: string; patient_name: string; type: string; status: string; created_at: string }> }>('/api/alerts'),

  // Notifications
  notifications: () => get<{ notifications: Notification[] }>('/api/notifications'),

  // Appointments
  updateAppointment: (data: { patient_id: string; outcome: string; notes?: string }) =>
    post<{ id: string; outcome: string }>('/api/appointments', data),
  appointments: () => get<{ appointments: Array<{ id: string; patient_name: string; outcome: string; recorded_at: string }> }>('/api/appointments'),

  // Dashboard
  hospitalDashboard: () => get<DashboardStats>('/api/dashboard/hospital'),
  insuranceDashboard: () => get<InsuranceDashboardStats>('/api/dashboard/insurance'),

  // Members
  members: (opts?: { risk?: string; q?: string; limit?: number; offset?: number }) => {
    const params = new URLSearchParams()
    if (opts?.risk && opts.risk !== 'All') params.set('risk', opts.risk)
    if (opts?.q) params.set('q', opts.q)
    if (opts?.limit) params.set('limit', String(opts.limit))
    if (opts?.offset) params.set('offset', String(opts.offset))
    const qs = params.toString()
    return get<{ members: Member[]; total: number }>(`/api/members${qs ? `?${qs}` : ''}`)
  },
  member: (id: string) => get<Member>(`/api/members/${id}`),
  necessityAnalysis: (memberId: string) => get<{ member_id: string; patient_id: string; patient_name: string; audit: GroqAuditResult; financial_summary?: FinancialSummary }>(`/api/members/${memberId}/necessity-analysis`),

  // Trends & Heatmap
  trends: () => get<{ trend_data: TrendPoint[]; utilization: UtilPoint[] }>('/api/trends'),
  heatmap: () => get<{ cells: Array<{ age_group: string; burden: string; percentage: number; count: number }> }>('/api/heatmap'),

  // Model info
  modelInfo: () => get<{ version: string; type: string; test_roc_auc: number; n_features: number }>('/api/model/info'),
}
