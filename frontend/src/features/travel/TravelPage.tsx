import { useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { useMutation } from '@tanstack/react-query';
import {
  Cloud,
  CloudLightning,
  CloudRain,
  Eye,
  Gauge,
  MapPin,
  Sunrise,
  Sunset,
  Thermometer,
  ThermometerSun,
  Umbrella,
  Waypoints,
  Wind,
} from 'lucide-react';

import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Input } from '../../components/ui/input';
import { Skeleton } from '../../components/ui/skeleton';
import { apiClient } from '../../api/client';
import { formatDateTime } from '../../lib/utils';

type WeatherInfo = {
  temp_c: number;
  feels_like_c?: number;
  condition_text?: string;
  condition_icon_url?: string;

  rain?: number;                    // 0..1
  precip_mm?: number;
  precipitation_chance?: number;    // 0..1 or 0..100
  cloud?: number;                   // %

  wind_speed?: number;              // m/s
  wind_gust?: number;               // m/s
  wind_dir?: string;

  humidity?: number;                // %
  dew_point_c?: number;
  pressure_hpa?: number;
  visibility_km?: number;
  uv_index?: number;
  aqi?: number;                     // US AQI
  thunder_risk?: number;            // 0..1

  sunrise?: string;                 // ISO
  sunset?: string;                  // ISO
};

type TravelAdvice = {
  leave_time: string;
  recommendation: string;
  bring_items: string[];
  route_url: string;
  fallback_used: boolean;
  weather?: WeatherInfo;
  notes?: string[];
};

type ApiResult<T> = { data?: T; error?: { detail?: string } };

// ---------- helpers ----------
function pctOrFraction(x?: number): number {
  if (x == null) return 0;
  return x > 1 ? Math.min(100, x) : Math.round(x * 100);
}
function kmh(mps?: number): number | undefined {
  return mps == null ? undefined : Math.round(mps * 3.6);
}
function aqiBand(aqi?: number) {
  if (aqi == null) return { label: '—', cls: '' };
  if (aqi <= 50) return { label: 'Good', cls: 'text-emerald-400' };
  if (aqi <= 100) return { label: 'Moderate', cls: 'text-yellow-400' };
  if (aqi <= 150) return { label: 'Unhealthy (SG)', cls: 'text-orange-400' };
  if (aqi <= 200) return { label: 'Unhealthy', cls: 'text-rose-400' };
  if (aqi <= 300) return { label: 'Very Unhealthy', cls: 'text-fuchsia-400' };
  return { label: 'Hazardous', cls: 'text-red-500' };
}

function derivedBringItems(weather?: WeatherInfo): string[] {
  if (!weather) return [];
  const tips: string[] = [];
  const t = weather.feels_like_c ?? weather.temp_c;

  // Rain
  const precipPct = Math.max(pctOrFraction(weather.rain), pctOrFraction(weather.precipitation_chance));
  if (precipPct >= 40 || (weather.precip_mm ?? 0) >= 1) tips.push('Umbrella / rain jacket');

  // Wind
  if ((weather.wind_speed ?? 0) >= 8 || (weather.wind_gust ?? 0) >= 12) tips.push('Windbreaker / light jacket');

  // Heat
  if (t >= 28) tips.push('Light, breathable clothing');

  // Cool/cold
  if (t <= 10) tips.push('Warm jacket; consider gloves');

  // AQI
  if ((weather.aqi ?? 0) >= 100) tips.push('Mask (AQI high)');

  // Humidity comfort
  if ((weather.humidity ?? 0) >= 85 && t >= 24) tips.push('Hand towel');

  // Avoid duplicates
  const seen = new Set<string>();
  return tips.filter(x => !seen.has(x) && seen.add(x));
}

export function TravelPage() {
  const [location, setLocation] = useState('University of Sydney');
  const [eventTime, setEventTime] = useState(() => new Date().toISOString().slice(0, 16));

  const mutation = useMutation({
    mutationFn: async () => {
      if (!eventTime) throw new Error('Event time required');
      const response = (await apiClient.POST('/travel/advise', {
        body: {
          location,
          datetime: new Date(eventTime).toISOString(),
        },
      })) as ApiResult<TravelAdvice>;
      if (response.error) throw new Error(response.error.detail ?? 'Failed to fetch travel advice');
      return response.data as TravelAdvice;
    },
  });

  const advice = mutation.data;

  // Merge server-provided bring_items with client-side derived suggestions, dedup
  const whatToBring = useMemo(() => {
    const base = advice?.bring_items ?? [];
    const derived = derivedBringItems(advice?.weather);
    const seen = new Set<string>();
    return [...base, ...derived].filter(x => !seen.has(x) && seen.add(x));
  }, [advice]);

  const precipPct = useMemo(() => {
    const w = advice?.weather;
    return Math.max(pctOrFraction(w?.rain), pctOrFraction(w?.precipitation_chance));
  }, [advice]);

  return (
    <section className="min-w-0 space-y-8">
      <Card className="min-w-0 border-foreground/12 bg-foreground/[0.08]">
        <CardHeader className="space-y-3">
          <Badge variant="glow">Travel advisor</Badge>
          <CardTitle className="flex items-center gap-3 text-2xl">
            <Waypoints className="h-6 w-6 text-primary" />
            Weather-aware travel timing
          </CardTitle>
          <CardDescription>
            Enter your destination and event time to get a leave recommendation, packing tips, and a walking route — with fallbacks if live data is unavailable.
          </CardDescription>
        </CardHeader>
        <CardContent className="min-w-0">
          <form
            className="space-y-4"
            onSubmit={(e) => {
              e.preventDefault();
              mutation.mutate();
            }}
          >
            <div className="space-y-4">
              <div className="min-w-0 space-y-2">
                <label className="text-xs uppercase tracking-[0.28em] text-foreground/50">Location</label>
                <Input
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
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
                  onChange={(e) => setEventTime(e.target.value)}
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
        <Card className="min-w-0 border-foreground/12 bg-foreground/[0.08]">
          <CardContent className="min-w-0 space-y-3">
            {Array.from({ length: 6 }).map((_, idx) => (
              <Skeleton key={idx} className="h-5 w-full rounded-full" />
            ))}
          </CardContent>
        </Card>
      )}

      {advice && !mutation.isPending && (
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.32, ease: [0.16, 1, 0.3, 1] }}>
          <Card className="relative min-w-0 overflow-hidden border-foreground/12 bg-foreground/10 p-0">
            <div className="absolute -top-32 right-[-10%] h-64 w-64 rounded-full bg-aurora/40 blur-[120px]" />
            <div className="absolute inset-0 rounded-3xl border border-foreground/10" />
            <CardContent className="relative grid gap-8 p-6 lg:grid-cols-[1fr_auto] lg:items-center">
              <div className="min-w-0 space-y-4">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="outline" className="text-foreground/60">
                    {formatDateTime(advice.leave_time)} departure
                  </Badge>
                  {advice.fallback_used && (
                    <Badge variant="outline" className="border-amber-400/30 text-amber-200">
                      Using cached weather
                    </Badge>
                  )}
                </div>

                <h2 className="break-words text-3xl font-semibold text-foreground">{advice.recommendation}</h2>

                <div className="space-y-2 text-sm text-foreground/70">
                  <span className="inline-flex min-w-0 items-center gap-2">
                    <MapPin className="h-4 w-4" />
                    {location}
                  </span>
                  <span className="inline-flex min-w-0 items-center gap-2">
                    <Umbrella className="h-4 w-4" />
                    <span className="flex flex-wrap items-center gap-1">
                      <span className="font-semibold text-foreground">Bring:</span>
                      <span className="break-words">{whatToBring.length ? whatToBring.join(', ') : 'No special items needed.'}</span>
                    </span>
                  </span>
                </div>

                {/* Optional server notes */}
                {!!advice.notes?.length && (
                  <ul className="list-disc space-y-1 pl-5 text-sm text-foreground/70">
                    {advice.notes.map((n, i) => (
                      <li key={i}>{n}</li>
                    ))}
                  </ul>
                )}
              </div>

              <Button asChild variant="secondary" className="inline-flex items-center justify-between gap-3 rounded-xl px-5 py-3">
                <a href={advice.route_url} target="_blank" rel="noopener noreferrer">
                  Open route
                  <Waypoints className="h-4 w-4" />
                </a>
              </Button>
            </CardContent>

            {/* Weather panel */}
            {advice.weather && (
              <div className="border-t border-foreground/10">
                <div className="grid gap-4 p-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                  {/* Headline conditions */}
                  <div className="col-span-full rounded-xl border border-foreground/10 bg-foreground/[0.05] p-4">
                    <div className="flex flex-wrap items-center gap-4">
                      <Thermometer className="h-5 w-5" />
                      <span className="text-lg font-semibold text-foreground">
                        {Math.round(advice.weather.temp_c)}°C
                      </span>
                      {advice.weather.feels_like_c != null && (
                        <span className="text-foreground/70">Feels {Math.round(advice.weather.feels_like_c)}°C</span>
                      )}
                    </div>
                    {advice.weather.condition_text && (
                      <div className="mt-2 flex items-center gap-2 text-sm text-foreground/70">
                        <Cloud className="h-4 w-4" />
                        {advice.weather.condition_text}
                      </div>
                    )}
                  </div>

                  {/* Precipitation & cloud */}
                  <div className="rounded-xl border border-foreground/10 bg-foreground/[0.05] p-4">
                    <div className="mb-2 flex items-center gap-2 font-medium">
                      <CloudRain className="h-4 w-4 text-blue-300" />
                      Precipitation
                    </div>
                    <div className="space-y-1 text-sm text-foreground/70">
                      <div>Chance: <span className="font-semibold text-foreground">{precipPct}%</span></div>
                      {advice.weather.precip_mm != null && <div>Total: ~{advice.weather.precip_mm.toFixed(1)} mm</div>}
                      {advice.weather.cloud != null && (
                        <div className="inline-flex items-center gap-2">
                          <Cloud className="h-4 w-4" />
                          Cloud cover: {advice.weather.cloud}%
                        </div>
                      )}
                      {advice.weather.thunder_risk && advice.weather.thunder_risk >= 0.3 && (
                        <div className="inline-flex items-center gap-2 text-rose-300">
                          <CloudLightning className="h-4 w-4" />
                          Thunder risk: {(advice.weather.thunder_risk * 100).toFixed(0)}%
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Wind */}
                  <div className="rounded-xl border border-foreground/10 bg-foreground/[0.05] p-4">
                    <div className="mb-2 flex items-center gap-2 font-medium">
                      <Wind className="h-4 w-4 text-cyan-300" />
                      Wind
                    </div>
                    <div className="space-y-1 text-sm text-foreground/70">
                      <div>Speed: <span className="font-semibold text-foreground">{kmh(advice.weather.wind_speed) ?? '—'} km/h</span></div>
                      {advice.weather.wind_gust != null && <div>Gust: {kmh(advice.weather.wind_gust)} km/h</div>}
                      {advice.weather.wind_dir && <div>Direction: {advice.weather.wind_dir}</div>}
                    </div>
                  </div>

                  {/* Air & visibility */}
                  <div className="rounded-xl border border-foreground/10 bg-foreground/[0.05] p-4">
                    <div className="mb-2 flex items-center gap-2 font-medium">
                      <Eye className="h-4 w-4 text-teal-300" />
                      Air & visibility
                    </div>
                    <div className="space-y-1 text-sm text-foreground/70">
                      {advice.weather.visibility_km != null && <div>Visibility: {advice.weather.visibility_km.toFixed(1)} km</div>}
                      {advice.weather.humidity != null && <div>Humidity: {advice.weather.humidity}%</div>}
                      {advice.weather.dew_point_c != null && <div>Dew point: {Math.round(advice.weather.dew_point_c)}°C</div>}
                      {advice.weather.pressure_hpa != null && (
                        <div className="inline-flex items-center gap-2">
                          <Gauge className="h-4 w-4" />
                          Pressure: {Math.round(advice.weather.pressure_hpa)} hPa
                        </div>
                      )}
                      {advice.weather.aqi != null && (
                        <div>
                          AQI: <span className={`font-semibold ${aqiBand(advice.weather.aqi).cls}`}>{advice.weather.aqi} — {aqiBand(advice.weather.aqi).label}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Sun times & comfort */}
                  <div className="rounded-xl border border-foreground/10 bg-foreground/[0.05] p-4">
                    <div className="mb-2 flex items-center gap-2 font-medium">
                      <ThermometerSun className="h-4 w-4 text-orange-300" />
                      Comfort
                    </div>
                    <div className="space-y-1 text-sm text-foreground/70">
                      {advice.weather.sunrise && (
                        <div className="inline-flex items-center gap-2">
                          <Sunrise className="h-4 w-4" />
                          Sunrise: {formatDateTime(advice.weather.sunrise)}
                        </div>
                      )}
                      {advice.weather.sunset && (
                        <div className="inline-flex items-center gap-2">
                          <Sunset className="h-4 w-4" />
                          Sunset: {formatDateTime(advice.weather.sunset)}
                        </div>
                      )}
                      {advice.weather.feels_like_c != null && (
                        <div>Heat index: {Math.round(advice.weather.feels_like_c)}°C</div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </Card>
        </motion.div>
      )}
    </section>
  );
}
