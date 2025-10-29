import { useMemo, useState } from 'react';
import { AnimatePresence, Reorder, motion } from 'framer-motion';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { CalendarDays, Check, ClipboardPaste, Clock, ListChecks, Wand2 } from 'lucide-react';

import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Input } from '../../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Skeleton } from '../../components/ui/skeleton';
import { Textarea } from '../../components/ui/textarea';
import { apiClient } from '../../api/client';
import { formatDateTime } from '../../lib/utils';

type DraftTask = {
  title: string;
  dueAt: string;
  dueAtConfidence: string;
};

type TodoExtractApiResponse = {
  drafts: {
    title: string;
    due_at?: string | null;
    due_at_confidence?: string | null;
  }[];
};

type SavedTask = {
  id: number;
  title: string;
  due_at: string | null;
  due_at_confidence: string | null;
  status: string;
};

type TodoListResponse = {
  todos: SavedTask[];
};

type ApiResult<T> = { data?: T; error?: { detail?: string } };

const TODOS_QUERY_KEY = ['todos'] as const;

const quickDueOptions = [
  { label: 'Today', offsetHours: 6 },
  { label: 'Tomorrow', offsetHours: 30 },
  { label: 'Next week', offsetHours: 24 * 7 },
];

export function TodoPage() {
  const [sourceText, setSourceText] = useState('');
  const [drafts, setDrafts] = useState<DraftTask[]>([]);
  const queryClient = useQueryClient();

  const todosQuery = useQuery({
    queryKey: TODOS_QUERY_KEY,
    queryFn: async () => {
      const response = (await apiClient.GET('/todo', {})) as ApiResult<TodoListResponse>;
      if (response.error) {
        throw new Error(response.error.detail ?? 'Failed to load todos');
      }
      return response.data?.todos ?? [];
    },
  });

  const extractMutation = useMutation({
    mutationFn: async () => {
      const response = (await apiClient.POST('/todo/extract', {
        body: { text: sourceText },
      })) as ApiResult<TodoExtractApiResponse>;
      if (response.error) {
        throw new Error(response.error.detail ?? 'Failed to extract tasks');
      }
      return response.data as TodoExtractApiResponse;
    },
    onSuccess: (data) => {
      const mapped = (data?.drafts ?? []).map((draft) => ({
        title: draft.title,
        dueAt: draft.due_at ? new Date(draft.due_at).toISOString().slice(0, 16) : '',
        dueAtConfidence: draft.due_at_confidence ?? 'low',
      }));
      setDrafts(mapped);
    },
  });

  const saveMutation = useMutation({
    mutationFn: async () => {
      const payload = {
        tasks: drafts.map((draft) => ({
          title: draft.title,
          due_at: draft.dueAt ? new Date(draft.dueAt).toISOString() : null,
          due_at_confidence: draft.dueAtConfidence,
        })),
      };
      const response = (await apiClient.POST('/todo', { body: payload })) as ApiResult<unknown>;
      if (response.error) {
        throw new Error(response.error.detail ?? 'Failed to save tasks');
      }
      return response.data;
    },
    onSuccess: () => {
      setDrafts([]);
      queryClient.invalidateQueries({ queryKey: TODOS_QUERY_KEY });
    },
  });

  const hasDrafts = drafts.length > 0;

  const handleDraftChange = (index: number, update: Partial<DraftTask>) => {
    setDrafts((prev) => prev.map((draft, idx) => (idx === index ? { ...draft, ...update } : draft)));
  };

  const applyQuickDue = (index: number, offsetHours: number) => {
    const target = new Date();
    target.setHours(target.getHours() + offsetHours);
    handleDraftChange(index, { dueAt: target.toISOString().slice(0, 16) });
  };

  const draftSummary = useMemo(() => {
    if (!hasDrafts) return '';
    const dueSoon = drafts.filter((draft) => draft.dueAt).
      map((draft) => `• ${draft.title} → ${formatDateTime(draft.dueAt)}`);
    return dueSoon.join('\n');
  }, [drafts, hasDrafts]);

  return (
    <section className="min-w-0 space-y-10">
      <Card className="min-w-0 border-white/12 bg-white/8">
        <CardHeader className="space-y-3">
          <Badge variant="glow">Smart capture</Badge>
          <CardTitle className="flex items-center gap-3 text-2xl">
            <ClipboardPaste className="h-6 w-6 text-primary" />
            Smart to-do extraction
          </CardTitle>
          <CardDescription>
            Paste any email or notes. We create editable drafts and highlight low-confidence due dates for your review.
          </CardDescription>
        </CardHeader>
        <CardContent className="min-w-0">
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              extractMutation.mutate();
            }}
          >
            <div className="space-y-2">
              <label className="text-xs uppercase tracking-[0.28em] text-foreground/50">Source text</label>
              <Textarea
                value={sourceText}
                onChange={(event) => setSourceText(event.target.value)}
                placeholder="Paste message content here"
                className="min-h-[220px] w-full max-w-full"
                required
              />
            </div>
            <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
              <Button type="submit" disabled={extractMutation.isPending || !sourceText}>
                {extractMutation.isPending ? (
                  <span className="inline-flex items-center gap-2">
                    Extracting
                    <Skeleton className="h-4 w-4 rounded-full" />
                  </span>
                ) : (
                  <>
                    Extract tasks
                    <Wand2 className="h-4 w-4" />
                  </>
                )}
              </Button>
              {hasDrafts && (
                <Button
                  type="button"
                  variant="ghost"
                  glow={false}
                  onClick={() => navigator.clipboard.writeText(draftSummary)}
                  disabled={!draftSummary}
                >
                  Copy summary
                  <Check className="h-4 w-4" />
                </Button>
              )}
            </div>
            {extractMutation.isError && (
              <p className="rounded-xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
                {(extractMutation.error as Error).message}
              </p>
            )}
            {saveMutation.isError && (
              <p className="rounded-xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
                {(saveMutation.error as Error).message}
              </p>
            )}
            {hasDrafts && (
              <p className="rounded-xl border border-cyan-400/30 bg-cyan-500/10 px-4 py-3 text-sm text-cyan-100">
                Review the drafts below. Low-confidence dates are flagged for you to confirm.
              </p>
            )}
          </form>
        </CardContent>
      </Card>

      {hasDrafts && (
        <Card className="min-w-0 border-white/12 bg-white/8">
          <CardHeader>
            <CardTitle className="flex items-center gap-3">
              <ListChecks className="h-5 w-5 text-primary" />
              Draft tasks
            </CardTitle>
            <CardDescription>Reorder, tweak due dates, or mark confidence before saving.</CardDescription>
          </CardHeader>
          <CardContent className="min-w-0 space-y-4">
            <Reorder.Group axis="y" values={drafts} onReorder={(values) => setDrafts(values)} className="flex flex-col gap-4">
              {drafts.map((draft, index) => (
                <Reorder.Item key={`${draft.title}-${index}`} value={draft} className="min-w-0">
                  <motion.div
                    whileHover={{ y: -2 }}
                    className="min-w-0 rounded-3xl border border-white/10 bg-white/6 p-5 shadow-soft-inner"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <Badge variant="outline" className="text-xs text-foreground/60">
                        Task {index + 1}
                      </Badge>
                      <Clock className="h-4 w-4 text-foreground/50" />
                    </div>
                    <div className="mt-3 space-y-4 md:space-y-0 md:grid md:gap-4 md:grid-cols-[minmax(0,1fr)_minmax(0,220px)_minmax(0,180px)]">
                      <div className="space-y-2">
                        <Input
                          value={draft.title}
                          onChange={(event) => handleDraftChange(index, { title: event.target.value })}
                          placeholder="Follow up with team"
                          className="w-full max-w-md"
                        />
                      </div>
                      <div className="space-y-2">
                        <Input
                          type="datetime-local"
                          value={draft.dueAt}
                          onChange={(event) => handleDraftChange(index, { dueAt: event.target.value })}
                          className="w-full max-w-md"
                        />
                        <div className="flex flex-wrap gap-2">
                          {quickDueOptions.map((option) => (
                            <Button
                              key={option.label}
                              type="button"
                              variant="ghost"
                              glow={false}
                              className="h-8 rounded-full px-3 text-xs"
                              onClick={() => applyQuickDue(index, option.offsetHours)}
                            >
                              {option.label}
                            </Button>
                          ))}
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Select
                          value={draft.dueAtConfidence}
                          onValueChange={(value) => handleDraftChange(index, { dueAtConfidence: value })}
                        >
                          <SelectTrigger className="h-10">
                            <SelectValue placeholder="Confidence" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="high">High confidence</SelectItem>
                            <SelectItem value="medium">Medium</SelectItem>
                            <SelectItem value="low">Low confidence</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  </motion.div>
                </Reorder.Item>
              ))}
            </Reorder.Group>
            <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
              <Button type="button" variant="secondary" onClick={() => setDrafts([])}>
                Clear drafts
              </Button>
              <Button type="button" onClick={() => saveMutation.mutate()} disabled={saveMutation.isPending}>
                {saveMutation.isPending ? 'Saving...' : 'Save to list'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Card className="min-w-0 border-white/12 bg-white/8">
        <CardHeader>
          <CardTitle className="flex items-center gap-3">
            <CalendarDays className="h-5 w-5 text-primary" />
            Saved tasks
          </CardTitle>
          <CardDescription>Your synced tasks stay in one place, ready for review each morning.</CardDescription>
        </CardHeader>
        <CardContent className="min-w-0 space-y-4">
          {todosQuery.isLoading && <Skeleton className="h-10 w-full rounded-xl" />}
          {todosQuery.error && (
            <p className="rounded-xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
              {(todosQuery.error as Error).message}
            </p>
          )}
          {todosQuery.data && todosQuery.data.length === 0 && (
            <p className="rounded-2xl border border-white/10 bg-white/6 px-4 py-3 text-sm text-foreground/70">
              No tasks saved yet. Extract a few to get started.
            </p>
          )}
          {todosQuery.data && todosQuery.data.length > 0 && (
            <div className="overflow-hidden rounded-2xl border border-white/10 divide-y divide-white/10">
              <AnimatePresence initial={false}>
                {todosQuery.data.map((todo) => (
                  <motion.div
                    key={todo.id}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    className="flex items-center justify-between gap-4 px-5 py-4 text-sm text-foreground/80"
                  >
                    <div className="min-w-0">
                      <p className="font-semibold text-foreground line-clamp-2">{todo.title}</p>
                      {todo.due_at && (
                        <p className="text-xs text-foreground/55">
                          Due {formatDateTime(todo.due_at)} ({todo.due_at_confidence ?? 'low'})
                        </p>
                      )}
                    </div>
                    <Badge variant="outline" className="shrink-0 text-xs text-foreground/60">
                      Status: {todo.status}
                    </Badge>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}
        </CardContent>
      </Card>
    </section>
  );
}
