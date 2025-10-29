import { useState } from 'react';
import { motion } from 'framer-motion';
import { useMutation } from '@tanstack/react-query';
import { CloudRain, MapPin, Umbrella, Waypoints } from 'lucide-react';

import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Input } from '../../components/ui/input';
import { Skeleton } from '../../components/ui/skeleton';
import { apiClient } from '../../api/client';
import { formatDateTime } from '../../lib/utils';

type TravelAdvice = {
  leave_time: string;
  recommendation: string;
  bring_items: string[];
  route_url: string;
  fallback_used: boolean;
};

type ApiResult<T> = { data?: T; error?: { detail?: string } };

export function TravelPage() {
  const [location, setLocation] = useState('UNSW Sydney');
  const [eventTime, setEventTime] = useState(() => new Date().toISOString().slice(0, 16));

  const mutation = useMutation({
    mutationFn: async () => {
      if (!eventTime) {
        throw new Error('Event time required');
      }
      const response = (await apiClient.POST('/travel/advise', {
        body: {
          location,
          datetime: new Date(eventTime).toISOString(),
        },
      })) as ApiResult<TravelAdvice>;
      if (response.error) {
        throw new Error(response.error.detail ?? 'Failed to fetch travel advice');
      }
      return response.data as TravelAdvice;
    },
  });

  const advice = mutation.data;

  return (
    <section className="min-w-0 space-y-8">
      <Card className="min-w-0 border-white/12 bg-white/8">
        <CardHeader className="space-y-3">
          <Badge variant="glow">Travel advisor</Badge>
          <CardTitle className="flex items-center gap-3 text-2xl">
            <Waypoints className="h-6 w-6 text-primary" />
            Weather-aware travel timing
          </CardTitle>
          <CardDescription>
            Enter your destination and event time to get a leave recommendation, packing tips, and a walking route—with fallbacks if live data is unavailable.
          </CardDescription>
        </CardHeader>
        <CardContent className="min-w-0">
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              mutation.mutate();
            }}
          >
            <div className="space-y-4">
              <div className="min-w-0 space-y-2">
                <label className="text-xs uppercase tracking-[0.28em] text-foreground/50">Location</label>
                <Input
                  value={location}
                  onChange={(event) => setLocation(event.target.value)}
                  placeholder="Campus library"
                  className="w-full max-w-md"
                  required
                />
              </div>
              <div className="min-w-0 space-y-2">
                <label className="text-xs uppercase tracking-[0.28em] text-foreground/50">Event time</label>
                <Input
                  type="datetime-local"
                  value={eventTime}
                  onChange={(event) => setEventTime(event.target.value)}
                  className="w-full max-w-md"
                  required
                />
              </div>
            </div>
            <div className="flex flex-col gap-3 pt-2 md:flex-row md:flex-wrap">
              <Button type="submit" disabled={mutation.isPending || !eventTime || !location}>
                {mutation.isPending ? (
                  <span className="inline-flex items-center gap-2">
                    Calculating
                    <Skeleton className="h-4 w-4 rounded-full" />
                  </span>
                ) : (
                  <>
                    Get advice
                    <CloudRain className="h-4 w-4" />
                  </>
                )}
              </Button>
            </div>
          </form>
          {mutation.isError && (
            <p className="mt-4 rounded-xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
              {(mutation.error as Error).message}
            </p>
          )}
        </CardContent>
      </Card>

      {mutation.isPending && (
        <Card className="min-w-0 border-white/12 bg-white/8">
          <CardContent className="min-w-0 space-y-3">
            {Array.from({ length: 4 }).map((_, idx) => (
              <Skeleton key={idx} className="h-5 w-full rounded-full" />
            ))}
          </CardContent>
        </Card>
      )}

      {advice && !mutation.isPending && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.32, ease: [0.16, 1, 0.3, 1] }}
        >
          <Card className="relative min-w-0 overflow-hidden border-white/12 bg-white/10 p-0">
            <div className="absolute -top-32 right-[-10%] h-64 w-64 rounded-full bg-aurora/40 blur-[120px]" />
            <div className="absolute inset-0 rounded-3xl border border-white/10" />
            <CardContent className="relative grid gap-6 p-6 lg:grid-cols-[1fr_auto] lg:items-center">
              <div className="min-w-0 space-y-4">
                <Badge variant="outline" className="text-foreground/60">
                  {formatDateTime(advice.leave_time)} departure
                </Badge>
                <h2 className="text-3xl font-semibold text-foreground break-words">{advice.recommendation}</h2>
                <div className="space-y-2 text-sm text-foreground/70">
                  <span className="inline-flex min-w-0 items-center gap-2">
                    <MapPin className="h-4 w-4" />
                    {location}
                  </span>
                  <span className="inline-flex min-w-0 items-center gap-2">
                    <Umbrella className="h-4 w-4" />
                    <span className="flex flex-wrap items-center gap-1">
                      <span className="font-semibold text-foreground">Bring:</span>
                      <span className="break-words">{advice.bring_items.join(', ')}</span>
                    </span>
                  </span>
                </div>
                {advice.fallback_used && (
                  <p className="inline-flex items-center gap-2 rounded-pill border border-amber-400/30 bg-amber-500/10 px-3 py-1 text-xs font-medium text-amber-100">
                    Using cached weather insights while live data reconnects.
                  </p>
                )}
              </div>
              <Button
                asChild
                variant="secondary"
                className="inline-flex items-center justify-between gap-3 rounded-xl px-5 py-3"
              >
                <a href={advice.route_url} target="_blank" rel="noopener noreferrer">
                  Open route
                  <Waypoints className="h-4 w-4" />
                </a>
              </Button>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </section>
  );
}
