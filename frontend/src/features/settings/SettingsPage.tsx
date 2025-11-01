import { useState } from 'react';
import { motion } from 'framer-motion';
import { useMutation } from '@tanstack/react-query';
import { BellRing, Palette, ShieldCheck, LogOut, User } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';

import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Input } from '../../components/ui/input';
import { SegmentedControl, SegmentedControlItem } from '../../components/ui/segmented-control';
import { Switch } from '../../components/ui/switch';
import { useTheme } from '../../providers/theme-context';
import { apiClient } from '../../api/client';

const DEFAULT_USER_ID = 'demo-user';

type ApiResult<T> = { data?: T; error?: { detail?: string } };

type PreferenceResponse = {
  user_id: string;
  digest_enabled: boolean;
  digest_time: string | null;
  timezone: string;
};

type ThemeOption = 'dark' | 'light';

export function SettingsPage() {
  const [enabled, setEnabled] = useState(true);
  const [time, setTime] = useState('07:45');
  const [timezone, setTimezone] = useState('Australia/Sydney');
  const { theme, setTheme } = useTheme();

  const mutation = useMutation({
    mutationFn: async () => {
      const response = (await apiClient.POST('/prefs/digest', {
        body: {
          user_id: DEFAULT_USER_ID,
          digest_enabled: enabled,
          digest_time: time,
          timezone,
        },
      })) as ApiResult<PreferenceResponse>;
      if (response.error) {
        throw new Error(response.error.detail ?? 'Failed to persist preferences');
      }
      return response.data;
    },
  });

  return (
    <section className="space-y-8">
      <Card className="border-foreground/12 bg-foreground/[0.08]">
        <CardHeader className="space-y-3">
          <Badge variant="glow">Preferences</Badge>
          <CardTitle className="flex items-center gap-3 text-2xl">
            <BellRing className="h-6 w-6 text-primary" />
            Morning digest preferences
          </CardTitle>
          <CardDescription>
            Configure the AI-powered recap that merges unread emails with travel hints. Preferences are stored securely server-side.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between rounded-2xl border border-foreground/10 bg-foreground/[0.06] p-4 shadow-soft-inner">
            <div>
              <p className="text-sm font-semibold text-foreground">Enable daily digest</p>
              <p className="text-xs text-foreground/55">Send a morning summary to your inbox.</p>
            </div>
            <Switch checked={enabled} onCheckedChange={(value) => setEnabled(Boolean(value))} />
          </div>

          <div className="space-y-4 md:space-y-0 md:grid md:gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <label className="text-xs uppercase tracking-[0.28em] text-foreground/50">Delivery time</label>
              <Input
                type="time"
                value={time}
                onChange={(event) => setTime(event.target.value)}
                disabled={!enabled}
                className="w-full max-w-md"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs uppercase tracking-[0.28em] text-foreground/50">Timezone</label>
              <Input value={timezone} onChange={(event) => setTimezone(event.target.value)} className="w-full max-w-md" />
            </div>
          </div>

          <Button type="button" onClick={() => mutation.mutate()} disabled={mutation.isPending}>
            {mutation.isPending ? 'Saving...' : 'Save preferences'}
          </Button>
          <div className="space-y-2 text-sm">
            {mutation.isError && (
              <p className="rounded-xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
                {(mutation.error as Error).message}
              </p>
            )}
            {mutation.isSuccess && (
              <motion.p
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                className="rounded-xl border border-emerald-400/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-100"
              >
                Preferences updated.
              </motion.p>
            )}
          </div>
        </CardContent>
      </Card>

      <Card className="border-foreground/12 bg-foreground/[0.08]">
        <CardHeader className="space-y-2">
          <CardTitle className="flex items-center gap-3">
            <Palette className="h-5 w-5 text-primary" />
            Theme
          </CardTitle>
          <CardDescription>Switch between dark and light mode. Dark remains the recommended experience.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <SegmentedControl type="single" value={theme as ThemeOption} onValueChange={(value) => setTheme(value as ThemeOption)}>
            <SegmentedControlItem value="dark">Dark</SegmentedControlItem>
            <SegmentedControlItem value="light">Light</SegmentedControlItem>
          </SegmentedControl>
        </CardContent>
      </Card>

      <Card className="border-foreground/12 bg-foreground/[0.08]">
        <CardHeader className="space-y-2">
          <CardTitle className="flex items-center gap-3">
            <ShieldCheck className="h-5 w-5 text-primary" />
            Privacy & data
          </CardTitle>
          <CardDescription>Digest configuration is encrypted at rest and never shared with third parties.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-foreground/65">
          <p>We only store the settings you configure above along with a hashed user identifier.</p>
          <p>You can reset preferences anytime�this clears the digest schedule on the server immediately.</p>
          <Button type="button" variant="ghost" glow={false} className="px-0 text-foreground/70">
            View data retention policy
          </Button>
        </CardContent>
      </Card>

      <AccountSection />
    </section>
  );
}

function AccountSection() {
  const { user, logout } = useAuth();

  return (
    <Card className="border-foreground/12 bg-foreground/[0.08]">
      <CardHeader className="space-y-2">
        <CardTitle className="flex items-center gap-3">
          <User className="h-5 w-5 text-primary" />
          Account
        </CardTitle>
        <CardDescription>Manage your account settings</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between rounded-xl border border-foreground/10 bg-foreground/[0.05] px-4 py-3">
          <div>
            <p className="text-sm font-medium text-foreground">Signed in as</p>
            <p className="text-sm text-foreground/70">{user?.email || 'Guest'}</p>
          </div>
        </div>
        <Button type="button" variant="ghost" onClick={logout} className="gap-2">
          <LogOut className="h-4 w-4" />
          Sign Out
        </Button>
      </CardContent>
    </Card>
  );
}
