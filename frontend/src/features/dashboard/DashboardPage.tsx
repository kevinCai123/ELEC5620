import { motion } from 'framer-motion';
import {
  ArrowRight,
  Brain,
  CalendarClock,
  GraduationCap,
  Mail,
  Map,
  NotebookPen,
  Rocket,
  Settings,
  Sparkles,
  Timer,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { Area, AreaChart, ResponsiveContainer, Tooltip as RechartsTooltip } from 'recharts';

import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';


const quickActions = [
  {
    title: 'Summarize text',
    description: 'Transform dense readings into clear TL;DR notes.',
    to: '/summarize',
    icon: NotebookPen,
    accent: 'from-cyan-400/40 to-indigo-500/20',
  },
  {
    title: 'New quiz',
    description: 'Spin up a 5-question quiz with rationale.',
    to: '/quiz',
    icon: Brain,
    accent: 'from-violet-400/40 to-cyan-300/20',
  },
  {
    title: 'Add deadlines (ICS)',
    description: 'Export milestones straight to Calendar.',
    to: '/study/plan',
    icon: CalendarClock,
    accent: 'from-emerald-400/35 to-teal-500/20',
  },
  {
    title: 'Travel advice',
    description: 'Plan routes with real-time weather hints.',
    to: '/travel',
    icon: Map,
    accent: 'from-amber-400/35 to-pink-400/15',
  },
  {
    title: 'Extract tasks',
    description: 'Convert messy notes into actionable to-dos.',
    to: '/todo',
    icon: Timer,
    accent: 'from-rose-400/35 to-indigo-500/25',
  },
];

const usageSparkline = [
  { day: 'Mon', value: 4 },
  { day: 'Tue', value: 6 },
  { day: 'Wed', value: 9 },
  { day: 'Thu', value: 8 },
  { day: 'Fri', value: 12 },
  { day: 'Sat', value: 7 },
  { day: 'Sun', value: 10 },
];

export function DashboardPage() {
  return (
    <section className="space-y-12">
      <div className="hero-border">
        <div className="hero-content relative overflow-hidden rounded-2xl p-8 sm:p-10">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(255,255,255,0.12),transparent_55%)]" />
          <div className="absolute left-1/2 top-[-30%] h-[320px] w-[540px] -translate-x-1/2 rounded-full bg-aurora opacity-40 blur-3xl" />
          <div className="relative flex flex-col gap-8 lg:flex-row lg:items-center lg:justify-between">
            <div className="max-w-2xl space-y-4">
              <Badge variant="glow" className="inline-flex items-center gap-2 bg-white/10 text-sm tracking-[0.3em]">
                <Sparkles className="h-3.5 w-3.5" />
                Insider
              </Badge>
              <motion.h1
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
                className="text-3xl font-semibold text-foreground sm:text-4xl lg:text-5xl"
              >
                Your personal assistant for everything uni — powered by adaptive AI workflows.
              </motion.h1>
              <p className="text-base text-foreground/70 sm:text-lg">
                Jump into the workflows that matter today. We’ve lined up your inbox insights, study plan, and smart
                automation shortcuts so you can stay in flow.
              </p>
              <div className="flex flex-wrap gap-3">
                <Button asChild>
                  <Link to="/summarize">
                    <Sparkles className="h-4 w-4" />
                    Start a new summary
                  </Link>
                </Button>
                <Button variant="ghost" glow={false} asChild>
                  <Link to="/emails">
                    Review top emails
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                </Button>
              </div>
            </div>
            <div className="relative w-full max-w-sm rounded-3xl border border-white/10 bg-white/5 p-6 text-sm shadow-glow-md backdrop-blur-lg">
              <div className="absolute -right-10 -top-10 h-40 w-40 rounded-full bg-aurora opacity-30 blur-3xl" />
              <p className="text-xs uppercase tracking-[0.35em] text-foreground/50">This week</p>
              <h2 className="mt-2 text-2xl font-semibold text-foreground">Momentum tracker</h2>
              <div className="mt-4 grid gap-3 text-sm">
                <div className="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 px-4 py-3 shadow-soft-inner">
                  <div className="flex items-center gap-2 text-foreground/70">
                    <Mail className="h-4 w-4" />
                    Emails summarised
                  </div>
                  <span className="text-foreground font-semibold">12</span>
                </div>
                <div className="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 px-4 py-3 shadow-soft-inner">
                  <div className="flex items-center gap-2 text-foreground/70">
                    <GraduationCap className="h-4 w-4" />
                    Study milestones
                  </div>
                  <span className="text-foreground font-semibold">5</span>
                </div>
                <div className="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 px-4 py-3 shadow-soft-inner">
                  <div className="flex items-center gap-2 text-foreground/70">
                    <Brain className="h-4 w-4" />
                    Quizzes generated
                  </div>
                  <span className="text-foreground font-semibold">3</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <section className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-6">
          <div>
            <h2 className="text-xl font-semibold text-foreground">Quick actions</h2>
            <p className="text-sm text-foreground/60">
              Launch a curated flow with pre-configured prompts and smart defaults.
            </p>
          </div>
          <Button variant="ghost" glow={false} asChild>
            <Link to="/settings">
              Configure automations
              <Settings className="h-4 w-4" />
            </Link>
          </Button>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {quickActions.map((action) => (
            <Link key={action.title} to={action.to} className="group h-full">
              <Card className="relative h-full overflow-hidden border-white/12 bg-white/10">
                <div
                  className={`pointer-events-none absolute inset-0 bg-gradient-to-br ${action.accent} opacity-0 transition duration-300 group-hover:opacity-100`}
                />
                <CardContent className="relative flex h-full flex-col gap-3 p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3 text-sm text-foreground/60">
                      <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-white/10 bg-white/10 text-foreground">
                        <action.icon className="h-5 w-5" />
                      </div>
                      <span className="text-sm font-medium uppercase tracking-[0.28em] text-foreground/50">
                        Flow
                      </span>
                    </div>
                    <ArrowRight className="h-5 w-5 text-foreground/60 transition group-hover:translate-x-1 group-hover:text-foreground" />
                  </div>
                  <h3 className="text-lg font-semibold text-foreground">{action.title}</h3>
                  <p className="text-sm text-foreground/65">{action.description}</p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <Card className="border-white/12 bg-white/8">
          <CardHeader>
            <CardTitle className="flex items-center gap-3">
              <Rocket className="h-5 w-5 text-primary" />
              Weekly engagement
            </CardTitle>
            <CardDescription>Staying consistent keeps the AI helper learning your preferences.</CardDescription>
          </CardHeader>
          <CardContent className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={usageSparkline}>
                <defs>
                  <linearGradient id="usageGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6E7AFF" stopOpacity={0.7} />
                    <stop offset="95%" stopColor="#22d3ee" stopOpacity={0.05} />
                  </linearGradient>
                </defs>
                <RechartsTooltip
                  cursor={{ stroke: 'rgba(110, 122, 255, 0.4)', strokeWidth: 1 }}
                  contentStyle={{
                    backgroundColor: 'rgba(11,15,23,0.9)',
                    borderRadius: 12,
                    border: '1px solid rgba(255,255,255,0.08)',
                    color: '#e6edf6',
                    padding: '8px 12px',
                  }}
                />
                <Area dataKey="value" stroke="#6E7AFF" strokeWidth={2} fill="url(#usageGradient)" />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <div className="grid gap-4">
          <Card className="border-white/12 bg-white/8">
            <CardHeader>
              <CardTitle className="flex items-center gap-3">
                <Mail className="h-4 w-4 text-primary" />
                Last digest
              </CardTitle>
              <CardDescription>Your Monday morning email summary landed 42 mins ago.</CardDescription>
            </CardHeader>
            <CardContent className="flex items-center justify-between">
              <span className="text-2xl font-semibold text-foreground">98%</span>
              <Badge variant="success">Synced</Badge>
            </CardContent>
          </Card>

          <Card className="border-white/12 bg-white/8">
            <CardHeader>
              <CardTitle className="flex items-center gap-3">
                <Brain className="h-4 w-4 text-primary" />
                Quizzes created
              </CardTitle>
              <CardDescription>Last 14 days</CardDescription>
            </CardHeader>
            <CardContent className="flex items-end justify-between">
              <span className="text-2xl font-semibold text-foreground">12</span>
              <span className="text-xs uppercase tracking-[0.3em] text-foreground/50">+22%</span>
            </CardContent>
          </Card>

          <Card className="border-white/12 bg-white/8">
            <CardHeader>
              <CardTitle className="flex items-center gap-3">
                <Timer className="h-4 w-4 text-primary" />
                Tasks extracted
              </CardTitle>
              <CardDescription>Across to-do and study plan automations.</CardDescription>
            </CardHeader>
            <CardContent className="flex items-center justify-between">
              <span className="text-2xl font-semibold text-foreground">34</span>
              <Badge variant="glow">Optimised</Badge>
            </CardContent>
          </Card>
        </div>
      </section>
    </section>
  );
}

