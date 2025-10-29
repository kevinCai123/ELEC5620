import { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { Compass, Loader2, MapPinned, Search } from 'lucide-react';

import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Input } from '../../components/ui/input';
import { Skeleton } from '../../components/ui/skeleton';
import { apiClient } from '../../api/client';

type CampusPlace = {
  id: string;
  name: string;
  description?: string | null;
  aliases: string[];
  tags: string[];
  latitude?: number | null;
  longitude?: number | null;
};

type PlacesResponse = {
  query: string;
  results: CampusPlace[];
  fallback_used: boolean;
  guidance?: string | null;
};

type ApiResult<T> = { data?: T; error?: { detail?: string } };

export function PlacesPage() {
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');

  useEffect(() => {
    const handler = setTimeout(() => setDebouncedQuery(query.trim()), 300);
    return () => clearTimeout(handler);
  }, [query]);

  const resultsQuery = useQuery({
    queryKey: ['places', debouncedQuery],
    queryFn: async () => {
      const response = (await apiClient.GET('/places', {
        params: { query: { q: debouncedQuery } },
      })) as ApiResult<PlacesResponse>;
      if (response.error) {
        throw new Error(response.error.detail ?? 'Failed to search places');
      }
      return response.data as PlacesResponse;
    },
    enabled: debouncedQuery.length > 0,
  });

  const hasResults = resultsQuery.data?.results?.length;

  const guidance = useMemo(() => {
    if (!resultsQuery.data) return null;
    if (resultsQuery.data.results.length > 0) return null;
    return resultsQuery.data.guidance ?? 'No matches found. Try a building code or landmark alias.';
  }, [resultsQuery.data]);

  return (
    <section className="min-w-0 space-y-8">
      <Card className="min-w-0 border-white/12 bg-white/8">
        <CardHeader className="space-y-3">
          <Badge variant="glow">Campus atlas</Badge>
          <CardTitle className="flex items-center gap-3 text-2xl">
            <Compass className="h-6 w-6 text-primary" />
            Campus location lookup
          </CardTitle>
          <CardDescription>
            Find buildings, study spots, and services with fuzzy search. hover a result to preview the quickest walking route.
          </CardDescription>
        </CardHeader>
        <CardContent className="min-w-0 space-y-6">
          <div className="flex flex-col gap-4 sm:gap-3">
            <div className="flex items-center justify-between gap-4">
              <div className="relative w-full max-w-2xl">
                <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground/40" />
                <Input
                  className="w-full pl-12"
                  placeholder="Search campus"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                />
              </div>
              <Button type="button" variant="secondary" glow={false} disabled className="h-10 shrink-0 rounded-lg px-4">
                Auto search
              </Button>
            </div>
          </div>

          <div className="space-y-3">
            {resultsQuery.isLoading && (
              <div className="flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-foreground/70">
                <Loader2 className="h-4 w-4 animate-spin" /> Searching campus map
              </div>
            )}
            {resultsQuery.error && (
              <p className="rounded-xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
                {(resultsQuery.error as Error).message}
              </p>
            )}
            {guidance && (
              <p className="rounded-xl border border-amber-400/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
                {guidance}
              </p>
            )}
            {hasResults && (
              <div className="max-h-[70dvh] space-y-4 overflow-y-auto overscroll-contain pr-1">
                {resultsQuery.data?.results.map((place, index) => (
                  <motion.div
                    key={place.id}
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: index * 0.04 }}
                    className="group flex min-w-0 flex-col gap-3 rounded-3xl border border-white/10 bg-white/6 p-5 shadow-soft-inner md:flex-row md:items-center md:justify-between"
                  >
                    <div className="min-w-0 space-y-2">
                      <div className="flex flex-wrap items-center gap-3">
                        <h2 className="text-lg font-semibold text-foreground break-words">{place.name}</h2>
                        <Badge variant="outline" className="shrink-0 text-xs text-foreground/60">
                          {place.tags.slice(0, 3).join(' · ') || 'General'}
                        </Badge>
                      </div>
                      {place.description ? (
                        <p className="text-sm text-foreground/70 line-clamp-2">{place.description}</p>
                      ) : (
                        <p className="text-sm text-foreground/50">No description available.</p>
                      )}
                      {place.aliases.length > 0 && (
                        <p className="text-xs uppercase tracking-[0.2em] text-foreground/45 line-clamp-1">
                          Also known as: {place.aliases.join(', ')}
                        </p>
                      )}
                    </div>
                    <Button
                      asChild
                      variant="secondary"
                      className="inline-flex items-center justify-between gap-2 self-start rounded-xl px-4 py-2 md:self-auto"
                    >
                      <a
                        href={`https://www.google.com/maps/dir/?api=1&travelmode=walking&destination=${encodeURIComponent(place.name)}`}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        Route
                        <MapPinned className="h-4 w-4" />
                      </a>
                    </Button>
                  </motion.div>
                ))}
              </div>
            )}
            {debouncedQuery && resultsQuery.isFetching && (
              <div className="space-y-3">
                {Array.from({ length: 2 }).map((_, idx) => (
                  <Skeleton key={idx} className="h-24 w-full rounded-3xl" />
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </section>
  );
}
