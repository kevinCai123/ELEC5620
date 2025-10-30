import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { ExternalLink, Inbox, RefreshCw, Sparkles, CheckCircle2, Tag, Mail, ChevronLeft, ChevronRight } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';

import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { Skeleton } from '../../components/ui/skeleton';
import { apiClient } from '../../api/client';

const EMAILS_QUERY_KEY = ['emails', 'top'] as const;

type EmailSummary = {
  id: string;
  subject: string;
  sender: string;
  summary: string;
  key_points: string[];
  category: string;
  original_url?: string | null;
};

type TopEmailsResponse = {
  emails: EmailSummary[];
  fallback_used: boolean;
};

type ApiResult<T> = { data?: T; error?: { detail?: string } };

const EMAILS_PER_PAGE = 6;
const TOTAL_EMAILS = 30;

export function EmailsPage() {
  const [selectedEmail, setSelectedEmail] = useState<EmailSummary | null>(null);
  const [currentPage, setCurrentPage] = useState(1);

  const { data, isPending, error, refetch } = useQuery({
    queryKey: EMAILS_QUERY_KEY,
    queryFn: async () => {
      const response = (await apiClient.GET('/emails/top', {
        params: { query: { n: TOTAL_EMAILS } },
      })) as ApiResult<TopEmailsResponse>;
      if (response.error) {
        throw new Error(response.error.detail ?? 'Failed to load emails');
      }
      return response.data as TopEmailsResponse;
    },
    staleTime: 120_000,
  });

  const isEmpty = data && data.emails.length === 0;

  // Pagination calculations
  const totalPages = data ? Math.ceil(data.emails.length / EMAILS_PER_PAGE) : 0;
  const paginatedEmails = useMemo(() => {
    if (!data) return [];
    const startIndex = (currentPage - 1) * EMAILS_PER_PAGE;
    const endIndex = startIndex + EMAILS_PER_PAGE;
    return data.emails.slice(startIndex, endIndex);
  }, [data, currentPage]);

  const handleNextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handlePreviousPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  return (
    <section className="min-w-0 space-y-10">
      <div className="flex flex-wrap items-end justify-between gap-6">
        <div className="space-y-2">
          <Badge variant="glow">Inbox briefing</Badge>
          <h1 className="text-3xl font-semibold text-foreground">Unread highlights</h1>
          <p className="max-w-2xl text-sm text-foreground/65">
            We surface the most actionable lines so you can decide what needs your attention first. Click a card to view
            full summary.
          </p>
          {data && !isEmpty && (
            <p className="text-sm text-foreground/50">
              Showing {paginatedEmails.length} of {data.emails.length} emails · Page {currentPage} of {totalPages}
            </p>
          )}
          {data?.fallback_used && (
            <div className="inline-flex items-center gap-2 rounded-pill border border-amber-400/40 bg-amber-400/10 px-3 py-1 text-xs font-medium text-amber-200">
              <Sparkles className="h-3.5 w-3.5" />
              Cached summaries shown while reconnecting
            </div>
          )}
        </div>
        <Button variant="ghost" glow={false} onClick={() => refetch()} disabled={isPending}>
          Refresh
          <RefreshCw className={`h-4 w-4 ${isPending ? 'animate-spin' : ''}`} />
        </Button>
      </div>

      {isPending && (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 4 }).map((_, idx) => (
            <Card key={idx} className="min-h-[120px] border-white/12 bg-white/8">
              <CardHeader className="space-y-2">
                <div className="flex items-center gap-3">
                  <Skeleton className="h-10 w-10 rounded-full" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-3 w-3/4 rounded-full" />
                    <Skeleton className="h-3 w-1/2 rounded-full" />
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <Skeleton className="h-3 w-full" />
                <Skeleton className="h-3 w-5/6" />
                <Skeleton className="h-3 w-4/5" />
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {error && !isPending && (
        <Card className="border-red-400/30 bg-red-500/10">
          <CardHeader>
            <CardTitle className="text-red-200">Unable to load emails</CardTitle>
            <CardDescription className="text-red-200/70">{(error as Error).message}</CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="destructive" onClick={() => refetch()}>
              Try again
            </Button>
          </CardContent>
        </Card>
      )}

      {isEmpty && !error && (
        <Card className="border-white/10 bg-white/4 text-foreground/70">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-foreground">
              <Inbox className="h-5 w-5 text-primary" />
              Inbox zero achieved
            </CardTitle>
            <CardDescription className="text-foreground/60">
              Everything is up to speed. We&apos;ll notify you when new highlights land.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="ghost" glow={false} onClick={() => refetch()}>
              Refresh now
              <RefreshCw className="h-4 w-4" />
            </Button>
          </CardContent>
        </Card>
      )}

      {data && data.emails.length > 0 && (
        <>
          <motion.div layout className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {paginatedEmails.map((email) => (
              <motion.div
                layout
                key={email.id}
                onClick={() => setSelectedEmail(email)}
                className="group relative block min-h-[120px] min-w-0 cursor-pointer overflow-hidden rounded-3xl border border-white/10 bg-white/6 p-6 text-left shadow-glow-md transition duration-300 ease-aurora hover:-translate-y-1 hover:border-white/20 hover:drop-shadow-glow"
              >
                <div className="absolute -right-10 top-0 h-24 w-24 rounded-full bg-aurora opacity-0 blur-2xl transition duration-300 group-hover:opacity-50" />
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <span className="flex h-10 w-10 items-center justify-center rounded-full border border-white/10 bg-white/5 text-sm font-semibold text-foreground">
                      {email.sender.slice(0, 2).toUpperCase()}
                    </span>
                    <div className="min-w-0 flex-1">
                      <h2 className="text-lg font-semibold text-foreground line-clamp-2">{email.subject}</h2>
                      <p className="text-xs uppercase tracking-[0.28em] text-foreground/45 line-clamp-1">{email.sender}</p>
                    </div>
                  </div>
                </div>
                <p className="mt-4 text-sm text-foreground/70 line-clamp-2">{email.summary}</p>
                {email.key_points && email.key_points.length > 0 && (
                  <div className="mt-4 space-y-2">
                    {email.key_points.slice(0, 2).map((point, idx) => (
                      <div key={idx} className="flex items-start gap-2 text-sm text-foreground/60">
                        <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
                        <span className="line-clamp-1">{point}</span>
                      </div>
                    ))}
                    {email.key_points.length > 2 && (
                      <p className="text-xs text-foreground/45">+{email.key_points.length - 2} more...</p>
                    )}
                  </div>
                )}
                <div className="mt-6 flex items-center justify-between gap-4">
                  {email.original_url && (
                    <a
                      href={email.original_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.3em] text-primary transition hover:text-primary/80"
                    >
                      Open original
                      <ExternalLink className="h-4 w-4" />
                    </a>
                  )}
                  <Badge 
                    variant="outline" 
                    className="shrink-0 capitalize text-xs"
                  >
                    <Tag className="mr-1 h-3 w-3" />
                    {email.category}
                  </Badge>
                </div>
              </motion.div>
            ))}
          </motion.div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between gap-4 rounded-2xl border border-white/10 bg-white/5 p-4">
              <Button
                variant="ghost"
                onClick={handlePreviousPage}
                disabled={currentPage === 1}
                className="gap-2"
              >
                <ChevronLeft className="h-4 w-4" />
                Previous
              </Button>

              <div className="flex items-center gap-2">
                {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                  <button
                    key={page}
                    onClick={() => {
                      setCurrentPage(page);
                      window.scrollTo({ top: 0, behavior: 'smooth' });
                    }}
                    className={`flex h-10 w-10 items-center justify-center rounded-lg border transition ${
                      page === currentPage
                        ? 'border-primary bg-primary/20 font-semibold text-primary'
                        : 'border-white/10 bg-white/5 text-foreground/60 hover:border-white/20 hover:bg-white/10'
                    }`}
                  >
                    {page}
                  </button>
                ))}
              </div>

              <Button
                variant="ghost"
                onClick={handleNextPage}
                disabled={currentPage === totalPages}
                className="gap-2"
              >
                Next
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          )}

          {/* Email Detail Dialog */}
          <Dialog open={!!selectedEmail} onOpenChange={(open) => !open && setSelectedEmail(null)}>
            <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
              {selectedEmail && (
                <>
                  <DialogHeader>
                    <div className="flex items-start gap-4">
                      <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full border border-white/10 bg-white/5 text-base font-semibold text-foreground">
                        {selectedEmail.sender.slice(0, 2).toUpperCase()}
                      </span>
                      <div className="min-w-0 flex-1">
                        <DialogTitle className="text-xl text-foreground">{selectedEmail.subject}</DialogTitle>
                        <DialogDescription className="mt-1 text-sm text-foreground/60">
                          From: {selectedEmail.sender}
                        </DialogDescription>
                        <Badge variant="outline" className="mt-2 capitalize">
                          <Tag className="mr-1 h-3 w-3" />
                          {selectedEmail.category}
                        </Badge>
                      </div>
                    </div>
                  </DialogHeader>

                  <div className="space-y-6 pt-4">
                    {/* Summary */}
                    <div>
                      <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-foreground/70">
                        <Mail className="h-4 w-4" />
                        Summary
                      </h3>
                      <p className="text-base text-foreground/80">{selectedEmail.summary}</p>
                    </div>

                    {/* Key Points */}
                    {selectedEmail.key_points && selectedEmail.key_points.length > 0 && (
                      <div>
                        <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-foreground/70">
                          <CheckCircle2 className="h-4 w-4" />
                          Key Points
                        </h3>
                        <div className="space-y-3">
                          {selectedEmail.key_points.map((point, idx) => (
                            <div
                              key={idx}
                              className="flex items-start gap-3 rounded-xl border border-white/10 bg-white/5 p-4"
                            >
                              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                              <p className="text-sm text-foreground/80">{point}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Open Original Link */}
                    {selectedEmail.original_url && (
                      <div className="flex justify-end border-t border-white/10 pt-4">
                        <Button asChild variant="default">
                          <a
                            href={selectedEmail.original_url}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            Open Original Email
                            <ExternalLink className="ml-2 h-4 w-4" />
                          </a>
                        </Button>
                      </div>
                    )}
                  </div>
                </>
              )}
            </DialogContent>
          </Dialog>
        </>
      )}
    </section>
  );
}
