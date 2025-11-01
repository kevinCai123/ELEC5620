import { useMemo, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { CalendarCheck2, CheckCircle2, Send } from 'lucide-react';
import { z } from 'zod';

import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../../components/ui/card';
import { Input } from '../../components/ui/input';
import { Skeleton } from '../../components/ui/skeleton';
import { apiClient } from '../../api/client';

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

const itemSchema = z.object({
  title: z.string().min(1, 'Add a descriptive title'),
  dueAt: z.string().min(1, 'Pick a due date'),
});

const planSchema = z.object({
  title: z.string().min(1, 'Give your plan a title'),
  recipientEmail: z.string().email('Enter a valid email address').optional(),
  items: z.array(itemSchema).length(1, 'One milestone required'),
});

type PlanItemForm = z.infer<typeof itemSchema> & { id: string };

type ApiResult<T> = { data?: T; error?: { detail?: string } };

type PlanCreationResponse = {
  plan_id: number;
  email_sent: boolean;
};

const makeItem = (): PlanItemForm => ({ id: crypto.randomUUID(), title: '', dueAt: '' });

const initialItems: PlanItemForm[] = [makeItem()];

export function PlanPage() {
  const [title, setTitle] = useState('');
  const [recipientEmail, setRecipientEmail] = useState('');
  const [items, setItems] = useState<PlanItemForm[]>(initialItems);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [successPlanId, setSuccessPlanId] = useState<number | null>(null);
  const [emailSent, setEmailSent] = useState(false);

  const mutation = useMutation({
    mutationFn: async () => {
      console.log('🚀 Mutation starting...');
      const trimmedEmail = recipientEmail.trim();
      const payload = {
        title,
        created_by: trimmedEmail || undefined,
        recipient_email: trimmedEmail || undefined,
        items: items
          .filter((item) => item.title && item.dueAt)
          .map((item) => ({
            title: item.title,
            due_at: new Date(item.dueAt).toISOString(),
          })),
      };
      console.log('📦 Payload:', payload);
      console.log('🌐 Sending POST to /study/plan...');
      const response = (await apiClient.POST('/study/plan', { body: payload })) as ApiResult<PlanCreationResponse>;
      console.log('📥 Response received:', response);
      if (response.error) {
        console.error('❌ Response has error:', response.error);
        throw new Error(response.error.detail ?? 'Failed to create plan');
      }
      console.log('✅ Success! Data:', response.data);
      return response.data;
    },
    onSuccess: (data) => {
      console.log('🎉 onSuccess callback, data:', data);
      setSuccessPlanId(data?.plan_id ?? null);
      setEmailSent(Boolean(data?.email_sent));
    },
    onError: (error) => {
      console.error('💥 onError callback:', error);
    },
  });

  const updateItem = (id: string, update: Partial<PlanItemForm>) => {
    setItems((prev) => prev.map((item) => (item.id === id ? { ...item, ...update } : item)));
    setErrors((prev) => {
      const next = { ...prev };
      delete next[`item-${id}`];
      return next;
    });
  };

  const downloadIcs = () => {
    if (successPlanId) {
      window.open(`${apiBaseUrl}/plan/${successPlanId}.ics`, '_blank');
    }
  };

  const validationState = useMemo(() => {
    const result = planSchema.safeParse({
      title,
      recipientEmail: recipientEmail.trim() || undefined,
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
    if (flattened.fieldErrors.recipientEmail?.[0]) {
      nextErrors.recipientEmail = flattened.fieldErrors.recipientEmail[0];
    }
    flattened.fieldErrors.items?.forEach((message) => {
      nextErrors.items = message;
    });
    return { valid: false as const, errors: nextErrors };
  }, [recipientEmail, items, title]);

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    console.log('📝 Form submitted!');
    console.log('Title:', title);
    console.log('Email:', recipientEmail);
    console.log('Items:', items);
    
    const result = planSchema.safeParse({
      title,
      recipientEmail: recipientEmail.trim() || undefined,
      items,
    });
    
    console.log('Validation result:', result.success);
    
    if (!result.success) {
      console.error('❌ Validation failed:', result.error);
      const flattened = result.error.flatten();
      const nextErrors: Record<string, string> = {};
      if (flattened.fieldErrors.title?.[0]) {
        nextErrors.title = flattened.fieldErrors.title[0];
      }
      if (flattened.fieldErrors.recipientEmail?.[0]) {
        nextErrors.recipientEmail = flattened.fieldErrors.recipientEmail[0];
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
      console.log('Errors set:', nextErrors);
      return;
    }
    
    console.log('✅ Validation passed, sending request...');
    setErrors({});
    setEmailSent(false);
    mutation.mutate();
  };

  return (
    <section className="mx-auto flex w-full max-w-3xl flex-col gap-8 min-w-0">
      <div className="min-w-0 space-y-2">
        <Badge variant="glow">Plan your week</Badge>
        <h1 className="text-3xl font-semibold text-foreground">Craft a focused plan</h1>
        <p className="max-w-2xl text-sm text-foreground/65">
          Create a single milestone with a deadline, then email the calendar-ready plan straight to Gmail with timezone-aware
          reminders.
        </p>
      </div>

      <Card className="min-w-0 border-foreground/12 bg-foreground/[0.08]">
        <CardHeader>
          <CardTitle className="flex items-center gap-3">
            <CalendarCheck2 className="h-5 w-5 text-primary" />
            Plan milestones
          </CardTitle>
          <CardDescription>Each item becomes a calendar event—perfect for deadlines, launches, or checkpoints.</CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit} className="space-y-6">
          <CardContent className="min-w-0 space-y-5">
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-xs uppercase tracking-[0.3em] text-foreground/50">Plan title</label>
                <Input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Project launch prep" className="w-full max-w-md" />
                {errors.title && <p className="text-xs text-rose-300/90">{errors.title}</p>}
              </div>
              <div className="space-y-2">
                <label className="text-xs uppercase tracking-[0.3em] text-foreground/50">Send to Gmail (optional)</label>
                <Input
                  value={recipientEmail}
                  onChange={(event) => setRecipientEmail(event.target.value)}
                  placeholder="you@gmail.com"
                  className="w-full max-w-md"
                />
                {errors.recipientEmail && <p className="text-xs text-rose-300/90">{errors.recipientEmail}</p>}
              </div>
            </div>

            <div className="min-w-0 rounded-2xl border border-foreground/10 bg-foreground/[0.06] p-4 shadow-soft-inner
                           space-y-4 lg:grid lg:min-h-0
                           lg:grid-cols-[minmax(0,280px)_minmax(0,240px)]
                           lg:items-end lg:gap-[74px] lg:space-y-0"
            >
              <div className="min-w-0 space-y-2">
                <label className="text-xs uppercase tracking-[0.28em] text-foreground/50">Milestone</label>
                <Input
                  value={items[0]?.title || ''}
                  onChange={(event) => items[0] && updateItem(items[0].id, { title: event.target.value })}
                  placeholder="Finalize budget proposal"
                  className="w-full max-w-[280px]"
                />
                {items[0] && errors[`item-${items[0].id}`] && (
                  <p className="text-xs text-rose-300/90">{errors[`item-${items[0].id}`]}</p>
                )}
              </div>
              <div className="min-w-0 space-y-2">
                <label className="text-xs uppercase tracking-[0.28em] text-foreground/50">Due at</label>
                <Input
                  type="datetime-local"
                  value={items[0]?.dueAt || ''}
                  onChange={(event) => items[0] && updateItem(items[0].id, { dueAt: event.target.value })}
                  className="w-full max-w-[240px]"
                />
              </div>
            </div>

            {validationState.errors.items && (
              <p className="text-xs text-rose-300/90">{validationState.errors.items}</p>
            )}

            <div className="flex flex-col gap-3 md:flex-row md:flex-wrap">
              <Button type="submit" disabled={mutation.isPending || !validationState.valid}>
                {mutation.isPending ? (
                  <span className="inline-flex items-center gap-2">
                    <Skeleton className="h-4 w-4 rounded-full" />
                    Saving plan...
                  </span>
                ) : (
                  <>
                    Save &amp; email plan
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
                    <p className="text-xs text-emerald-100/70">
                      {emailSent
                        ? 'We’ve emailed the ICS file to Gmail and you can download it anytime.'
                        : 'Download the ICS file or keep refining your milestones.'}
                    </p>
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
