import { useMemo, useState } from 'react';
import { AnimatePresence, LayoutGroup, motion } from 'framer-motion';
import { useMutation } from '@tanstack/react-query';
import { CalendarCheck2, CheckCircle2, Plus, Send, Trash2 } from 'lucide-react';
import { z } from 'zod';

import { Button } from '../../components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../../components/ui/card';
import { Input } from '../../components/ui/input';
import { Skeleton } from '../../components/ui/skeleton';
import { Badge } from '../../components/ui/badge';
import { apiClient } from '../../api/client';

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

const itemSchema = z.object({
  title: z.string().min(1, 'Add a descriptive title'),
  dueAt: z.string().min(1, 'Pick a due date'),
});

const planSchema = z.object({
  title: z.string().min(1, 'Give your plan a title'),
  createdBy: z.string().optional(),
  items: z.array(itemSchema).min(3, 'Minimum 3 milestones').max(5, 'Maximum 5 milestones'),
});

type PlanItemForm = z.infer<typeof itemSchema> & { id: string };

type ApiResult<T> = { data?: T; error?: { detail?: string } };

const makeItem = (): PlanItemForm => ({ id: crypto.randomUUID(), title: '', dueAt: '' });

const initialItems: PlanItemForm[] = Array.from({ length: 3 }, makeItem);

export function StudyPlanPage() {
  const [title, setTitle] = useState('');
  const [createdBy, setCreatedBy] = useState('');
  const [items, setItems] = useState<PlanItemForm[]>(initialItems);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [successPlanId, setSuccessPlanId] = useState<number | null>(null);

  const mutation = useMutation({
    mutationFn: async () => {
      const payload = {
        title,
        created_by: createdBy || undefined,
        items: items
          .filter((item) => item.title && item.dueAt)
          .map((item) => ({
            title: item.title,
            due_at: new Date(item.dueAt).toISOString(),
          })),
      };
      const response = (await apiClient.POST('/study/plan', { body: payload })) as ApiResult<{
        plan_id: number;
      }>;
      if (response.error) {
        throw new Error(response.error.detail ?? 'Failed to create study plan');
      }
      return response.data;
    },
    onSuccess: (data) => {
      setSuccessPlanId(data?.plan_id ?? null);
    },
  });

  const canAddMore = items.length < 5;
  const canRemove = items.length > 3;

  const updateItem = (id: string, update: Partial<PlanItemForm>) => {
    setItems((prev) => prev.map((item) => (item.id === id ? { ...item, ...update } : item)));
    setErrors((prev) => {
      const next = { ...prev };
      delete next[`item-${id}`];
      return next;
    });
  };

  const addItem = () => {
    if (canAddMore) {
      setItems((prev) => [...prev, makeItem()]);
    }
  };

  const removeItem = (id: string) => {
    if (canRemove) {
      setItems((prev) => prev.filter((item) => item.id !== id));
      setErrors((prev) => {
        const next = { ...prev };
        delete next[`item-${id}`];
        return next;
      });
    }
  };

  const downloadIcs = () => {
    if (successPlanId) {
      window.open(`${apiBaseUrl}/study/plan/${successPlanId}.ics`, '_blank');
    }
  };

  const validationState = useMemo(() => {
    const result = planSchema.safeParse({
      title,
      createdBy: createdBy || undefined,
      items,
    });
    if (result.success) {
      return { valid: true as const, errors: {} as Record<string, string> };
    }
    const flattened = result.error.flatten();
    const nextErrors: Record<string, string> = {};
    if (flattened.fieldErrors.title?.[0]) {
      nextErrors.title = flattened.fieldErrors.title[0];
    }
    flattened.fieldErrors.items?.forEach((message) => {
      nextErrors.items = message;
    });
    return { valid: false as const, errors: nextErrors };
  }, [createdBy, items, title]);

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const result = planSchema.safeParse({ title, createdBy: createdBy || undefined, items });
    if (!result.success) {
      const flattened = result.error.flatten();
      const nextErrors: Record<string, string> = {};
      if (flattened.fieldErrors.title?.[0]) {
        nextErrors.title = flattened.fieldErrors.title[0];
      }
      flattened.fieldErrors.items?.forEach((message) => {
        nextErrors.items = message;
      });
      result.error.issues.forEach((issue) => {
        if (issue.path[0] === 'items' && typeof issue.path[1] === 'number') {
          const itemForIssue = items[issue.path[1]];
          if (itemForIssue) {
            nextErrors[`item-${itemForIssue.id}`] = issue.message;
          }
        }
      });
      setErrors(nextErrors);
      return;
    }
    setErrors({});
    mutation.mutate();
  };

  return (
    <section className="mx-auto flex w-full max-w-3xl flex-col gap-8 min-w-0">
      <div className="min-w-0 space-y-2">
        <Badge variant="glow">Plan your week</Badge>
        <h1 className="text-3xl font-semibold text-foreground">Craft a focused study plan</h1>
        <p className="max-w-2xl text-sm text-foreground/65">
          Capture 3-5 key deadlines, then export them directly to your calendar with timezone-aware reminders.
        </p>
      </div>

      <Card className="min-w-0 border-white/12 bg-white/8">
        <CardHeader>
          <CardTitle className="flex items-center gap-3">
            <CalendarCheck2 className="h-5 w-5 text-primary" />
            Study milestones
          </CardTitle>
          <CardDescription>Keep it short and punchy—each milestone becomes a calendar event with reminders.</CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit} className="space-y-6">
          <CardContent className="min-w-0 space-y-5">
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-xs uppercase tracking-[0.3em] text-foreground/50">Plan title</label>
                <Input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Final exam prep" className="w-full max-w-md" />
                {errors.title && <p className="text-xs text-rose-300/90">{errors.title}</p>}
              </div>
              <div className="space-y-2">
                <label className="text-xs uppercase tracking-[0.3em] text-foreground/50">Created by (optional)</label>
                <Input value={createdBy} onChange={(event) => setCreatedBy(event.target.value)} placeholder="Your name" className="w-full max-w-md" />
              </div>
            </div>

            {/* LIST CONTAINER: motion-enabled to animate height/flow */}
            <LayoutGroup id="plan-items">
              <motion.div
                layout
                transition={{ layout: { duration: 0.25 } }}
                className="flex flex-col gap-4"
              >
                <AnimatePresence initial={false}>
                  {items.map((item, index) => (
                    <motion.div
                      key={item.id}
                      layout
                      layoutId={item.id}
                      transition={{ layout: { duration: 0.25 } }}
                      exit={{ opacity: 0, height: 0, marginTop: 0, marginBottom: 0 }}
                      style={{ overflow: 'hidden' }} // avoid content spilling during height collapse
                      className="min-w-0 rounded-2xl border border-white/10 bg-white/6 p-4 shadow-soft-inner
                                 space-y-4 lg:grid lg:min-h-0
                                 lg:grid-cols-[minmax(0,280px)_minmax(0,240px)_auto]
                                 lg:items-end lg:gap-3 lg:space-y-0"
                    >
                      <div className="min-w-0 space-y-2">
                        <label className="text-xs uppercase tracking-[0.28em] text-foreground/50">Milestone {index + 1}</label>
                        <Input
                          value={item.title}
                          onChange={(event) => updateItem(item.id, { title: event.target.value })}
                          placeholder="Submit lab report"
                          className="w-full max-w-[280px]"
                        />
                        {errors[`item-${item.id}`] && (
                          <p className="text-xs text-rose-300/90">{errors[`item-${item.id}`]}</p>
                        )}
                      </div>
                      <div className="min-w-0 space-y-2 lg:ml-[50px]">
                        <label className="text-xs uppercase tracking-[0.28em] text-foreground/50">Due at</label>
                        <Input
                          type="datetime-local"
                          value={item.dueAt}
                          onChange={(event) => updateItem(item.id, { dueAt: event.target.value })}
                          className="w-full max-w-[240px]"
                        />
                      </div>
                      <div className="flex items-end justify-end">
                        <Button
                          type="button"
                          variant="ghost"
                          glow={false}
                          onClick={() => removeItem(item.id)}
                          disabled={!canRemove}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </motion.div>
            </LayoutGroup>

            {validationState.errors.items && (
              <p className="text-xs text-rose-300/90">{validationState.errors.items}</p>
            )}

            <div className="flex flex-col gap-3 md:flex-row md:flex-wrap">
              <Button type="button" variant="secondary" onClick={addItem} disabled={!canAddMore}>
                <Plus className="h-4 w-4" />
                Add milestone
              </Button>
              <Button type="submit" disabled={mutation.isPending || !validationState.valid}>
                {mutation.isPending ? (
                  <span className="inline-flex items-center gap-2">
                    <Skeleton className="h-4 w-4 rounded-full" />
                    Saving plan...
                  </span>
                ) : (
                  <>
                    Save plan
                    <Send className="h-4 w-4" />
                  </>
                )}
              </Button>
              <Button type="button" variant="outline" glow={false} onClick={downloadIcs} disabled={!successPlanId}>
                Download .ics
              </Button>
            </div>
          </CardContent>

          <CardFooter className="flex flex-col gap-4">
            {mutation.isError && (
              <p className="w-full rounded-xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
                {(mutation.error as Error).message}
              </p>
            )}
            {successPlanId && (
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="flex w-full flex-col gap-3 rounded-2xl border border-emerald-400/30 bg-emerald-500/10 px-4 py-3 text-emerald-100 md:flex-row md:items-center md:justify-between"
              >
                <div className="flex items-center gap-3">
                  <span className="relative flex h-10 w-10 items-center justify-center">
                    <motion.span
                      className="absolute inset-0 rounded-full border-2 border-emerald-300"
                      animate={{ rotate: 360 }}
                      transition={{ repeat: Infinity, duration: 6, ease: 'linear' }}
                    />
                    <CheckCircle2 className="relative h-6 w-6" />
                  </span>
                  <div>
                    <p className="text-sm font-semibold">Plan saved successfully</p>
                    <p className="text-xs text-emerald-100/70">Download the ICS file or keep refining your milestones.</p>
                  </div>
                </div>
                <Button type="button" variant="secondary" onClick={downloadIcs}>
                  Download .ics
                </Button>
              </motion.div>
            )}
          </CardFooter>
        </form>
      </Card>
    </section>
  );
}
