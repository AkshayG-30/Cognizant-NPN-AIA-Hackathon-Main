'use client'

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Activity, AlertCircle, AlertTriangle, ArrowDownRight, ArrowUpRight, BarChart3, Bell, CalendarDays, Check, ChevronDown, CircleHelp, Clock3, FileText, GitBranch, LayoutDashboard, Loader2, Menu, MessageSquare, MoreHorizontal, Phone, Plus, Search, Send, Settings, ShieldCheck, Target, TrendingUp, Upload, Users, X } from 'lucide-react'
import { navItems, type Workspace } from '@/lib/carepath-data'
import { api, type Patient, type Member, type JourneyEvent, type ShapFactor, type Notification, type RiskLevel, type DashboardStats, type InsuranceDashboardStats, type TrendPoint, type UtilPoint } from '@/lib/api'

/* ── Generic fetch hook ──────────────────────────────────────────────────── */
const globalApiCache = new Map<string, any>();

function useApi<T>(fn: () => Promise<T>, deps: unknown[] = []) {
  const cacheKey = useMemo(() => {
    try { return fn.toString() + JSON.stringify(deps); } catch { return ''; }
  }, deps);

  const initialCache = cacheKey && globalApiCache.has(cacheKey) ? globalApiCache.get(cacheKey) : null;
  const [data, setData] = useState<T | null>(initialCache);
  const [loading, setLoading] = useState(!initialCache);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (cacheKey && globalApiCache.has(cacheKey)) {
      setData(globalApiCache.get(cacheKey));
      setLoading(false);
      setError(null);
    }
  }, [cacheKey]);

  const load = useCallback((force = false) => { 
    if (!cacheKey || !globalApiCache.has(cacheKey) || force) setLoading(true); 
    setError(null); 
    fn().then(res => { 
      if (cacheKey) globalApiCache.set(cacheKey, res); 
      setData(res); 
    }).catch(e => setError(e.message)).finally(() => setLoading(false)) 
  }, deps);
  
  useEffect(() => { load() }, [load]);
  
  return { data, loading, error, reload: () => load(true) };
}

function LoadingState() { return <div className="flex items-center justify-center gap-2 py-20 text-slate-500"><Loader2 className="size-5 animate-spin" /><span className="text-sm">Loading…</span></div> }
function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) { return <div className="flex flex-col items-center gap-3 py-20 text-center"><AlertTriangle className="size-6 text-rose-400" /><p className="text-sm text-slate-600">{message}</p>{onRetry && <button onClick={onRetry} className="rounded-lg bg-teal-700 px-3 py-1.5 text-xs font-semibold text-white hover:bg-teal-800">Retry</button>}</div> }

const icons = { LayoutDashboard, Users, GitBranch, CalendarDays, Bell, FileText, Target, TrendingUp, BarChart3 }

function RiskBadge({ level, score }: { level: RiskLevel; score?: number }) {
  const styles = level === 'High' ? 'border-rose-200 bg-rose-50 text-rose-700' : level === 'Medium' ? 'border-amber-200 bg-amber-50 text-amber-700' : 'border-teal-200 bg-teal-50 text-teal-700'
  return <span className={`inline-flex items-center gap-1.5 border px-2 py-1 text-[11px] font-semibold uppercase tracking-[0.12em] ${styles}`}><span className="size-1.5 rounded-full bg-current" />{level}{score !== undefined && <span className="font-mono text-[10px]">{Math.round(score * 100)}%</span>}</span>
}

function Card({ children, className = '' }: { children: React.ReactNode; className?: string }) { return <section className={`border-y border-slate-200 bg-white ${className}`}>{children}</section> }
function SectionTitle({ eyebrow, title, action }: { eyebrow?: string; title: string; action?: React.ReactNode }) { return <div className="flex items-end justify-between gap-4"><div>{eyebrow && <p className="mb-1 text-[10px] font-bold uppercase tracking-[0.2em] text-teal-700">{eyebrow}</p>}<h2 className="text-lg font-semibold tracking-tight text-slate-800">{title}</h2></div>{action}</div> }
function Kpi({ label, value, detail, tone = 'cyan', icon: Icon = Activity }: { label: string; value: string; detail: string; tone?: string; icon?: React.ElementType }) { return <div className="border-l border-slate-200 px-4 py-2 first:border-l-0"><div className="flex items-center gap-2"><p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">{label}</p><Icon className={`size-3.5 ${tone === 'rose' ? 'text-rose-600' : tone === 'amber' ? 'text-amber-600' : 'text-teal-700'}`} /></div><p className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">{value}</p><p className={`mt-1 text-xs ${tone === 'rose' ? 'text-rose-700' : tone === 'amber' ? 'text-amber-700' : 'text-teal-700'}`}>{detail}</p></div> }
function Button({ children, onClick, variant = 'primary', className = '', type = 'button' }: { children: React.ReactNode; onClick?: () => void; variant?: 'primary' | 'secondary' | 'ghost' | 'danger'; className?: string; type?: 'button' | 'submit' }) { const styles = { primary: 'bg-teal-700 text-white hover:bg-teal-800', secondary: 'border border-slate-300 bg-white text-slate-800 hover:bg-slate-100', ghost: 'text-slate-700 hover:bg-slate-100 hover:text-slate-950', danger: 'border border-rose-300 bg-rose-50 text-rose-700 hover:bg-rose-100' }; return <button type={type} onClick={onClick} className={`inline-flex min-h-9 items-center justify-center gap-2 rounded-lg px-3.5 text-xs font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-600 ${styles[variant]} ${className}`}>{children}</button> }

function Sidebar({ workspace, setWorkspace }: { workspace: Workspace; setWorkspace: (value: Workspace) => void }) { const router = useRouter(); const pathname = usePathname(); const [open, setOpen] = useState(false); return <><aside className={`fixed inset-y-0 left-0 z-40 w-64 border-r border-slate-200 bg-slate-50 p-4 transition-transform lg:static lg:translate-x-0 ${open ? 'translate-x-0' : '-translate-x-full'}`}><div className="flex items-center gap-3 px-2 py-3"><div className="grid size-9 place-items-center rounded-xl bg-teal-700 text-slate-950"><Activity className="size-5" /></div><div><p className="text-sm font-bold tracking-tight text-slate-950">CarePath</p><p className="text-[10px] uppercase tracking-[0.16em] text-slate-500">Navigation intelligence</p></div></div><div className="my-5 rounded-xl border border-slate-300/80 bg-white/80 p-1"><button onClick={() => setWorkspace(workspace === 'hospital' ? 'insurance' : 'hospital')} className="flex w-full items-center justify-between rounded-lg px-3 py-2 text-left hover:bg-slate-100"><span><span className="block text-[10px] uppercase tracking-[0.14em] text-slate-500">Workspace</span><span className="text-xs font-semibold text-slate-800">{workspace === 'hospital' ? 'Hospital / Care Mgmt' : 'Insurance / Population'}</span></span><ChevronDown className="size-4 text-slate-500" /></button></div><nav className="flex flex-col gap-1">{navItems(workspace).map((item) => { const Icon = icons[item.icon as keyof typeof icons]; const active = pathname === item.href || (item.href !== '/hospital' && item.href !== '/insurance' && pathname.startsWith(item.href)); return <button key={item.href} onClick={() => { router.push(item.href); setOpen(false) }} className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm transition ${active ? 'bg-teal-700/10 text-teal-800 ring-1 ring-cyan-400/20' : 'text-slate-600 hover:bg-slate-100/80 hover:text-slate-800'}`}><Icon className="size-4" />{item.label}{item.label === 'Alerts' && <span className="ml-auto rounded-full bg-rose-400 px-1.5 py-0.5 text-[10px] font-bold text-slate-950">4</span>}</button> })}</nav><div className="mt-auto hidden border-t border-slate-200 pt-4 lg:block"><button className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-slate-500 hover:bg-slate-100 hover:text-slate-200"><Settings className="size-4" />Settings</button><div className="mt-4 flex items-center gap-3 px-3"><div className="grid size-8 place-items-center rounded-full bg-slate-300 text-xs font-semibold text-teal-800">JD</div><div><p className="text-xs font-medium text-slate-200">Jordan Davis</p><p className="text-[10px] text-slate-500">Care manager</p></div></div></div></aside>{open && <button aria-label="Close navigation" className="fixed inset-0 z-30 bg-slate-100/60 lg:hidden" onClick={() => setOpen(false)} />}</> }

function Header({ workspace, title }: { workspace: Workspace; title: string }) { const router = useRouter(); return <header className="sticky top-0 z-20 flex min-h-16 items-center justify-between border-b border-slate-200/90 bg-white/95 px-4 backdrop-blur lg:px-8"><div className="flex items-center gap-3"><button aria-label="Open navigation" className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 lg:hidden" onClick={() => window.dispatchEvent(new CustomEvent('carepath-menu'))}><Menu className="size-5" /></button><div><p className="hidden text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500 sm:block">{workspace === 'hospital' ? 'Hospital / Care Management' : 'Insurance / Population Analytics'}</p><h1 className="text-sm font-semibold text-slate-800 lg:text-base">{title}</h1></div></div><div className="flex items-center gap-2"><div className="hidden items-center gap-2 rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-600 md:flex"><Search className="size-3.5" />Search patients, members...</div><button onClick={() => router.push(workspace === 'hospital' ? '/hospital/alerts' : '/insurance/interventions')} aria-label="Open notifications" className="relative rounded-lg p-2 text-slate-600 hover:bg-slate-100 hover:text-slate-950"><Bell className="size-4" /><span className="absolute right-1 top-1 size-1.5 rounded-full bg-rose-400" /></button><div className="grid size-8 place-items-center rounded-full border border-slate-600 bg-slate-100 text-[10px] font-bold text-teal-800">JD</div></div></header> }

function LineChart({ insurance = false, data }: { insurance?: boolean; data?: TrendPoint[] }) { const chartData = data ?? []; return <div className="h-56 w-full">{chartData.length === 0 ? <LoadingState /> : <ResponsiveContainer width="100%" height="100%"><AreaChart data={chartData}><CartesianGrid stroke="#223247" strokeDasharray="3 3" vertical={false} /><XAxis dataKey="month" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} /><YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} /><Tooltip contentStyle={{ background: '#ffffff', border: '1px solid #dbe4e8', borderRadius: 4, color: '#1e293b' }} /><Area type="monotone" dataKey={insurance ? 'medium' : 'high'} stroke="#0f766e" strokeWidth={2.5} fill="none" /></AreaChart></ResponsiveContainer>}</div> }
function DistributionChart({ high = 11.5, medium = 88.5, low = 0 }: { high?: number; medium?: number; low?: number }) { const data = [{ name: 'High', value: high, color: '#fb7185' }, { name: 'Medium', value: medium, color: '#fbbf24' }, { name: 'Low', value: low, color: '#2dd4bf' }]; return <div className="flex h-56 items-center gap-4"><ResponsiveContainer width="52%" height="100%"><PieChart><Pie data={data} dataKey="value" innerRadius={58} outerRadius={78} paddingAngle={4}>{data.map((entry) => <Cell key={entry.name} fill={entry.color} />)}</Pie><Tooltip contentStyle={{ background: '#ffffff', border: '1px solid #dbe4e8', borderRadius: 4, color: '#1e293b' }} /></PieChart></ResponsiveContainer><div className="flex flex-col gap-3">{data.map((item) => <div key={item.name} className="flex items-center gap-2 text-xs text-slate-700"><span className="size-2 rounded-full" style={{ background: item.color }} />{item.name}<span className="font-mono text-slate-500">{item.value}%</span></div>)}</div></div> }

function PatientTable({ compact = false }: { compact?: boolean }) {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [filter, setFilter] = useState<'All' | RiskLevel>('All');
  const [offset, setOffset] = useState(0);
  const [pageSize, setPageSize] = useState(compact ? 5 : 200);
  const [isBuffering, setIsBuffering] = useState(false);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedQuery(query);
      setOffset(0);
    }, 400);
    return () => clearTimeout(handler);
  }, [query]);

  const handleFilterChange = (newFilter: 'All' | RiskLevel) => {
    setFilter(newFilter);
    setOffset(0);
  };

  const handleQueryChange = (newQuery: string) => {
    setQuery(newQuery);
  };

  const handlePageSizeChange = (newSize: number) => {
    setPageSize(newSize);
    setOffset(0);
  };

  const fetchPatients = useCallback(async () => {
    setIsBuffering(true);
    try {
      const res = await api.patients({
        risk: filter !== 'All' ? filter : undefined,
        q: debouncedQuery || undefined,
        limit: pageSize,
        offset: offset,
      });
      return res;
    } finally {
      setIsBuffering(false);
    }
  }, [filter, debouncedQuery, pageSize, offset]);

  const { data, loading, error, reload } = useApi(fetchPatients, [filter, debouncedQuery, pageSize, offset]);

  if (loading && offset === 0 && !data) return <Card className="p-8"><LoadingState /></Card>;
  if (error) return <Card className="p-8"><ErrorState message={error} onRetry={reload} /></Card>;

  const pts = data?.patients ?? [];
  const totalFiltered = data?.total ?? 0;
  const totalDs = data?.total_dataset ?? 7754;

  const startIdx = totalFiltered === 0 ? 0 : offset + 1;
  const endIdx = Math.min(offset + pts.length, totalFiltered);
  const totalPages = Math.ceil(totalFiltered / pageSize) || 1;
  const currentPage = Math.floor(offset / pageSize) + 1;

  const handleNextBatch = () => {
    if (offset + pageSize < totalFiltered) {
      setOffset(prev => prev + pageSize);
      window.scrollTo({ top: 300, behavior: 'smooth' });
    }
  };

  const handlePrevBatch = () => {
    if (offset - pageSize >= 0) {
      setOffset(prev => prev - pageSize);
      window.scrollTo({ top: 300, behavior: 'smooth' });
    }
  };

  return (
    <Card className="overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 p-4">
        <div>
          <SectionTitle eyebrow="Action queue" title={compact ? 'Priority patient worklist' : 'Full Patient Database & Worklist'} />
          {!compact && (
            <p className="mt-1 text-xs text-slate-500">
              Showing patients <span className="font-semibold text-teal-800">#{startIdx}–#{endIdx}</span> of <span className="font-semibold text-slate-800">{totalFiltered.toLocaleString()}</span> filtered ({totalDs.toLocaleString()} total database) · Sorted by Risk Score (DESC)
            </p>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {!compact && (
            <div className="flex items-center gap-1 text-xs text-slate-600">
              <span className="text-[11px] font-medium text-slate-500">Batch size:</span>
              <select
                value={pageSize}
                onChange={(e) => handlePageSizeChange(Number(e.target.value))}
                aria-label="Batch size"
                className="rounded-lg border border-slate-300 bg-slate-100/60 px-2 py-1 text-xs font-semibold text-slate-700 outline-none"
              >
                <option value={200}>200 / batch</option>
                <option value={500}>500 / batch</option>
                <option value={1000}>1000 / batch</option>
              </select>
            </div>
          )}
          <div className="flex items-center gap-2 rounded-lg border border-slate-300 bg-slate-100/60 px-2.5 py-1.5">
            <Search className="size-3.5 text-slate-500" />
            <input
              aria-label="Search patients"
              value={query}
              onChange={(e) => handleQueryChange(e.target.value)}
              placeholder="Search ID, name..."
              className="w-28 bg-transparent text-xs text-slate-800 outline-none placeholder:text-slate-500"
            />
          </div>
          <div className="flex items-center gap-1">
            <span className="text-[11px] font-medium text-slate-500 hidden sm:inline">Risk:</span>
            <select
              value={filter}
              onChange={(e) => handleFilterChange(e.target.value as 'All' | RiskLevel)}
              aria-label="Filter by risk"
              className="rounded-lg border border-slate-300 bg-slate-100/60 px-2.5 py-1.5 text-xs font-semibold text-slate-700 outline-none"
            >
              <option value="All">All Risks (7,754)</option>
              <option value="High">High Risk (&gt;80%)</option>
              <option value="Medium">Medium Risk (60-80%)</option>
              <option value="Low">Low Risk (&lt;60%)</option>
            </select>
          </div>
        </div>
      </div>

      {isBuffering && (
        <div className="flex items-center justify-center gap-2 bg-teal-50/80 py-3 text-xs font-semibold text-teal-800 border-b border-teal-200">
          <Loader2 className="size-4 animate-spin text-teal-700" />
          <span>Buffering patient details #{startIdx} to #{startIdx + pageSize - 1} from full database...</span>
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full min-w-[850px] text-left text-xs">
          <thead className="bg-slate-50 text-[10px] uppercase tracking-[0.14em] text-slate-500">
            <tr>
              <th className="px-4 py-3 font-semibold">Rank</th>
              <th className="px-4 py-3 font-semibold">Patient</th>
              <th className="px-4 py-3 font-semibold">Risk</th>
              <th className="px-4 py-3 font-semibold">ED visits</th>
              <th className="px-4 py-3 font-semibold">Conditions</th>
              <th className="px-4 py-3 font-semibold">Continuity</th>
              <th className="px-4 py-3 font-semibold">Last event</th>
              <th className="px-4 py-3 font-semibold">Status</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {pts.length === 0 ? (
              <tr><td colSpan={9} className="py-8 text-center text-xs text-slate-500">No patients found matching criteria</td></tr>
            ) : (
              pts.map((p, idx) => (
                <tr key={p.id} className="group hover:bg-slate-100/40">
                  <td className="px-4 py-3 font-mono text-[11px] font-bold text-slate-400">#{offset + idx + 1}</td>
                  <td className="px-4 py-3">
                    <button onClick={() => router.push(`/hospital/patients/${p.id}`)} className="text-left">
                      <span className="block font-semibold text-slate-800 group-hover:text-teal-800">{p.name}</span>
                      <span className="font-mono text-[10px] text-slate-500">{p.id} · age {p.age}</span>
                    </button>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-col gap-1">
                      <RiskBadge level={p.level as RiskLevel} score={p.risk} />
                      {p.is_updated && (
                        <span className="inline-flex items-center gap-1 text-[9px] font-bold text-amber-700 bg-amber-50 px-1 py-0.5 rounded border border-amber-200">
                          <ArrowUpRight className="size-2.5" /> UPDATED {p.previous_risk !== undefined && `(${Math.round(p.previous_risk * 100)}% → ${Math.round(p.risk * 100)}%)`}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 font-mono text-slate-700">{p.ed}</td>
                  <td className="max-w-32 px-4 py-3 text-slate-600">{p.conditions}</td>
                  <td className="px-4 py-3 text-slate-600">{p.continuity}</td>
                  <td className="max-w-44 px-4 py-3 text-slate-600">{p.event}</td>
                  <td className="px-4 py-3"><span className="rounded-md bg-slate-100 px-2 py-1 text-[10px] text-slate-700">{p.status}</span></td>
                  <td className="px-4 py-3 text-right">
                    <Button onClick={() => router.push(`/hospital/patients/${p.id}`)} variant="ghost" className="h-7 px-2 text-[11px]">
                      View Details <ArrowUpRight className="size-3" />
                    </Button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {!compact && totalFiltered > 0 && (
        <div className="flex flex-wrap items-center justify-between gap-4 border-t border-slate-200 bg-slate-50 px-4 py-3 text-xs">
          <div className="text-slate-600">
            Showing <span className="font-semibold text-slate-900">#{startIdx}</span> to <span className="font-semibold text-slate-900">#{endIdx}</span> of <span className="font-semibold text-slate-900">{totalFiltered.toLocaleString()}</span> patients (Batch {currentPage} of {totalPages})
          </div>
          <div className="flex items-center gap-2">
            <Button
              onClick={handlePrevBatch}
              disabled={offset === 0 || isBuffering}
              variant="secondary"
              className="px-3 py-1 text-xs disabled:opacity-40"
            >
              ← Previous {pageSize}
            </Button>
            <Button
              onClick={handleNextBatch}
              disabled={offset + pageSize >= totalFiltered || isBuffering}
              variant="primary"
              className="bg-teal-700 hover:bg-teal-800 text-white px-4 py-1.5 text-xs font-bold"
            >
              {isBuffering ? (
                <>
                  <Loader2 className="size-3.5 animate-spin" /> Buffering...
                </>
              ) : (
                <>
                  LOAD NEXT {pageSize} PATIENTS →
                </>
              )}
            </Button>
          </div>
        </div>
      )}
    </Card>
  );
}

function HospitalDashboard() { const router = useRouter(); const { data: stats, loading: statsLoading, error: statsError, reload: reloadStats } = useApi(() => api.hospitalDashboard(), []); const { data: trends, loading: trendsLoading, error: trendsError, reload: reloadTrends } = useApi(() => api.trends(), []); const { data: heatmapData, loading: heatmapLoading, error: heatmapError, reload: reloadHeatmap } = useApi(() => api.heatmap(), []); if (statsLoading || trendsLoading || heatmapLoading) return <PageFrame workspace="hospital" title="Care Management"><Card className="p-12"><LoadingState /></Card></PageFrame>; if (statsError || trendsError || heatmapError) return <PageFrame workspace="hospital" title="Care Management"><Card className="p-12"><ErrorState message={statsError || trendsError || heatmapError || 'Failed to load dashboard data'} onRetry={() => { reloadStats(); reloadTrends(); reloadHeatmap(); }} /></Card></PageFrame>; const s = stats ?? { total_patients: 0, high_risk: 0, medium_risk: 0, needs_attention: 0, recent_ed_events: 0, missed_appointments: 0, high_pct: 0, medium_pct: 0, low_pct: 0 }; const cells = heatmapData?.cells ?? []; if (s.total_patients === 0) return <PageFrame workspace="hospital" title="Care Management"><Card className="p-12 text-center text-slate-500"><p className="text-sm font-semibold">No patient panel data available.</p><button onClick={() => { reloadStats(); reloadTrends(); reloadHeatmap(); }} className="mt-3 text-xs font-semibold text-teal-700 hover:underline">Refresh</button></Card></PageFrame>; return <PageFrame workspace="hospital" title="Care Management"><div className="flex flex-col gap-6"><div className="flex flex-wrap items-end justify-between gap-4"><div><p className="text-xs text-slate-500">Tuesday, April 14, 2026 · Northstar Health Network</p><h2 className="mt-1 text-2xl font-semibold tracking-tight text-slate-950">What needs attention today?</h2></div><Button onClick={() => router.push('/hospital/patients')} variant="secondary"><Users className="size-4" />Open patient worklist</Button></div><div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-6"><Kpi label="Total patients" value={String(s.total_patients)} detail="ML-scored population" icon={Users} /><Kpi label="High risk" value={String(s.high_risk)} detail={`${s.high_pct}% of panel`} tone="rose" icon={AlertTriangle} /><Kpi label="Medium risk" value={String(s.medium_risk)} detail={`${s.medium_pct}% of panel`} tone="amber" icon={Activity} /><Kpi label="Needs attention" value={String(s.needs_attention)} detail="Requires outreach" icon={Target} /><Kpi label="Recent ED events" value={String(s.recent_ed_events)} detail="Patients with ED visits" icon={Activity} /><Kpi label="Missed appointments" value={String(s.missed_appointments)} detail="High-risk patients" tone="rose" icon={CalendarDays} /></div><div className="grid gap-4 xl:grid-cols-[1.1fr_.9fr]"><Card className="p-5"><SectionTitle eyebrow="Population signal" title="Risk distribution" action={<span className="text-[10px] text-slate-500">V2 Ensemble model</span>} /><DistributionChart high={s.high_pct} medium={s.medium_pct} low={s.low_pct} /></Card><Card className="p-5"><SectionTitle eyebrow="Six-month view" title="High-risk trend" action={<span className="inline-flex items-center gap-1 text-xs text-rose-700"><ArrowUpRight className="size-3" />+7 pts</span>} /><LineChart data={trends?.trend_data} /></Card></div><Card className="p-5"><SectionTitle eyebrow="Exploration" title="Risk heatmap" action={<Button variant="ghost" onClick={() => router.push('/hospital/patients')}>Drill into patients <ArrowUpRight className="size-3" /></Button>} /><div className="mt-5 grid grid-cols-4 gap-2 text-center text-[10px] text-slate-500"><div /><div>Low burden</div><div>Moderate burden</div><div>High burden</div>{['55-64','65-74','75+'].map((ageKey) => <div key={ageKey} className="contents"><div className="py-4 text-left text-slate-600">Age {ageKey}</div>{['Low','Moderate','High'].map((burdenKey) => { const cell = cells.find((c) => c.age_group === ageKey && c.burden === burdenKey); const pct = cell ? cell.percentage : 0; const bgClass = pct > 20 ? 'bg-rose-500/35' : pct > 10 ? 'bg-amber-400/25' : 'bg-teal-500/20'; return <button key={burdenKey} onClick={() => router.push('/hospital/patients')} className={`rounded-xl border border-slate-300 py-5 text-sm font-semibold text-slate-950 transition hover:scale-[1.02] ${bgClass}`}>{pct}%</button> })}</div>)}</div><p className="mt-4 text-xs text-slate-500">Cells represent the share of the demo panel with a high navigation-opportunity score. Select a cell to open the filtered worklist.</p></Card><PatientTable compact /></div></PageFrame> }

function PatientDetail({ id, subpage }: { id: string; subpage?: string }) {
  const { data: patient, loading, error, reload } = useApi(() => api.patient(id), [id]);
  const router = useRouter();
  const [modal, setModal] = useState<'event' | 'alert' | 'upload' | null>(null);
  const [sent, setSent] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [predicting, setPredicting] = useState(false);
  const [risk, setRisk] = useState(0);
  const [previousRisk, setPreviousRisk] = useState<number | null>(null);
  const [lastPredicted, setLastPredicted] = useState<string | null>(null);
  const [predictError, setPredictError] = useState<string | null>(null);
  const [evType, setEvType] = useState('Patient contacted');
  const [evDesc, setEvDesc] = useState('');
  const [journeyKey, setJourneyKey] = useState(0);
  const [explanationKey, setExplanationKey] = useState(0);

  useEffect(() => {
    if (patient) {
      setRisk(patient.risk);
      if (patient.previous_risk !== undefined) setPreviousRisk(patient.previous_risk);
      if (patient.last_updated_at) setLastPredicted(patient.last_updated_at);
    }
  }, [patient]);

  if (loading) return <PageFrame workspace="hospital" title="Loading…"><LoadingState /></PageFrame>;
  if (error || !patient) return <PageFrame workspace="hospital" title="Error"><ErrorState message={error ?? 'Patient not found'} onRetry={reload} /></PageFrame>;

  const title = subpage === 'journey' ? 'Care journey' : subpage === 'explanation' ? 'Risk explanation' : subpage === 'alerts' ? 'Patient alert' : 'Patient overview';

  const handlePredictRisk = async () => {
    try {
      setPredicting(true);
      setPredictError(null);
      const res = await api.predictRisk(id);
      setRisk(res.risk_score);
      if (res.previous_risk !== undefined) setPreviousRisk(res.previous_risk);
      setLastPredicted(res.predicted_at || 'Just now');
      setExplanationKey(k => k + 1);
      setJourneyKey(k => k + 1);
      reload();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Prediction failed';
      setPredictError(msg);
    } finally {
      setPredicting(false);
    }
  };

  const handleAddEvent = async () => {
    try {
      const res = await api.addJourneyEvent(id, { type: evType, description: evDesc || `${evType} recorded.` });
      setRisk(res.updated_risk);
      setModal(null);
      setEvDesc('');
      setJourneyKey(k => k + 1);
      setExplanationKey(k => k + 1);
      reload();
    } catch {}
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      setUploading(true);
      const res = await api.uploadReport(id, file);
      setRisk(res.updated_risk);
      setModal(null);
      setJourneyKey(k => k + 1);
      setExplanationKey(k => k + 1);
      reload();
    } catch (err) {
      alert('Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleAlert = async () => {
    try {
      await api.sendAlert(id, { intervention_type: 'Care follow-up' });
      setSent(true);
      setModal(null);
    } catch {}
  };

  return (
    <PageFrame workspace="hospital" title={`${patient.name} · ${title}`}>
      <div className="flex flex-col gap-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <button onClick={() => router.push('/hospital/patients')} className="mb-3 text-xs text-slate-500 hover:text-teal-800">← Back to patients</button>
            <div className="flex flex-wrap items-center gap-3">
              <h2 className="text-2xl font-semibold text-slate-950">{patient.name}</h2>
              <RiskBadge level={risk > .8 ? 'High' : risk > .6 ? 'Medium' : 'Low'} score={risk} />
            </div>
            <p className="mt-1 font-mono text-xs text-slate-500 flex flex-wrap items-center gap-2">
              <span>{patient.id} · age {patient.age} · updated {lastPredicted ?? 'recently'}</span>
              <span className="text-slate-300">|</span>
              <span className="flex items-center gap-1 font-semibold text-teal-800">
                <Phone className="size-3" />
                {patient.phone_masked ?? '******0435'}
              </span>
              {patient.is_demo_target && (
                <span className="rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-bold text-amber-800">
                  DEMO OVERRIDE
                </span>
              )}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button onClick={handlePredictRisk} disabled={predicting} className="bg-teal-800 text-white hover:bg-teal-900">
              {predicting ? <Loader2 className="size-4 animate-spin" /> : <Activity className="size-4" />}
              {predicting ? 'Predicting...' : 'Predict Risk'}
            </Button>
            <Button onClick={() => setModal('alert')}><Send className="size-4" />Alert patient</Button>
            <Button variant="secondary" onClick={() => setModal('event')}><Plus className="size-4" />Update journey</Button>
            <Button variant="secondary" onClick={() => setModal('upload')}><Upload className="size-4" />Upload report</Button>
          </div>
        </div>

        {predictError && (
          <div className="rounded-lg border border-rose-300 bg-rose-50 p-3 text-xs text-rose-700 flex items-center justify-between">
            <span>Prediction failed: {predictError}</span>
            <button onClick={() => setPredictError(null)} className="font-bold">Dismiss</button>
          </div>
        )}

        <div className="grid gap-4 xl:grid-cols-[.85fr_1.15fr]">
          <Card className="border-cyan-400/20 bg-teal-700/[.04] p-5">
            <div className="flex items-center justify-between">
              <p className="text-xs font-medium text-teal-800">Navigation opportunity risk</p>
              <Button onClick={handlePredictRisk} disabled={predicting} className="h-7 text-[11px] px-2.5">
                {predicting ? <Loader2 className="size-3 animate-spin" /> : <Activity className="size-3" />}
                {predicting ? 'Predicting...' : 'Predict Risk'}
              </Button>
            </div>
            <div className="mt-3 flex items-end gap-3">
              <span className="text-5xl font-semibold tracking-tight text-slate-950">{Math.round(risk * 100)}%</span>
              <span className="mb-2"><RiskBadge level={risk > .8 ? 'High' : risk > .6 ? 'Medium' : 'Low'} /></span>
            </div>
            {lastPredicted && (
              <p className="mt-2 text-xs font-semibold text-teal-700">
                Predicted: {lastPredicted}
              </p>
            )}
            {previousRisk !== null && previousRisk !== undefined && (
              <div className="mt-2 text-xs text-amber-800 bg-amber-50 border border-amber-300 rounded p-2 font-mono">
                <span className="font-bold uppercase tracking-wider text-[10px]">Risk updated</span>: {Math.round(previousRisk * 100)}% → {Math.round(risk * 100)}%
              </div>
            )}
            <p className="mt-3 text-xs text-slate-600">Predictive score for care-navigation prioritization, not a medical diagnosis.</p>
            <div className="mt-4 flex items-center gap-2 text-xs text-rose-700"><ArrowUpRight className="size-3" />{patient.trend} since previous assessment</div>
          </Card>

          <Card className="p-5">
            <SectionTitle eyebrow="Patient profile" title="Signals for care management" />
            <div className="mt-5 grid gap-4 sm:grid-cols-2">
              <div><p className="text-[10px] uppercase tracking-[.15em] text-slate-500">Conditions</p><p className="mt-1 text-sm text-slate-800 font-medium">{patient.conditions}</p></div>
              <div><p className="text-[10px] uppercase tracking-[.15em] text-slate-500">Care continuity</p><p className="mt-1 text-sm text-slate-800 font-medium">{patient.continuity}</p></div>
              <div><p className="text-[10px] uppercase tracking-[.15em] text-slate-500">Last primary-care contact</p><p className="mt-1 text-sm text-slate-800 font-medium">{patient.contact}</p></div>
              <div><p className="text-[10px] uppercase tracking-[.15em] text-slate-500">Recent utilization</p><p className="mt-1 text-sm text-slate-800 font-medium">{patient.ed} ED visits · 1 outpatient gap</p></div>
            </div>
          </Card>
        </div>

        {subpage === 'journey' ? (
          <Journey key={journeyKey} patientId={id} onAdd={() => setModal('event')} />
        ) : subpage === 'explanation' ? (
          <Explanation key={explanationKey} patientId={id} />
        ) : subpage === 'alerts' ? (
          <AlertWorkflow
            patientId={id}
            patientName={patient.name}
            patientPhoneMasked={patient.phone_masked}
            isDemoTarget={patient.is_demo_target}
            onComplete={() => {
              setJourneyKey(k => k + 1);
              reload();
            }}
          />
        ) : (
          <div className="grid gap-4 xl:grid-cols-[1.1fr_.9fr]">
            <Journey key={journeyKey} patientId={id} onAdd={() => setModal('event')} />
            <Card className="p-5">
              <SectionTitle eyebrow="Next best action" title="Care team focus" />
              <div className="mt-5 flex flex-col gap-4">
                <div className="rounded-xl border border-amber-400/20 bg-amber-400/[.06] p-4">
                  <p className="text-sm font-semibold text-amber-900">Resolve transportation barrier</p>
                  <p className="mt-1 text-xs leading-5 text-slate-600">Patient missed cardiology follow-up. Coordinate transport before the Apr 18 appointment.</p>
                </div>
                <Button onClick={() => setModal('alert')}>Prepare outreach</Button>
                <Button variant="ghost" onClick={() => router.push(`/hospital/patients/${patient.id}/explanation`)}>Review model factors <ArrowUpRight className="size-3" /></Button>
              </div>
            </Card>
          </div>
        )}

        {modal && (
          <Modal title={modal === 'event' ? 'Add journey event' : modal === 'upload' ? 'Upload clinical report' : 'Prepare patient alert'} onClose={() => setModal(null)}>
            <div className="flex flex-col gap-4">
              <p className="text-xs leading-5 text-slate-600">Events are persisted via the backend API and trigger ML model rescoring.</p>
              {modal === 'upload' ? (
                <div className="grid place-items-center rounded-xl border border-dashed border-cyan-400/40 bg-teal-700/[.04] p-10 text-center">
                  <Upload className="size-7 text-teal-700" />
                  <p className="mt-3 text-sm text-slate-800 font-semibold">{uploading ? 'Processing report & rescoring risk profile…' : 'Select a clinical report PDF'}</p>
                  <p className="mt-1 text-xs text-slate-500">PDF, DOCX, or text file</p>
                  <label className="mt-4 inline-flex cursor-pointer items-center justify-center gap-2 rounded-lg bg-teal-700 px-4 py-2 text-xs font-semibold text-white hover:bg-teal-800">
                    {uploading ? <Loader2 className="size-4 animate-spin" /> : <Upload className="size-4" />}
                    {uploading ? 'Uploading…' : 'Choose file & process'}
                    <input type="file" accept=".pdf,.txt,.docx" className="hidden" onChange={handleFileUpload} disabled={uploading} />
                  </label>
                </div>
              ) : modal === 'event' ? (
                <>
                  <label className="text-xs text-slate-600 font-semibold">Event type
                    <select value={evType} onChange={e => setEvType(e.target.value)} className="mt-2 w-full rounded-lg border border-slate-300 bg-slate-50 p-3 text-sm text-slate-800">
                      <option>Patient contacted</option>
                      <option>Appointment missed</option>
                      <option>Follow-up completed</option>
                      <option>New clinical event</option>
                    </select>
                  </label>
                  <label className="text-xs text-slate-600 font-semibold">Description
                    <textarea value={evDesc} onChange={e => setEvDesc(e.target.value)} className="mt-2 min-h-24 w-full rounded-lg border border-slate-300 bg-slate-50 p-3 text-sm text-slate-800" placeholder="Add context for the care team" />
                  </label>
                  <Button onClick={handleAddEvent}><Check className="size-4" />Save event & rescore</Button>
                </>
              ) : (
                <AlertWorkflow
                  patientId={id}
                  patientName={patient.name}
                  patientPhoneMasked={patient.phone_masked}
                  isDemoTarget={patient.is_demo_target}
                  onComplete={() => {
                    setModal(null);
                    setJourneyKey(k => k + 1);
                    reload();
                  }}
                />
              )}
            </div>
          </Modal>
        )}
      </div>
    </PageFrame>
  );
}


function Journey({ patientId, onAdd }: { patientId: string; onAdd: () => void }) { const { data, loading } = useApi(() => api.journey(patientId), [patientId]); const events = data?.events ?? []; return <Card className="p-5"><SectionTitle eyebrow="Longitudinal record" title="Care journey" action={<Button variant="secondary" onClick={onAdd}><Plus className="size-4" />Add event</Button>} />{loading ? <LoadingState /> : <div className="mt-6 flex flex-col">{events.map((event, index) => <div key={event.date + event.type + index} className="relative flex gap-4 pb-6 last:pb-0"><div className="relative flex w-5 justify-center"><span className={`z-10 mt-1 size-3 rounded-full ring-4 ring-white ${event.source === 'Claims' ? 'bg-violet-300' : event.source === 'Care Manager' ? 'bg-cyan-300' : 'bg-amber-300'}`} />{index < events.length - 1 && <span className="absolute top-4 h-full w-px bg-slate-300" />}</div><div className="flex-1 rounded-xl border border-slate-200 bg-slate-50 p-3"><div className="flex flex-wrap items-center justify-between gap-2"><div><p className="text-xs font-semibold text-slate-800">{event.type}</p><p className="mt-1 text-[10px] text-slate-500">{event.date} · {event.source}</p></div><span className="rounded-md bg-slate-100 px-2 py-1 text-[10px] text-slate-600">{event.status}</span></div><p className="mt-3 text-xs leading-5 text-slate-600">{event.description}</p><p className="mt-2 font-mono text-[10px] text-slate-600">{event.meta}</p></div></div>)}</div>}</Card> }
function Explanation({ patientId }: { patientId: string }) { const { data, loading, error, reload } = useApi(() => api.explanation(patientId), [patientId]); if (loading) return <LoadingState />; if (error) return <ErrorState message={error} onRetry={reload} />; const factors = data?.factors ?? []; const maxVal = Math.max(...factors.map(f => Math.abs(f.value)), 0.01); return <div className="flex flex-col gap-4"><Card className="p-5"><SectionTitle eyebrow="Model-derived explanation" title="Why is this patient high priority?" /><p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">{data?.note ?? 'Feature contributions from the V2 Ensemble model.'}</p><div className="mt-6 flex flex-col gap-3">{factors.map((factor) => <div key={factor.label} className="grid gap-2 sm:grid-cols-[170px_1fr_60px] sm:items-center"><div className="text-xs text-slate-700">{factor.label}</div><div className="h-3 rounded-full bg-slate-100"><div className={`h-3 rounded-full ${factor.value > 0 ? 'bg-rose-400' : 'bg-teal-400'}`} style={{ width: `${Math.abs(factor.value) / maxVal * 100}%` }} /></div><div className={`text-right font-mono text-xs ${factor.value > 0 ? 'text-rose-700' : 'text-teal-700'}`}>{factor.value > 0 ? '+' : ''}{factor.value.toFixed(2)}</div><p className="text-[11px] leading-5 text-slate-500 sm:col-start-2">{factor.description}</p></div>)}</div></Card><details className="rounded-2xl border border-slate-300 bg-white/70 p-5"><summary className="cursor-pointer text-sm font-semibold text-slate-200">How to interpret this</summary><p className="mt-3 text-xs leading-6 text-slate-600">Positive factors increase the model score; negative factors lower it. Contributions are derived from the V2 Ensemble model (ROC-AUC 0.8816) using real feature importance weights.</p></details></div> }

function AlertWorkflow({
  patientId,
  patientName = 'Patient',
  patientPhoneMasked = '******0435',
  isDemoTarget = false,
  onComplete,
}: {
  patientId?: string;
  patientName?: string;
  patientPhoneMasked?: string;
  isDemoTarget?: boolean;
  onComplete?: () => void;
}) {
  const [phoneInput, setPhoneInput] = useState('');
  const [selectedIntervention, setSelectedIntervention] = useState('Care follow-up');
  const [isEditing, setIsEditing] = useState(false);
  const [customMessage, setCustomMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [deliveryResult, setDeliveryResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const templates: Record<string, string> = {
    'Care follow-up': `Hello ${patientName}, your CarePath clinical care team is following up on your care plan. Please call us to confirm your next check-in.`,
    'Appointment reminder': `Hello ${patientName}, this is a reminder from CarePath regarding your upcoming clinical appointment. Please contact your coordinator to confirm.`,
    'Care coordination': `Hello ${patientName}, your multidisciplinary care team has updated your personalized care plan. Please review with your care manager.`,
    'General outreach': `Hello ${patientName}, CarePath health services is checking in on your well-being. Please connect with your primary coordinator.`,
  };

  const currentTemplate = customMessage || templates[selectedIntervention] || templates['Care follow-up'];
  const fullMessageWithDisclaimer = currentTemplate.includes('medical emergency')
    ? currentTemplate
    : `${currentTemplate}\n\nIf you are experiencing a medical emergency, seek emergency care immediately.`;

  const handleInterventionChange = (type: string) => {
    setSelectedIntervention(type);
    setCustomMessage(templates[type] || '');
  };

  const handleSendSMS = async () => {
    if (!patientId) return;
    setIsSending(true);
    setError(null);
    try {
      const res = await api.sendAlert(patientId, {
        intervention_type: selectedIntervention,
        message: currentTemplate,
        phone_number: phoneInput.trim() || undefined,
      });
      setDeliveryResult(res);
      if (onComplete) onComplete();
    } catch (err: any) {
      setError(err?.message || 'Failed to send SMS');
    } finally {
      setIsSending(false);
    }
  };

  return (
    <Card className="p-5 border border-slate-200 bg-white shadow-xl rounded-2xl">
      <SectionTitle
        eyebrow="Real-Time Outreach Gateway"
        title="Prepare Patient Alert"
        action={
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700 ring-1 ring-inset ring-emerald-600/20">
              <span className="size-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Gateway: CarePath SMS Gateway (+91 India)
            </span>
          </div>
        }
      />

      <div className="mt-4 flex flex-col gap-3 rounded-xl border border-slate-200 bg-slate-50/80 p-3.5">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="grid size-9 place-items-center rounded-lg bg-teal-600/10 text-teal-700">
              <Phone className="size-4" />
            </div>
            <div>
              <p className="text-xs font-bold text-slate-900">
                Default Patient Phone: <span className="font-mono text-teal-700">{patientPhoneMasked}</span>
              </p>
              <p className="text-[11px] text-slate-500">
                Target country: <span className="font-bold text-slate-700">🇮🇳 India (+91)</span>
              </p>
            </div>
          </div>
        </div>

        <div className="mt-1 flex flex-col gap-1.5 border-t border-slate-200/80 pt-3">
          <label className="text-[11px] font-bold uppercase tracking-wider text-slate-600">
            Recipient Mobile Phone Number (+91 India)
          </label>
          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <Phone className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
              <input
                type="tel"
                value={phoneInput}
                onChange={(e) => setPhoneInput(e.target.value)}
                placeholder="+91 75980 70435 (Enter your mobile number to test delivery)"
                className="w-full rounded-xl border border-slate-300 bg-white py-2 pl-9 pr-3 text-xs text-slate-900 shadow-sm focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-500/20 font-mono font-medium"
              />
            </div>
            <span className="rounded-lg bg-teal-50 border border-teal-200 px-2.5 py-2 text-[11px] font-bold text-teal-800 flex items-center gap-1">
              🇮🇳 +91
            </span>
          </div>
          <p className="text-[10px] text-slate-500">
            Leave blank to send to default patient phone, or enter your own 10-digit Indian mobile number to dispatch directly to your device.
          </p>
        </div>
      </div>

      {deliveryResult ? (
        <div className="mt-5 rounded-2xl border border-emerald-300 bg-emerald-50/60 p-5">
          <div className="flex items-start gap-3">
            <div className="grid size-10 place-items-center rounded-xl bg-emerald-600 text-white shadow-sm">
              <Check className="size-5" />
            </div>
            <div className="flex-1">
              <h4 className="text-sm font-bold text-emerald-950">SMS Outreach Dispatched & Logged</h4>
              <p className="mt-1 text-xs text-emerald-800 leading-relaxed">
                {deliveryResult.note || `SMS outreach processed for ${deliveryResult.masked_phone || patientPhoneMasked}.`}
              </p>
              <div className="mt-3 grid gap-2 rounded-xl bg-white/80 p-3 text-xs border border-emerald-200">
                <div className="flex justify-between text-slate-700">
                  <span className="font-medium text-slate-500">Delivery Gateway:</span>
                  <span className="font-mono text-teal-800 font-bold">{deliveryResult.provider || 'CarePath SMS Gateway (+91)'}</span>
                </div>
                <div className="flex justify-between text-slate-700">
                  <span className="font-medium text-slate-500">Recipient Phone:</span>
                  <span className="font-mono text-slate-900 font-bold">{deliveryResult.masked_phone || patientPhoneMasked}</span>
                </div>
                <div className="flex justify-between text-slate-700">
                  <span className="font-medium text-slate-500">Status:</span>
                  <span className="font-mono text-emerald-700 font-bold uppercase">{deliveryResult.alert?.status || deliveryResult.status || 'Dispatched'}</span>
                </div>
                <div className="flex justify-between text-slate-700">
                  <span className="font-medium text-slate-500">Care Journey:</span>
                  <span className="text-teal-700 font-medium">Logged in Patient Audit Timeline</span>
                </div>
              </div>
              <div className="mt-4 flex gap-2">
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => {
                    setDeliveryResult(null);
                    setIsEditing(false);
                  }}
                >
                  Send another outreach
                </Button>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="mt-5 space-y-4">
          <div>
            <label className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
              1. Choose Outreach Intervention
            </label>
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              {[
                { type: 'Care follow-up', desc: 'Recommended for high ED utilization & care gaps' },
                { type: 'Appointment reminder', desc: 'Schedule & confirm clinical visit' },
                { type: 'Care coordination', desc: 'Connect with multidisciplinary care team' },
                { type: 'General outreach', desc: 'Wellness check-in & preventive care' },
              ].map((item) => (
                <button
                  key={item.type}
                  type="button"
                  onClick={() => handleInterventionChange(item.type)}
                  className={`rounded-xl border p-3 text-left transition-all ${
                    selectedIntervention === item.type
                      ? 'border-teal-600 bg-teal-50/60 ring-2 ring-teal-500/20 shadow-sm'
                      : 'border-slate-200 bg-slate-50/50 hover:border-slate-300 hover:bg-slate-100/50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-bold text-slate-900">{item.type}</p>
                    {selectedIntervention === item.type && (
                      <span className="size-2 rounded-full bg-teal-600" />
                    )}
                  </div>
                  <p className="mt-1 text-[11px] text-slate-500">{item.desc}</p>
                </button>
              ))}
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between">
              <label className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                2. Message Payload (Formatted)
              </label>
              <button
                type="button"
                onClick={() => setIsEditing(!isEditing)}
                className="flex items-center gap-1 text-xs font-semibold text-teal-700 hover:text-teal-900"
              >
                <MessageSquare className="size-3.5" />
                {isEditing ? 'Done editing' : 'Edit message'}
              </button>
            </div>

            {isEditing ? (
              <div className="mt-2">
                <textarea
                  value={customMessage || currentTemplate}
                  onChange={(e) => setCustomMessage(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 bg-white p-3.5 text-xs text-slate-900 shadow-inner focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-500/20 min-h-24"
                  placeholder="Enter custom outreach message text..."
                />
              </div>
            ) : (
              <div className="mt-2 rounded-xl border border-slate-200 bg-slate-50 p-3.5">
                <p className="text-xs leading-relaxed text-slate-800 font-medium">
                  {currentTemplate}
                </p>
                <div className="mt-2.5 pt-2.5 border-t border-slate-200/80 text-[11px] text-amber-700 font-semibold flex items-center gap-1.5">
                  <AlertCircle className="size-3.5 flex-shrink-0" />
                  <span>If you are experiencing a medical emergency, seek emergency care immediately.</span>
                </div>
              </div>
            )}
            <div className="mt-1 flex justify-between text-[10px] text-slate-400 font-mono">
              <span>Length: {fullMessageWithDisclaimer.length} characters</span>
              <span>1 SMS Segment (GSM-7)</span>
            </div>
          </div>

          {error && (
            <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 flex items-center gap-2">
              <AlertCircle className="size-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="sticky bottom-0 bg-white pt-3 flex items-center justify-between gap-3 border-t border-slate-200">
            <span className="text-[11px] font-medium text-slate-500">
              Gateway: <span className="font-semibold text-teal-800">CarePath SMS (+91 India)</span>
            </span>
            <Button
              onClick={handleSendSMS}
              disabled={isSending}
              className="bg-teal-700 hover:bg-teal-800 text-white font-bold shadow-lg shadow-teal-900/20 px-6 py-2.5 min-h-[40px]"
            >
              {isSending ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  Sending SMS...
                </>
              ) : (
                <>
                  <Send className="size-4" />
                  SEND SMS
                </>
              )}
            </Button>
          </div>
        </div>
      )}
    </Card>
  );
}


function InsuranceDashboard() {
  const router = useRouter();
  const { data: stats } = useApi(() => api.insuranceDashboard(), []);
  const { data: trends } = useApi(() => api.trends(), []);
  const s = stats ?? {
    total_members: 7754,
    high_priority: 1245,
    high_opportunity: 2180,
    high_impact: 1640,
    active_interventions: 642,
    estimated_impact: '$3.1M',
    impact_note: 'AI Audit Opportunity',
    total_population_spend: '$38.4M',
    avoidable_ed_spend: '$8.2M',
    avg_journey_cost: '$4,952'
  };

  return (
    <PageFrame workspace="insurance" title="Population & Financial Analytics">
      <div className="flex flex-col gap-6">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-xs text-slate-500">Tuesday, April 14, 2026 · Meridian Medicare Advantage</p>
            <h2 className="mt-1 text-2xl font-semibold tracking-tight text-slate-950">Payer Cost & Population Health Intelligence</h2>
          </div>
          <Button onClick={() => router.push('/insurance/interventions')}>
            <Target className="size-4" />Open intervention engine
          </Button>
        </div>

        {/* Financial & Population Key Performance Indicators */}
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-6">
          <Kpi label="Total members" value={String(s.total_members)} detail="ML-scored panel" icon={Users} />
          <Kpi label="Total Population Spend" value={s.total_population_spend ?? '$38.4M'} detail="YTD Paid Claims" icon={BarChart3} />
          <Kpi label="Avoidable ED Leakage" value={s.avoidable_ed_spend ?? '$8.2M'} detail="Preventable ED spend (21.3%)" tone="rose" icon={ShieldCheck} />
          <Kpi label="Avg Journey Cost" value={s.avg_journey_cost ?? '$4,952'} detail="Per member episode" icon={TrendingUp} />
          <Kpi label="High priority" value={String(s.high_priority)} detail="Priority > 80" tone="rose" icon={Target} />
          <Kpi label="AI Savings Potential" value={s.estimated_impact} detail={s.impact_note || 'AI Audit Opportunity'} tone="amber" icon={Activity} />
        </div>

        <div className="grid gap-4 xl:grid-cols-2">
          <Card className="p-5">
            <SectionTitle eyebrow="Population signal" title="Risk distribution" />
            <DistributionChart />
          </Card>
          <Card className="p-5">
            <SectionTitle eyebrow="Six-month view" title="Population risk trend" />
            <LineChart insurance data={trends?.trend_data} />
          </Card>
        </div>

        <Card className="p-5">
          <SectionTitle eyebrow="Three-dimensional prioritization" title="Risk + Opportunity + Financial Impact" />
          <div className="mt-5 grid gap-3 md:grid-cols-3">
            {[
              ['RISK', 'How likely to escalate?', 'Predictive ED & Inpatient hospitalization risk from ML Ensemble V2', 'rose'],
              ['OPPORTUNITY', 'Is there an avoidable care gap?', 'Outpatient PCP gap, medication non-adherence, and care fragmentation', 'amber'],
              ['FINANCIAL IMPACT', 'How much spend is preventable?', 'Clinical necessity audit estimating avoidable medical expense leakage', 'cyan']
            ].map(([label, question, detail, tone]) => (
              <div key={label} className={`rounded-xl border p-4 ${tone === 'rose' ? 'border-rose-400/20 bg-rose-400/[.05]' : tone === 'amber' ? 'border-amber-400/20 bg-amber-400/[.05]' : 'border-teal-700/20 bg-teal-700/[.05]'}`}>
                <p className="text-[10px] font-bold tracking-[.18em] text-slate-600">{label}</p>
                <p className="mt-3 text-sm font-semibold text-slate-950">{question}</p>
                <p className="mt-1 text-xs leading-5 text-slate-600">{detail}</p>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </PageFrame>
  );
}

function MemberTable() {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [riskFilter, setRiskFilter] = useState('All');
  const [offset, setOffset] = useState(0);
  const [pageSize, setPageSize] = useState(200);
  const [isBuffering, setIsBuffering] = useState(false);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedQuery(query);
      setOffset(0);
    }, 400);
    return () => clearTimeout(handler);
  }, [query]);

  const { data, loading, error, reload } = useApi(
    () => api.members({ q: debouncedQuery || undefined, risk: riskFilter !== 'All' ? riskFilter : undefined, limit: pageSize, offset }),
    [debouncedQuery, riskFilter, offset, pageSize]
  );

  const handleNextBatch = () => {
    setIsBuffering(true);
    setTimeout(() => {
      setOffset((prev) => prev + pageSize);
      setIsBuffering(false);
    }, 400);
  };

  const handlePrevBatch = () => {
    setIsBuffering(true);
    setTimeout(() => {
      setOffset((prev) => Math.max(0, prev - pageSize));
      setIsBuffering(false);
    }, 400);
  };

  const handleRiskChange = (newRisk: string) => {
    setIsBuffering(true);
    setRiskFilter(newRisk);
    setOffset(0);
    setTimeout(() => setIsBuffering(false), 300);
  };

  const handleSearchChange = (q: string) => {
    setQuery(q);
  };

  if (loading && offset === 0 && !data) return <Card className="p-8"><LoadingState /></Card>;
  if (error) return <Card className="p-8"><ErrorState message={error} onRetry={reload} /></Card>;

  const members = data?.members ?? [];
  const totalFiltered = data?.total ?? 0;
  const startIdx = totalFiltered === 0 ? 0 : offset + 1;
  const endIdx = Math.min(offset + members.length, totalFiltered);
  const totalPages = Math.ceil(totalFiltered / pageSize) || 1;
  const currentPage = Math.floor(offset / pageSize) + 1;

  return (
    <Card className="overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 p-4">
        <SectionTitle eyebrow="Population Financial Analytics" title="Members Financial & Risk Worklist" />
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 rounded-lg border border-slate-300 bg-slate-100/60 px-2.5 py-1.5">
            <Search className="size-3.5 text-slate-500" />
            <input
              aria-label="Search members"
              value={query}
              onChange={(e) => handleSearchChange(e.target.value)}
              placeholder="Search member name or ID..."
              className="w-44 bg-transparent text-xs text-slate-800 outline-none placeholder:text-slate-500"
            />
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[11px] font-medium text-slate-500">Risk level:</span>
            <select
              value={riskFilter}
              onChange={(e) => handleRiskChange(e.target.value)}
              aria-label="Filter members by risk"
              className="rounded-lg border border-slate-300 bg-slate-100/60 px-2.5 py-1.5 text-xs font-semibold text-slate-700 outline-none"
            >
              <option value="All">All Risks (7,754)</option>
              <option value="High">High Risk (&gt;80%)</option>
              <option value="Medium">Medium Risk (60-80%)</option>
              <option value="Low Risk (&lt;60%)">Low Risk (&lt;60%)</option>
            </select>
          </div>
        </div>
      </div>

      {isBuffering && (
        <div className="flex items-center justify-center gap-2 bg-teal-50/80 py-3 text-xs font-semibold text-teal-800 border-b border-teal-200">
          <Loader2 className="size-4 animate-spin text-teal-700" />
          <span>Buffering member details #{startIdx} to #{startIdx + pageSize - 1} from full database...</span>
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full min-w-[1100px] text-left text-xs">
          <thead className="bg-slate-50 text-[10px] uppercase tracking-[.14em] text-slate-500">
            <tr>
              <th className="px-4 py-3 font-semibold">Rank</th>
              <th className="px-4 py-3 font-semibold">Member</th>
              <th className="px-4 py-3 font-semibold">Risk Score</th>
              <th className="px-4 py-3 font-semibold">Total Spend</th>
              <th className="px-4 py-3 font-semibold">Avoidable Leakage</th>
              <th className="px-4 py-3 font-semibold">Priority</th>
              <th className="px-4 py-3 font-semibold">Opportunity</th>
              <th className="px-4 py-3 font-semibold">Care Gap</th>
              <th className="px-4 py-3 font-semibold">Status</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {members.length === 0 ? (
              <tr>
                <td colSpan={10} className="py-8 text-center text-xs text-slate-500">
                  No members found matching criteria
                </td>
              </tr>
            ) : (
              members.map((m, idx) => (
                <tr key={m.id} className="group hover:bg-slate-100/40">
                  <td className="px-4 py-3 font-mono text-[11px] font-bold text-slate-400">#{offset + idx + 1}</td>
                  <td className="px-4 py-3">
                    <button onClick={() => router.push(`/insurance/members/${m.id}`)} className="text-left">
                      <span className="block font-semibold text-slate-800 group-hover:text-teal-800">{m.name}</span>
                      <span className="font-mono text-[10px] text-slate-500">{m.id} · {m.patient_id}</span>
                    </button>
                  </td>
                  <td className="px-4 py-3">
                    <RiskBadge level={m.risk > 0.8 ? 'High' : m.risk > 0.6 ? 'Medium' : 'Low'} score={m.risk} />
                  </td>
                  <td className="px-4 py-3 font-mono font-semibold text-slate-900">{m.cost}</td>
                  <td className="px-4 py-3 font-mono font-bold text-rose-600">
                    <span className="inline-flex items-center gap-1 rounded bg-rose-50 px-2 py-0.5 border border-rose-200">
                      {m.avoidable_spend || '$1,850'}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono font-bold text-slate-900">{m.priority}</td>
                  <td className="px-4 py-3">
                    <span className={`font-semibold ${m.opportunity === 'High' ? 'text-amber-700' : 'text-slate-600'}`}>{m.opportunity}</span>
                  </td>
                  <td className="px-4 py-3 text-slate-600">{m.gap}</td>
                  <td className="px-4 py-3">
                    <span className="rounded-md bg-slate-100 px-2 py-1 text-[10px] text-slate-700">{m.status}</span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Button onClick={() => router.push(`/insurance/members/${m.id}`)} variant="ghost" className="h-7 px-2 text-[11px] text-teal-800 font-bold">
                      Audit & Journey <ArrowUpRight className="size-3" />
                    </Button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {totalFiltered > 0 && (
        <div className="flex flex-wrap items-center justify-between gap-4 border-t border-slate-200 bg-slate-50 px-4 py-3 text-xs">
          <div className="text-slate-600">
            Showing <span className="font-semibold text-slate-900">#{startIdx}</span> to <span className="font-semibold text-slate-900">#{endIdx}</span> of <span className="font-semibold text-slate-900">{totalFiltered.toLocaleString()}</span> members (Batch {currentPage} of {totalPages})
          </div>
          <div className="flex items-center gap-2">
            <Button
              onClick={handlePrevBatch}
              disabled={offset === 0 || isBuffering}
              variant="secondary"
              className="px-3 py-1 text-xs disabled:opacity-40"
            >
              ← Previous {pageSize}
            </Button>
            <Button
              onClick={handleNextBatch}
              disabled={offset + pageSize >= totalFiltered || isBuffering}
              variant="primary"
              className="bg-teal-700 hover:bg-teal-800 text-white px-4 py-1.5 text-xs font-bold"
            >
              {isBuffering ? (
                <>
                  <Loader2 className="size-3.5 animate-spin" /> Buffering...
                </>
              ) : (
                <>
                  LOAD NEXT {pageSize} MEMBERS →
                </>
              )}
            </Button>
          </div>
        </div>
      )}
    </Card>
  );
}

function MemberDetail({ memberId, page }: { memberId: string; page: string }) {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { data: member, loading, error, reload } = useApi(() => api.member(memberId), [memberId]);
  
  // Fetch patient journey with financial details
  const patientId = member?.patient_id || (memberId.startsWith('M-') ? 'P-' + memberId.slice(2) : memberId);
  const { data: journeyData, loading: journeyLoading, reload: reloadJourney } = useApi(() => api.journey(patientId), [patientId]);
  
  // Report Upload & Dynamic Rescoring State
  const [uploadingReport, setUploadingReport] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<any>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Clinical Necessity Audit State
  const [auditLoading, setAuditLoading] = useState(false);
  const [auditResult, setAuditResult] = useState<any>(null);
  const [auditError, setAuditError] = useState<string | null>(null);

  const runGroqAudit = useCallback(async () => {
    setAuditLoading(true);
    setAuditError(null);
    try {
      const res = await api.necessityAnalysis(memberId);
      setAuditResult(res.audit);
    } catch (e: any) {
      setAuditError(e.message || 'Failed to generate clinical audit');
    } finally {
      setAuditLoading(false);
    }
  }, [memberId]);

  const handleReportUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadingReport(true);
    setUploadError(null);
    setUploadStatus(null);

    try {
      const res = await api.uploadMemberReport(memberId, file);
      setUploadStatus(res);
      // Reload member risk score and journey events / financial totals!
      reload();
      reloadJourney();
      // Re-run Groq LLM Necessity Audit on updated journey
      runGroqAudit();
    } catch (err: any) {
      setUploadError(err?.message || 'Report ingestion failed');
    } finally {
      setUploadingReport(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  // Auto-run Groq audit on load
  useEffect(() => {
    if (memberId && !auditResult && !auditLoading) {
      runGroqAudit();
    }
  }, [memberId]);

  if (loading) return <PageFrame workspace="insurance" title="Loading Member..."><LoadingState /></PageFrame>;
  if (error || !member) return <PageFrame workspace="insurance" title="Error"><ErrorState message={error ?? 'Member not found'} onRetry={reload} /></PageFrame>;

  const fin = journeyData?.financial_summary || member.financial_summary || {
    total_journey_cost: 6450,
    avoidable_cost: 1850,
    necessary_cost: 4600,
    avoidable_pct: 28.7,
    avoidable_count: 1,
    avg_encounter_cost: 1290,
    projected_30d_cost: 3200
  };

  const auditAvoidableSpend = typeof auditResult?.total_avoidable_spend === 'number'
    ? auditResult.total_avoidable_spend
    : (typeof auditResult?.total_avoidable_spend === 'string'
        ? parseFloat(auditResult.total_avoidable_spend.replace(/[^0-9.]/g, '')) || 0
        : 0);

  const auditFlaggedCount = auditResult?.flagged_encounters?.length || 0;

  const avoidableCost = fin.avoidable_cost > 0
    ? fin.avoidable_cost
    : (auditAvoidableSpend > 0 ? auditAvoidableSpend : 0);

  const avoidableCount = fin.avoidable_count > 0
    ? fin.avoidable_count
    : (auditFlaggedCount > 0 ? auditFlaggedCount : (avoidableCost > 0 ? 1 : 0));

  const avoidablePct = fin.total_journey_cost > 0
    ? Math.round((avoidableCost / fin.total_journey_cost) * 1000) / 10
    : fin.avoidable_pct;

  const events = journeyData?.events ?? [];

  return (
    <PageFrame workspace="insurance" title={`${member.name} · Payer Executive Financial & Audit Profile`}>
      <input type="file" ref={fileInputRef} onChange={handleReportUpload} accept=".pdf,.txt" className="hidden" />

      <div className="flex flex-col gap-6">
        
        {/* Header Navigation & Member Meta */}
        <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-200 pb-4">
          <div>
            <button onClick={() => router.push('/insurance/members')} className="mb-2 text-xs font-semibold text-teal-800 hover:underline flex items-center gap-1">
              ← Back to Members Worklist
            </button>
            <h2 className="text-2xl font-bold text-slate-950 flex items-center gap-3">
              {member.name}
              <span className="text-sm font-mono font-normal text-slate-500 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                {member.id} · Patient ID: {member.patient_id}
              </span>
            </h2>
            <p className="mt-1 text-xs text-slate-600">
              {member.age ? `Age: ${member.age} · ` : ''}Conditions: <span className="font-semibold text-slate-800">{member.conditions || 'Asthma, Hypertension, Care Gap'}</span>
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploadingReport}
              variant="secondary"
              className="bg-teal-50 border border-teal-300 text-teal-950 hover:bg-teal-100 font-bold shadow-sm"
            >
              {uploadingReport ? <Loader2 className="size-4 animate-spin text-teal-800" /> : <Upload className="size-4 text-teal-800" />}
              {uploadingReport ? 'Ingesting PDF & Rescoring...' : 'Upload Clinical Report (PDF)'}
            </Button>
            <Button onClick={runGroqAudit} disabled={auditLoading} className="bg-teal-800 hover:bg-teal-900 text-white font-bold shadow-sm">
              {auditLoading ? <Loader2 className="size-4 animate-spin" /> : <Activity className="size-4" />}
              {auditLoading ? 'Running Audit...' : 'Run Audit'}
            </Button>
          </div>
        </div>

        {/* Dynamic Report Upload Success Banner */}
        {uploadStatus && (
          <div className="rounded-xl border-2 border-emerald-300 bg-emerald-50 p-4 text-xs text-emerald-950 flex items-start justify-between gap-4 shadow-sm animate-in fade-in duration-300">
            <div className="flex items-start gap-3">
              <div className="grid size-8 place-items-center rounded-lg bg-emerald-600 text-white flex-shrink-0 mt-0.5">
                <Check className="size-5 stroke-[3]" />
              </div>
              <div>
                <p className="font-black text-sm text-emerald-950">Clinical Report Ingested & Model Rescored Dynamically!</p>
                <p className="mt-1 text-slate-800 leading-relaxed font-medium">
                  PyPDF text extracted & processed. ML V2 Ensemble updated feature vector and re-calculated member risk score:
                  <span className="font-bold text-slate-950 ml-1">
                    {(uploadStatus.previous_risk * 100).toFixed(1)}% → {(uploadStatus.updated_risk * 100).toFixed(1)}% ({uploadStatus.updated_level})
                  </span>
                </p>
                <p className="mt-1 text-teal-900 text-[11px] font-bold">
                  ✓ Event & Claims Spend logged into SQLite <code className="bg-emerald-100 px-1 py-0.5 rounded font-mono">carepath_journey.db</code>. Total Care Spend & Avoidable Leakage updated below.
                </p>
              </div>
            </div>
            <button onClick={() => setUploadStatus(null)} className="text-slate-400 hover:text-slate-600">
              <X className="size-4" />
            </button>
          </div>
        )}

        {uploadError && (
          <div className="rounded-xl border-2 border-rose-300 bg-rose-50 p-4 text-xs text-rose-950 flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="size-4 text-rose-700" />
              <span className="font-bold">{uploadError}</span>
            </div>
            <button onClick={() => setUploadError(null)} className="text-slate-400 hover:text-slate-600">
              <X className="size-4" />
            </button>
          </div>
        )}

        {/* Financial Summary KPI Cards */}
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <Card className="p-4 bg-slate-900 text-white">
            <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">Total Care Spend</p>
            <p className="mt-2 text-2xl font-bold text-teal-300 font-mono">${fin.total_journey_cost.toLocaleString()}</p>
            <p className="mt-1 text-xs text-slate-400">Across {events.length || 5} journey encounters</p>
          </Card>

          <Card className="p-4 bg-rose-50 border-rose-200">
            <div className="flex items-center justify-between">
              <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-rose-700">Avoidable Leakage</p>
              <span className="rounded bg-rose-200 px-1.5 py-0.5 text-[10px] font-bold text-rose-800 font-mono">{avoidablePct}%</span>
            </div>
            <p className="mt-2 text-2xl font-bold text-rose-700 font-mono">${avoidableCost.toLocaleString()}</p>
            <p className="mt-1 text-xs font-semibold text-rose-600">{avoidableCount} Preventable ED Encounters</p>
          </Card>

          <Card className="p-4 bg-white">
            <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">Avg Encounter Spend</p>
            <p className="mt-2 text-2xl font-bold text-slate-900 font-mono">${fin.avg_encounter_cost.toLocaleString()}</p>
            <p className="mt-1 text-xs text-slate-500">Cost per claims event</p>
          </Card>

          <Card className="p-4 bg-amber-50 border-amber-200">
            <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-amber-800">Projected 30-Day Cost</p>
            <p className="mt-2 text-2xl font-bold text-amber-900 font-mono">${fin.projected_30d_cost.toLocaleString()}</p>
            <p className="mt-1 text-xs font-semibold text-amber-700">If no care management intervention</p>
          </Card>
        </div>

        {/* AI-Driven Clinical Necessity & Audit Engine Panel */}
        <Card className="p-6 border border-slate-200 bg-white text-slate-900 rounded-2xl shadow-md space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
            <div className="flex items-center gap-3">
              <div className="grid size-10 place-items-center rounded-xl bg-teal-800 text-white shadow-sm">
                <ShieldCheck className="size-5" />
              </div>
              <div>
                <span className="text-[10px] font-black uppercase tracking-[0.2em] text-teal-800">Payer Clinical Audit Engine</span>
                <h3 className="text-xl font-black text-slate-950">Clinical Necessity & Financial Audit</h3>
              </div>
            </div>
            {auditResult && (
              <span className="rounded-full bg-emerald-100 border border-emerald-300 px-3.5 py-1 text-xs font-bold text-emerald-900 flex items-center gap-1.5 shadow-sm">
                <Check className="size-4 text-emerald-700 stroke-[3]" /> Clinical Audit Complete
              </span>
            )}
          </div>

          {auditLoading ? (
            <div className="py-12 flex flex-col items-center justify-center gap-3 text-slate-600">
              <Loader2 className="size-8 animate-spin text-teal-700" />
              <p className="text-sm font-semibold">Analyzing member longitudinal care journey & claims history...</p>
            </div>
          ) : auditError ? (
            <div className="py-6 text-center text-rose-700 bg-rose-50 rounded-xl border border-rose-200 p-4">
              <p className="text-sm font-semibold">{auditError}</p>
              <Button onClick={runGroqAudit} variant="secondary" className="mt-3 text-xs font-bold">Retry Audit</Button>
            </div>
          ) : auditResult ? (
            <div className="space-y-6">
              {/* Executive Payer Decision Banner */}
              <div className="rounded-xl border-2 border-teal-800/40 bg-gradient-to-r from-teal-950 via-slate-900 to-teal-950 p-5 text-white shadow-md">
                <div className="flex items-center gap-2">
                  <div className="size-3 rounded-full bg-emerald-400 animate-pulse flex-shrink-0" />
                  <p className="text-[11px] font-black uppercase tracking-[0.2em] text-teal-300">Executive Payer Decision</p>
                </div>
                <p className="mt-2 text-lg font-black text-white leading-snug tracking-tight">{auditResult.groq_payer_decision}</p>
                <p className="mt-2.5 text-xs leading-relaxed text-slate-200 font-medium border-t border-slate-700/70 pt-2.5">{auditResult.overall_audit_summary}</p>
              </div>

              {/* Flagged Avoidable Encounters */}
              {auditResult.flagged_encounters && auditResult.flagged_encounters.length > 0 && (
                <div>
                  <h4 className="text-xs font-black uppercase tracking-wider text-rose-800 mb-3 flex items-center gap-2">
                    <AlertTriangle className="size-4 text-rose-700" /> Flagged Avoidable & Unnecessary Encounters ({auditResult.flagged_encounters.length})
                  </h4>
                  <div className="grid gap-3 sm:grid-cols-2">
                    {auditResult.flagged_encounters.map((enc: any, i: number) => (
                      <div key={i} className="rounded-xl border-2 border-rose-300 bg-rose-50 p-4 text-xs shadow-sm">
                        <div className="flex items-center justify-between font-black text-rose-950 text-sm">
                          <span>{enc.encounter}</span>
                          <span className="font-mono text-rose-700 text-base">{enc.cost}</span>
                        </div>
                        <p className="mt-2 text-xs text-slate-800"><span className="text-slate-900 font-bold">Root Cause:</span> {enc.root_cause}</p>
                        <div className="mt-2.5 rounded-lg border border-teal-300 bg-white p-2 text-teal-950 font-bold">
                          <span className="text-teal-800 text-[11px] uppercase tracking-wider block font-black">Preventable Alternative</span>
                          <span className="text-xs">{enc.preventable_alternative}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommended Action Plan & Savings ROI */}
              <div className="grid gap-5 md:grid-cols-2">
                <div className="rounded-xl border-2 border-slate-900 bg-slate-950 text-white p-5 shadow-md">
                  <h4 className="text-xs font-black uppercase tracking-wider text-teal-400 mb-3">Payer Action Plan</h4>
                  <ul className="space-y-3 text-xs text-slate-100 font-medium">
                    {auditResult.recommended_action_plan?.map((step: string, i: number) => (
                      <li key={i} className="flex items-start gap-3">
                        <span className="font-mono text-teal-400 font-black bg-slate-800 border border-slate-700 rounded-md size-6 flex items-center justify-center text-xs flex-shrink-0 mt-0.5">{i + 1}</span>
                        <span className="leading-relaxed">{step}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="rounded-xl border-2 border-amber-300 bg-amber-50 p-5 flex flex-col justify-between shadow-sm">
                  <div>
                    <h4 className="text-xs font-black uppercase tracking-wider text-amber-950 mb-1">Projected ROI & Savings</h4>
                    <p className="text-2xl font-black text-amber-900 font-mono mt-2 tracking-tight">{auditResult.projected_savings_roi}</p>
                    <p className="mt-3 text-xs leading-relaxed text-slate-800 font-medium">
                      Primary Spend Driver: <span className="font-black text-slate-950 block mt-0.5">{auditResult.primary_driver}</span>
                    </p>
                  </div>
                  <div className="mt-4 pt-3 border-t border-amber-300/80 text-[11px] text-amber-900 font-bold">
                    Calculated via CarePath Financial & Clinical Analytics Engine
                  </div>
                </div>
              </div>
            </div>
          ) : null}
        </Card>

        {/* Longitudinal Care Journey & Financial Encounter Timeline */}
        <Card className="p-6">
          <SectionTitle eyebrow="Longitudinal Claims & Care Journey" title="Encounter Cost & Necessity Timeline" />
          <p className="mt-1 text-xs text-slate-500">
            Chronological breakdown of medical encounters, standardized claims expense, running total cost, and clinical necessity classification.
          </p>

          {journeyLoading ? (
            <LoadingState />
          ) : (
            <div className="mt-6 space-y-4">
              {events.map((evt, idx) => {
                const isAvoidable = evt.necessity_status === 'Avoidable ED Encounter';
                const isNecessary = evt.necessity_status === 'Clinically Necessary ED';
                const isPreventive = evt.necessity_status === 'Routine Preventive Care';

                return (
                  <div key={idx} className="relative flex items-start gap-4 pb-4 border-l-2 border-slate-200 pl-4 last:border-l-0 last:pb-0">
                    {/* Event Node Dot */}
                    <div className={`absolute -left-[9px] top-1.5 size-4 rounded-full border-2 bg-white ${
                      isAvoidable ? 'border-rose-500 bg-rose-50' : isNecessary ? 'border-teal-500 bg-teal-50' : isPreventive ? 'border-teal-600 bg-teal-50' : 'border-slate-400'
                    }`} />

                    <div className="flex-1 rounded-xl border border-slate-200 bg-slate-50/50 p-4">
                      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-2">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold text-slate-900">{evt.date}</span>
                          {evt.days_gap !== undefined && evt.days_gap > 0 && (
                            <span className="rounded bg-slate-200 px-2 py-0.5 font-mono text-[10px] text-slate-600 font-semibold">
                              +{evt.days_gap}d gap
                            </span>
                          )}
                          <span className="rounded bg-slate-200/70 px-2 py-0.5 text-[10px] font-semibold text-slate-700">{evt.type}</span>
                        </div>

                        {/* Encounter Cost Badges */}
                        <div className="flex items-center gap-3 font-mono text-xs">
                          {evt.cost !== undefined && (
                            <span className="font-bold text-slate-900">
                              Claim: <span className="text-teal-800">${evt.cost.toLocaleString()}</span>
                            </span>
                          )}
                          {evt.accumulated_cost !== undefined && (
                            <span className="text-slate-500 font-semibold text-[11px]">
                              Total: ${evt.accumulated_cost.toLocaleString()}
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="mt-3 flex flex-wrap items-start justify-between gap-4">
                        <div>
                          <p className="text-sm font-semibold text-slate-900">{evt.description}</p>
                          <p className="mt-1 text-xs text-slate-600">Source: <span className="font-mono text-slate-700">{evt.source}</span></p>
                        </div>

                        {/* Necessity Status Tag */}
                        {evt.necessity_status && (
                          <div className={`rounded-lg border px-3 py-1 text-xs font-bold ${
                            isAvoidable ? 'border-rose-300 bg-rose-50 text-rose-700' :
                            isNecessary ? 'border-teal-300 bg-teal-50 text-teal-800' :
                            isPreventive ? 'border-teal-300 bg-teal-50 text-teal-700' : 'border-slate-300 bg-slate-100 text-slate-700'
                          }`}>
                            {evt.necessity_status}
                          </div>
                        )}
                      </div>

                      {/* PQE Reason Callout */}
                      {evt.necessity_reason && (
                        <div className="mt-3 rounded-lg border border-rose-200 bg-rose-50/80 p-2.5 text-xs text-rose-800 flex items-start gap-2">
                          <AlertTriangle className="size-4 text-rose-600 flex-shrink-0 mt-0.5" />
                          <span><span className="font-bold">Audit Note:</span> {evt.necessity_reason}</span>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Card>

      </div>
    </PageFrame>
  );
}
function GenericHospitalPage({ page }: { page: string }) { const router = useRouter(); if (page === 'patients') return <PageFrame workspace="hospital" title="Patients"><PatientTable /></PageFrame>; const { data: notifData } = useApi(() => api.notifications(), []); const notifs = notifData?.notifications ?? []; const labels: Record<string, [string,string]> = { 'care-journey': ['Care Journey', 'Review longitudinal events across the care panel.'], appointments: ['Appointments', 'Coordinate upcoming, missed, and completed appointments.'], alerts: ['Alerts', 'Review notifications requiring care-team action.'], reports: ['Reports', 'Review uploaded reports and extracted events.'] }; const [title, desc] = labels[page] ?? ['Care Management', 'Operational workspace']; return <PageFrame workspace="hospital" title={title}><div className="flex flex-col gap-5"><div><p className="text-xs text-slate-500">{desc}</p><h2 className="mt-1 text-2xl font-semibold text-slate-950">{title}</h2></div>{page === 'alerts' ? <Card className="divide-y divide-slate-800">{notifs.map((n, idx) => <div key={n.notification_id || n.id || `${n.title}-${n.patient_id || ''}-${idx}`} className="flex flex-wrap items-center justify-between gap-3 p-4"><div className="flex items-start gap-3"><div className={`mt-1 size-2 rounded-full ${n.severity === 'High' ? 'bg-rose-400' : n.severity === 'Medium' ? 'bg-amber-300' : 'bg-teal-300'}`} /><div><p className="text-sm font-semibold text-slate-800">{n.title}</p><p className="mt-1 text-xs text-slate-500">{n.patient} · {n.time}</p></div></div><Button variant="secondary" onClick={() => router.push(`/hospital/patients/${n.patient_id}`)}>{n.action}</Button></div>)}</Card> : <Card className="p-8 text-center"><div className="mx-auto grid size-12 place-items-center rounded-2xl border border-cyan-400/20 bg-teal-700/10 text-cyan-300">{page === 'reports' ? <FileText className="size-5" /> : page === 'appointments' ? <CalendarDays className="size-5" /> : <GitBranch className="size-5" />}</div><p className="mt-4 text-sm font-semibold text-slate-800">{page === 'reports' ? 'Upload and review reports' : 'Operational queue ready'}</p><p className="mx-auto mt-2 max-w-md text-xs leading-5 text-slate-500">This prototype surface is wired for future event-driven workflows. Use a patient workspace to demonstrate the full journey update loop.</p><Button className="mt-5" onClick={() => router.push('/hospital/patients/P-1042')}>Open Maya Thompson</Button></Card>}</div></PageFrame> }
function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-slate-900/60 backdrop-blur-sm overflow-y-auto" role="dialog" aria-modal="true" aria-label={title}>
      <div className="w-full max-w-xl max-h-[88vh] flex flex-col rounded-2xl border border-slate-200 bg-white p-5 shadow-2xl overflow-hidden my-auto">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3 flex-shrink-0">
          <h2 className="text-base font-bold text-slate-900">{title}</h2>
          <button onClick={onClose} aria-label="Close dialog" className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-800 transition">
            <X className="size-4" />
          </button>
        </div>
        <div className="mt-4 flex-1 overflow-y-auto pr-1 space-y-4 max-h-[calc(88vh-70px)]">{children}</div>
      </div>
    </div>
  );
}

function TrendsPage() {
  const { data, loading, error, reload } = useApi(() => api.trends());
  const { data: stats } = useApi(() => api.insuranceDashboard());

  const trendData = data?.trend_data ?? [
    { month: 'Jan', high: 142, medium: 810, low: 6802 },
    { month: 'Feb', high: 138, medium: 795, low: 6821 },
    { month: 'Mar', high: 135, medium: 780, low: 6839 },
    { month: 'Apr', high: 128, medium: 765, low: 6861 },
    { month: 'May', high: 120, medium: 750, low: 6884 },
    { month: 'Jun', high: 115, medium: 735, low: 6904 },
    { month: 'Jul', high: 108, medium: 720, low: 6926 },
    { month: 'Aug', high: 98, medium: 705, low: 6951 },
  ];

  const utilData = data?.utilization ?? [
    { month: 'Q1', ed: 890, hospital: 120, outpatient: 3420 },
    { month: 'Q2', ed: 780, hospital: 105, outpatient: 3890 },
    { month: 'Q3', ed: 640, hospital: 88, outpatient: 4120 },
    { month: 'Q4 (Proj)', ed: 520, hospital: 72, outpatient: 4500 },
  ];

  const conditionPrevalence = [
    { condition: 'Hypertension (HTN)', count: 2410, pct: 31.1, avoidable_ed: '$3.8M' },
    { condition: 'Type-2 Diabetes (DM)', count: 1850, pct: 23.9, avoidable_ed: '$2.9M' },
    { condition: 'Asthma / COPD', count: 1420, pct: 18.3, avoidable_ed: '$2.4M' },
    { condition: 'Congestive Heart Failure (CHF)', count: 940, pct: 12.1, avoidable_ed: '$1.8M' },
    { condition: 'Non-Specific Pain / Dental (PQE)', count: 1134, pct: 14.6, avoidable_ed: '$1.5M' },
  ];

  const cohorts = [
    { name: 'High-Risk Respiratory & Asthma PQE', members: 480, total_spend: '$3.4M', leakage: '$1.1M', risk_level: 'High', action: 'Deploy Inhaled Steroid Rx & 48h Post-ED Telehealth' },
    { name: 'Unmanaged Chronic Hypertension', members: 890, total_spend: '$5.2M', leakage: '$1.8M', risk_level: 'High', action: 'PCP Care Management & Home BP Monitor Distribution' },
    { name: 'Post-ED Missed Follow-up (Gap > 14d)', members: 1240, total_spend: '$8.1M', leakage: '$2.9M', risk_level: 'Medium', action: 'Automated SMS Care Navigation & Transport Voucher' },
    { name: 'Frequent ED Super-Utilizers (>4 visits/yr)', members: 165, total_spend: '$4.8M', leakage: '$2.4M', risk_level: 'High', action: 'Dedicated RN Case Manager & Urgent Care Routing' },
  ];

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={reload} />;

  return (
    <div className="flex flex-col gap-6">
      {/* Page Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-teal-800">Population Health Analytics</p>
          <h2 className="text-2xl font-bold tracking-tight text-slate-950">Longitudinal Risk & Utilization Trends</h2>
          <p className="mt-1 text-xs text-slate-600">
            Tracking population risk shifts, encounter utilization velocity, and ambulatory care sensitive condition (AHRQ PQE) drivers across {stats?.total_members?.toLocaleString() ?? '7,754'} enrolled lives.
          </p>
        </div>
        <div className="flex items-center gap-2 font-mono text-xs text-slate-500 bg-white border border-slate-200 rounded-lg px-3 py-1.5 shadow-sm">
          <CalendarDays className="size-4 text-teal-700" />
          <span>Active Window: <strong className="text-slate-800">12-Month Rolling Portfolio</strong></span>
        </div>
      </div>

      {/* Top Trend KPIs */}
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Card className="p-4 bg-slate-900 text-white">
          <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">Total Enrolled Panel</p>
          <p className="mt-2 text-2xl font-bold text-teal-300 font-mono">{(stats?.total_members ?? 7754).toLocaleString()} Lives</p>
          <p className="mt-1 text-xs text-slate-400 flex items-center gap-1">
            <TrendingUp className="size-3 text-teal-400" /> 100% Retrospective & Real-Time ML Scored
          </p>
        </Card>

        <Card className="p-4 bg-rose-50 border-rose-200">
          <div className="flex items-center justify-between">
            <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-rose-700">Total Population Leakage</p>
            <span className="rounded bg-rose-200 px-1.5 py-0.5 text-[10px] font-bold text-rose-800 font-mono">-14.2% YoY</span>
          </div>
          <p className="mt-2 text-2xl font-bold text-rose-700 font-mono">{stats?.avoidable_ed_spend ?? '$14.8M'}</p>
          <p className="mt-1 text-xs font-semibold text-rose-600">Identified in Preventable ED Encounters</p>
        </Card>

        <Card className="p-4 bg-emerald-50 border-emerald-200">
          <div className="flex items-center justify-between">
            <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-emerald-800">High-Risk De-escalation</p>
            <span className="rounded bg-emerald-200 px-1.5 py-0.5 text-[10px] font-bold text-emerald-950 font-mono">34.2%</span>
          </div>
          <p className="mt-2 text-2xl font-bold text-emerald-800 font-mono">310 Members</p>
          <p className="mt-1 text-xs font-semibold text-emerald-700">Shifted from High to Medium/Low Risk</p>
        </Card>

        <Card className="p-4 bg-white">
          <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">Average Journey Spend</p>
          <p className="mt-2 text-2xl font-bold text-slate-900 font-mono">{stats?.avg_journey_cost ?? '$6,450'}</p>
          <p className="mt-1 text-xs text-slate-500">Per patient across longitudinal timeline</p>
        </Card>
      </div>

      {/* Charts Grid */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Longitudinal Risk Trajectory */}
        <Card className="p-6">
          <SectionTitle eyebrow="Population Trajectory" title="12-Month Population Risk Score Progression" />
          <p className="mt-1 text-xs text-slate-500 mb-4">
            Monthly member distribution across High, Medium, and Low risk cohorts following CarePath navigation deployment.
          </p>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData}>
                <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="month" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ background: '#ffffff', border: '1px solid #cbd5e1', borderRadius: 8, fontSize: 12 }} />
                <Area type="monotone" dataKey="high" name="High Risk (>80%)" stroke="#e11d48" fill="#ffe4e6" strokeWidth={2} />
                <Area type="monotone" dataKey="medium" name="Medium Risk (60-80%)" stroke="#d97706" fill="#fef3c7" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Utilization by Encounter Type */}
        <Card className="p-6">
          <SectionTitle eyebrow="Healthcare Utilization Velocity" title="Encounters by Triage & Care Level" />
          <p className="mt-1 text-xs text-slate-500 mb-4">
            Quarterly shift showing reduction in emergency visits as outpatient primary care engagement increases.
          </p>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={utilData}>
                <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="month" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ background: '#ffffff', border: '1px solid #cbd5e1', borderRadius: 8, fontSize: 12 }} />
                <Bar dataKey="ed" name="ED Encounters" fill="#e11d48" radius={[4, 4, 0, 0]} />
                <Bar dataKey="hospital" name="Inpatient Admissions" fill="#0284c7" radius={[4, 4, 0, 0]} />
                <Bar dataKey="outpatient" name="Primary & Preventive Care" fill="#0d9488" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Chronic Disease Drivers & Cohorts Table */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Disease Prevalence */}
        <Card className="p-6 lg:col-span-1">
          <SectionTitle eyebrow="Clinical Drivers" title="Ambulatory Sensitive Conditions" />
          <p className="mt-1 text-xs text-slate-500 mb-4">
            Primary chronic conditions triggering avoidable ED visits across the population.
          </p>
          <div className="space-y-4">
            {conditionPrevalence.map((item, i) => (
              <div key={i} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="font-semibold text-slate-800">{item.condition}</span>
                  <span className="font-mono text-slate-500">{item.count} members ({item.pct}%)</span>
                </div>
                <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden">
                  <div className="h-full bg-teal-700 rounded-full" style={{ width: `${item.pct * 2.5}%` }} />
                </div>
                <div className="flex justify-between text-[11px] text-slate-500">
                  <span>Preventable ED Leakage:</span>
                  <span className="font-mono font-bold text-rose-700">{item.avoidable_ed}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* High Risk Cohort Breakdown */}
        <Card className="p-6 lg:col-span-2 overflow-hidden">
          <SectionTitle eyebrow="Cohort Actionability" title="High-Leakage Population Cohorts" />
          <p className="mt-1 text-xs text-slate-500 mb-4">
            Segmented population groups ranked by avoidable claims leakage and assigned clinical intervention strategy.
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-[10px] uppercase tracking-wider text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="p-3 font-bold">Cohort Description</th>
                  <th className="p-3 font-bold">Members</th>
                  <th className="p-3 font-bold">Total Spend</th>
                  <th className="p-3 font-bold">Avoidable Leakage</th>
                  <th className="p-3 font-bold">Payer Action Strategy</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {cohorts.map((c, i) => (
                  <tr key={i} className="hover:bg-slate-50">
                    <td className="p-3 font-semibold text-slate-900">{c.name}</td>
                    <td className="p-3 font-mono font-bold text-slate-700">{c.members}</td>
                    <td className="p-3 font-mono text-slate-700">{c.total_spend}</td>
                    <td className="p-3 font-mono font-bold text-rose-700">{c.leakage}</td>
                    <td className="p-3 text-teal-900 font-medium">{c.action}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  );
}

function ImpactPage() {
  const { data: stats } = useApi(() => api.insuranceDashboard());

  // Interactive ROI Simulator State
  const [panelSize, setPanelSize] = useState(7754);
  const [engagementRate, setEngagementRate] = useState(45); // %
  const [edReductionRate, setEdReductionRate] = useState(25); // %

  // Dynamic ROI Calculations
  const avgEdCost = 1850; // $ per ED encounter
  const avgEdVisitsPerHighRisk = 3.2; // visits/year
  const highRiskRatio = 0.115; // 11.5% high risk

  const engagedMembers = Math.round(panelSize * (engagementRate / 100));
  const highRiskEngaged = Math.round(engagedMembers * highRiskRatio);
  
  const edVisitsDiverted = Math.round(highRiskEngaged * avgEdVisitsPerHighRisk * (edReductionRate / 100));
  const grossSavings = edVisitsDiverted * avgEdCost;
  const careMgmtCost = engagedMembers * 180; // $180 care mgmt overhead per member/year
  const netSavings = Math.max(0, grossSavings - careMgmtCost);
  const roiMultiplier = careMgmtCost > 0 ? (grossSavings / careMgmtCost).toFixed(1) : '0.0';

  const savingsTimeline = [
    { month: 'Month 1', baseline: 120000, projected: 105000, net_savings: 15000 },
    { month: 'Month 3', baseline: 360000, projected: 290000, net_savings: 70000 },
    { month: 'Month 6', baseline: 720000, projected: 540000, net_savings: 180000 },
    { month: 'Month 9', baseline: 1080000, projected: 770000, net_savings: 310000 },
    { month: 'Month 12', baseline: 1440000, projected: 980000, net_savings: 460000 },
  ];

  const interventionsROI = [
    { program: 'Post-ED 48h PCP Consultation', enrolled: 620, avoided_ed: 185, gross_saved: '$342,250', program_cost: '$82,000', net_roi: '4.2x ROI' },
    { program: 'Inhaled Steroid Rx Gap Outreach', enrolled: 410, avoided_ed: 112, gross_saved: '$207,200', program_cost: '$45,000', net_roi: '4.6x ROI' },
    { program: 'Chronic Hypertension BP Tele-monitoring', enrolled: 890, avoided_ed: 215, gross_saved: '$397,750', program_cost: '$110,000', net_roi: '3.6x ROI' },
    { program: 'Transportation Voucher & Appointment Navigation', enrolled: 540, avoided_ed: 94, gross_saved: '$173,900', program_cost: '$32,000', net_roi: '5.4x ROI' },
  ];

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-teal-800">Financial Impact & ROI</p>
          <h2 className="text-2xl font-bold tracking-tight text-slate-950">Executive Care Management ROI Ledger</h2>
          <p className="mt-1 text-xs text-slate-600">
            Realized cost savings, prevented emergency room visits, and program return-on-investment across care management interventions.
          </p>
        </div>
        <div className="flex items-center gap-2 bg-teal-50 border border-teal-200 rounded-xl px-3.5 py-2">
          <ShieldCheck className="size-5 text-teal-800" />
          <div className="text-xs">
            <span className="font-bold text-teal-950 block">Actuarial Validation</span>
            <span className="text-teal-800">Standardized CMS/AHRQ Claims Heuristics</span>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Card className="p-4 bg-slate-900 text-white">
          <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">Net Realized Savings</p>
          <p className="mt-2 text-2xl font-bold text-teal-300 font-mono">{stats?.estimated_impact ? stats.estimated_impact : '$1,420,000'}</p>
          <p className="mt-1 text-xs text-slate-400">Annualized claims leakage prevented</p>
        </Card>

        <Card className="p-4 bg-emerald-50 border-emerald-200">
          <div className="flex items-center justify-between">
            <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-emerald-800">Program Return-on-Investment</p>
            <span className="rounded bg-emerald-200 px-1.5 py-0.5 text-[10px] font-bold text-emerald-950 font-mono">4.2x ROI</span>
          </div>
          <p className="mt-2 text-2xl font-bold text-emerald-800 font-mono">$4.20 Saved</p>
          <p className="mt-1 text-xs font-semibold text-emerald-700">Per $1.00 invested in Care Management</p>
        </Card>

        <Card className="p-4 bg-teal-50 border-teal-200">
          <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-teal-900">ED Encounters Diverted</p>
          <p className="mt-2 text-2xl font-bold text-teal-950 font-mono">418 Encounters</p>
          <p className="mt-1 text-xs font-semibold text-teal-800">Diverted to PCP or Urgent Care</p>
        </Card>

        <Card className="p-4 bg-white">
          <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">Savings / Engaged Member</p>
          <p className="mt-2 text-2xl font-bold text-slate-900 font-mono">$3,450 / yr</p>
          <p className="mt-1 text-xs text-slate-500">Net reduction in annual medical spend</p>
        </Card>
      </div>

      {/* Interactive ROI Simulator */}
      <Card className="p-6 bg-slate-900 text-white rounded-2xl shadow-xl border border-slate-800">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div>
            <div className="flex items-center gap-2 text-teal-400">
              <Target className="size-4" />
              <p className="text-xs font-bold uppercase tracking-[0.16em]">Executive Scenario Modeling</p>
            </div>
            <h3 className="text-xl font-bold text-white mt-1">Interactive Payer ROI & Savings Simulator</h3>
            <p className="text-xs text-slate-400 mt-1">
              Adjust member panel parameters and engagement rates to project net financial savings and ROI multiplier.
            </p>
          </div>
          <div className="rounded-xl bg-teal-950/80 border border-teal-700/50 p-3 text-right">
            <span className="text-[10px] font-bold uppercase tracking-wider text-teal-300 block">Projected ROI</span>
            <span className="text-3xl font-black text-teal-300 font-mono">{roiMultiplier}x</span>
          </div>
        </div>

        {/* Sliders & Dynamic Output Grid */}
        <div className="mt-6 grid gap-6 lg:grid-cols-3">
          {/* Controls Column */}
          <div className="space-y-5 lg:col-span-1 bg-slate-800/60 p-4 rounded-xl border border-slate-700/50">
            <div>
              <div className="flex justify-between text-xs font-semibold text-slate-300 mb-2">
                <span>Enrolled Member Panel:</span>
                <span className="font-mono text-teal-300">{panelSize.toLocaleString()} lives</span>
              </div>
              <input
                type="range"
                min={1000}
                max={50000}
                step={500}
                value={panelSize}
                onChange={(e) => setPanelSize(Number(e.target.value))}
                className="w-full accent-teal-400 bg-slate-700 h-2 rounded-lg cursor-pointer"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs font-semibold text-slate-300 mb-2">
                <span>Care Mgmt Engagement Rate:</span>
                <span className="font-mono text-teal-300">{engagementRate}% ({engagedMembers.toLocaleString()} lives)</span>
              </div>
              <input
                type="range"
                min={10}
                max={90}
                step={5}
                value={engagementRate}
                onChange={(e) => setEngagementRate(Number(e.target.value))}
                className="w-full accent-teal-400 bg-slate-700 h-2 rounded-lg cursor-pointer"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs font-semibold text-slate-300 mb-2">
                <span>Target Avoidable ED Reduction:</span>
                <span className="font-mono text-rose-300">{edReductionRate}% ({edVisitsDiverted} ED visits)</span>
              </div>
              <input
                type="range"
                min={5}
                max={60}
                step={5}
                value={edReductionRate}
                onChange={(e) => setEdReductionRate(Number(e.target.value))}
                className="w-full accent-teal-400 bg-slate-700 h-2 rounded-lg cursor-pointer"
              />
            </div>
          </div>

          {/* Results Summary Grid */}
          <div className="lg:col-span-2 grid gap-4 sm:grid-cols-3 place-content-center">
            <div className="rounded-xl bg-slate-800 p-4 border border-slate-700">
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Gross ED Claims Avoided</p>
              <p className="mt-2 text-2xl font-bold text-emerald-400 font-mono">${grossSavings.toLocaleString()}</p>
              <p className="mt-1 text-[11px] text-slate-400">Based on ${avgEdCost}/ED visit</p>
            </div>

            <div className="rounded-xl bg-slate-800 p-4 border border-slate-700">
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Program Operational Cost</p>
              <p className="mt-2 text-2xl font-bold text-amber-300 font-mono">${careMgmtCost.toLocaleString()}</p>
              <p className="mt-1 text-[11px] text-slate-400">$180/engaged member overhead</p>
            </div>

            <div className="rounded-xl bg-teal-900/60 p-4 border border-teal-600/50">
              <p className="text-[10px] font-bold uppercase tracking-wider text-teal-300">Net Annualized Savings</p>
              <p className="mt-2 text-2xl font-bold text-teal-300 font-mono">${netSavings.toLocaleString()}</p>
              <p className="mt-1 text-[11px] text-teal-200 font-bold">Bottom-Line Payer Value</p>
            </div>
          </div>
        </div>
      </Card>

      {/* Savings Chart & Program ROI Table */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Cumulative Savings Growth Chart */}
        <Card className="p-6">
          <SectionTitle eyebrow="Cost Reduction Trajectory" title="12-Month Cumulative Net Savings Growth" />
          <p className="mt-1 text-xs text-slate-500 mb-4">
            Comparison between baseline claims expenditure trajectory and intervention-adjusted actual claims spend.
          </p>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={savingsTimeline}>
                <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="month" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ background: '#ffffff', border: '1px solid #cbd5e1', borderRadius: 8, fontSize: 12 }} />
                <Bar dataKey="net_savings" name="Cumulative Net Savings ($)" fill="#0d9488" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Program ROI Ledger Table */}
        <Card className="p-6 overflow-hidden">
          <SectionTitle eyebrow="Program Performance" title="Intervention Portfolio ROI Ledger" />
          <p className="mt-1 text-xs text-slate-500 mb-4">
            Audited financial breakdown across active CarePath population intervention tracks.
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-[10px] uppercase tracking-wider text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="p-2.5 font-bold">Intervention Program</th>
                  <th className="p-2.5 font-bold">Enrolled</th>
                  <th className="p-2.5 font-bold">Gross Saved</th>
                  <th className="p-2.5 font-bold">Net ROI</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {interventionsROI.map((item, i) => (
                  <tr key={i} className="hover:bg-slate-50">
                    <td className="p-2.5 font-semibold text-slate-900">{item.program}</td>
                    <td className="p-2.5 font-mono text-slate-700">{item.enrolled}</td>
                    <td className="p-2.5 font-mono font-bold text-teal-800">{item.gross_saved}</td>
                    <td className="p-2.5 font-mono font-bold text-emerald-800 bg-emerald-50 rounded">{item.net_roi}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  );
}

function InsurancePage({ page, memberId }: { page: string; memberId?: string }) {
  const router = useRouter();
  if (page === 'members') return <PageFrame workspace="insurance" title="Members"><MemberTable /></PageFrame>;
  if (page === 'interventions') {
    return (
      <PageFrame workspace="insurance" title="Intervention Engine">
        <div className="flex flex-col gap-5">
          <div>
            <p className="text-xs text-slate-500">Risk + Opportunity + Impact → Priority Score → Queue</p>
            <h2 className="mt-1 text-2xl font-semibold text-slate-950">Intervention Engine</h2>
          </div>
          <MemberTable />
        </div>
      </PageFrame>
    );
  }
  if (memberId) return <MemberDetail memberId={memberId} page={page} />;
  
  return (
    <PageFrame workspace="insurance" title={page === 'trends' ? 'Population Trends' : page === 'impact' ? 'Impact / ROI' : 'Population Analytics'}>
      {page === 'impact' ? <ImpactPage /> : page === 'trends' ? <TrendsPage /> : <InsuranceDashboard />}
    </PageFrame>
  );
}

function PageFrame({ workspace, title, children }: { workspace: Workspace; title: string; children: React.ReactNode }) { const [menu, setMenu] = useState(false); return <div className="min-h-screen bg-slate-100 text-slate-800"><div className="flex min-h-screen"><Sidebar workspace={workspace} setWorkspace={(value) => { window.location.href = value === 'hospital' ? '/hospital' : '/insurance' }} /><main className="min-w-0 flex-1"><Header workspace={workspace} title={title} /><div className="mx-auto max-w-[1500px] p-4 lg:p-8">{children}</div></main></div></div> }

export default function CarePathApp() { const pathname = usePathname(); const hospitalPatient = pathname.match(/^\/hospital\/patients\/([^/]+)(?:\/(journey|explanation|alerts))?$/); const insuranceMember = pathname.match(/^\/insurance\/members\/([^/]+)(?:\/(analysis))?$/); if (pathname === '/' || pathname === '/hospital') return <HospitalDashboard />; if (hospitalPatient) return <PatientDetail id={hospitalPatient[1]} subpage={hospitalPatient[2]} />; if (pathname.startsWith('/hospital/')) return <GenericHospitalPage page={pathname.split('/')[2] ?? 'hospital'} />; if (pathname === '/insurance') return <InsuranceDashboard />; if (insuranceMember) return <InsurancePage page={insuranceMember[2] ?? 'member'} memberId={insuranceMember[1]} />; if (pathname.startsWith('/insurance/')) return <InsurancePage page={pathname.split('/')[2] ?? 'insurance'} />; return <HospitalDashboard /> }
