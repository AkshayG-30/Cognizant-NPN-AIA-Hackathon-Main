export type RiskLevel = 'High' | 'Medium' | 'Low'
export type Workspace = 'hospital' | 'insurance'

export const patients = [
  { id: 'P-1042', name: 'Maya Thompson', age: 72, risk: 0.91, level: 'High' as RiskLevel, ed: 3, conditions: 'CHF, COPD', continuity: 'Fragmented', contact: 'Mar 24, 2026', event: 'Missed cardiology appointment', status: 'Needs outreach', trend: '+0.08' },
  { id: 'P-1088', name: 'Robert Chen', age: 68, risk: 0.84, level: 'High' as RiskLevel, ed: 2, conditions: 'Diabetes, CKD', continuity: 'Low', contact: 'Mar 22, 2026', event: 'ED visit · 2 days ago', status: 'Assigned', trend: '+0.04' },
  { id: 'P-1007', name: 'Elena Rodriguez', age: 61, risk: 0.76, level: 'Medium' as RiskLevel, ed: 1, conditions: 'Asthma', continuity: 'Moderate', contact: 'Mar 28, 2026', event: 'Care manager contacted', status: 'In progress', trend: '-0.02' },
  { id: 'P-1120', name: 'James Wilson', age: 79, risk: 0.71, level: 'Medium' as RiskLevel, ed: 1, conditions: 'CHF, HTN', continuity: 'Moderate', contact: 'Mar 19, 2026', event: 'Clinical report uploaded', status: 'Review needed', trend: '+0.01' },
  { id: 'P-1064', name: 'Aisha Patel', age: 55, risk: 0.48, level: 'Low' as RiskLevel, ed: 0, conditions: 'Diabetes', continuity: 'Stable', contact: 'Mar 30, 2026', event: 'Follow-up completed', status: 'Stable', trend: '-0.06' },
  { id: 'P-1099', name: 'Samuel Brooks', age: 66, risk: 0.39, level: 'Low' as RiskLevel, ed: 0, conditions: 'COPD', continuity: 'Stable', contact: 'Mar 29, 2026', event: 'Appointment attended', status: 'Stable', trend: '-0.03' },
]

export const members = [
  { id: 'M-20481', name: 'Maya Thompson', risk: 0.91, opportunity: 'High', impact: 'High', priority: 94, utilization: '3 ED visits', cost: '+18%', gap: 'Cardiology follow-up', action: 'Care coordination', status: 'Queued', trajectory: 'Deteriorating' },
  { id: 'M-20912', name: 'Robert Chen', risk: 0.84, opportunity: 'High', impact: 'Medium', priority: 87, utilization: '2 ED visits', cost: '+11%', gap: 'Diabetes management', action: 'PCP connection', status: 'In review', trajectory: 'Stable' },
  { id: 'M-20107', name: 'Elena Rodriguez', risk: 0.76, opportunity: 'Medium', impact: 'High', priority: 81, utilization: '1 ED visit', cost: '+6%', gap: 'Asthma action plan', action: 'Appointment reminder', status: 'Active', trajectory: 'Improving' },
  { id: 'M-21120', name: 'James Wilson', risk: 0.71, opportunity: 'High', impact: 'High', priority: 84, utilization: '1 ED visit', cost: '+9%', gap: 'Medication review', action: 'Care manager outreach', status: 'Queued', trajectory: 'Deteriorating' },
  { id: 'M-20664', name: 'Aisha Patel', risk: 0.48, opportunity: 'Medium', impact: 'Medium', priority: 55, utilization: '0 ED visits', cost: '-4%', gap: 'Annual wellness visit', action: 'Preventive outreach', status: 'Monitoring', trajectory: 'Improving' },
]

export const journeyEvents = [
  { date: 'Apr 12, 2026', type: 'Clinical report uploaded', source: 'Clinical Report', description: 'Cardiology note reviewed; follow-up recommended within 14 days.', status: 'Review needed', meta: 'Report · Cardiology' },
  { date: 'Apr 09, 2026', type: 'Appointment attended', source: 'Appointment', description: 'Primary care follow-up completed with medication reconciliation.', status: 'Completed', meta: 'Dr. N. Patel · PCP' },
  { date: 'Apr 02, 2026', type: 'Follow-up appointment scheduled', source: 'Care Manager', description: 'Cardiology appointment scheduled after outreach attempt.', status: 'Scheduled', meta: 'Apr 18 · Cardiology' },
  { date: 'Mar 24, 2026', type: 'Care manager contacted patient', source: 'Care Manager', description: 'Patient reached by phone; transportation barrier identified.', status: 'Completed', meta: '12 min call' },
  { date: 'Mar 18, 2026', type: 'Emergency Department Visit', source: 'Claims', description: 'ED encounter for shortness of breath; discharged same day.', status: 'Claims-derived', meta: '3.2 hours · ED' },
]

export const notifications = [
  { title: 'Missed appointment', patient: 'Maya Thompson', time: '12 min ago', severity: 'High', action: 'Review patient' },
  { title: 'New high-risk prediction', patient: 'Robert Chen', time: '48 min ago', severity: 'High', action: 'Open worklist' },
  { title: 'New report ready for review', patient: 'James Wilson', time: '2 hr ago', severity: 'Medium', action: 'Review report' },
  { title: 'Patient response received', patient: 'Elena Rodriguez', time: 'Yesterday', severity: 'Low', action: 'View response' },
]

export const trendData = [
  { month: 'Nov', high: 18, medium: 31, low: 51 }, { month: 'Dec', high: 21, medium: 33, low: 46 }, { month: 'Jan', high: 24, medium: 35, low: 41 }, { month: 'Feb', high: 22, medium: 38, low: 40 }, { month: 'Mar', high: 27, medium: 36, low: 37 }, { month: 'Apr', high: 25, medium: 39, low: 36 },
]

export const shapFactors = [
  { label: 'Prior ED visits', value: 0.15, description: 'Three ED encounters in the prior 12 months.' },
  { label: 'Active asthma', value: 0.12, description: 'Active respiratory condition on recent claims.' },
  { label: 'Care fragmentation', value: 0.08, description: 'Care delivered across multiple disconnected settings.' },
  { label: 'Age', value: 0.04, description: 'Age-related utilization pattern.' },
  { label: 'Recent primary-care contact', value: -0.06, description: 'A recent completed primary-care encounter.' },
  { label: 'Stable utilization', value: -0.03, description: 'No recent inpatient escalation.' },
]

export const navGroups = {
  hospital: [
    { label: 'Dashboard', href: '/hospital', icon: 'LayoutDashboard' }, { label: 'Patients', href: '/hospital/patients', icon: 'Users' }, { label: 'Care Journey', href: '/hospital/care-journey', icon: 'GitBranch' }, { label: 'Appointments', href: '/hospital/appointments', icon: 'CalendarDays' }, { label: 'Alerts', href: '/hospital/alerts', icon: 'Bell' }, { label: 'Reports', href: '/hospital/reports', icon: 'FileText' },
  ],
  insurance: [
    { label: 'Dashboard', href: '/insurance', icon: 'LayoutDashboard' }, { label: 'Members', href: '/insurance/members', icon: 'Users' }, { label: 'Intervention Engine', href: '/insurance/interventions', icon: 'Target' }, { label: 'Trends', href: '/insurance/trends', icon: 'TrendingUp' }, { label: 'Impact / ROI', href: '/insurance/impact', icon: 'BarChart3' },
  ],
}

type NavItem = (typeof navGroups.hospital)[number]
export function navItems(workspace: Workspace): NavItem[] { return navGroups[workspace] }
export function getPatient(id: string) { return patients.find((patient) => patient.id === id) ?? patients[0] }
export function getMember(id: string) { return members.find((member) => member.id === id) ?? members[0] }
