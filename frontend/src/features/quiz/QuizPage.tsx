import { useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { useMutation } from '@tanstack/react-query';
import { ChevronDown, GraduationCap, PartyPopper, Sparkles } from 'lucide-react';

import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Input } from '../../components/ui/input';
import { Textarea } from '../../components/ui/textarea';
import { apiClient } from '../../api/client';

type QuizItem = {
  stem: string;
  options: string[];
  answer_index: number;
  rationale: string;
  generated_from?: string;
};

type QuizResponse = {
  items: QuizItem[];
  duplicate_stem_rate: number;
  fallback_used: boolean;
};

type ApiResult<T> = { data?: T; error?: { detail?: string } };

export function QuizPage() {
  const [notes, setNotes] = useState('');
  const [topic, setTopic] = useState('');
  const [openRationaleIndex, setOpenRationaleIndex] = useState<number | null>(null);
  const mutation = useMutation({
    mutationFn: async () => {
      const response = (await apiClient.POST('/study/quiz', { body: { notes, topic: topic || undefined } })) as ApiResult<QuizResponse>;
      if (response.error) {
        throw new Error(response.error.detail ?? 'Failed to generate quiz');
      }
      return response.data as QuizResponse;
    },
  });

  const duplicateRate = useMemo(() => {
    if (!mutation.data) return null;
    return `${(mutation.data.duplicate_stem_rate * 100).toFixed(0)}%`;
  }, [mutation.data]);

  return (
    <section className="min-w-0 space-y-8">
      <Card className="min-w-0 border-white/12 bg-white/8">
        <CardHeader className="space-y-3">
          <Badge variant="glow">Quiz generator</Badge>
          <CardTitle className="flex items-center gap-3 text-2xl">
            <GraduationCap className="h-6 w-6 text-primary" />
            Instant practice questions
          </CardTitle>
          <CardDescription>
            Paste your notes and generate five focused multiple-choice questions, complete with rationales and difficulty cues.
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
                <label className="text-xs uppercase tracking-[0.28em] text-foreground/50">Topic focus (optional)</label>
                <Input
                  value={topic}
                  onChange={(event) => setTopic(event.target.value)}
                  placeholder="e.g. Neural networks"
                  className="w-full max-w-md"
                />
              </div>
              <div className="min-w-0 space-y-2">
                <label className="text-xs uppercase tracking-[0.28em] text-foreground/50">Notes</label>
                <Textarea
                  value={notes}
                  onChange={(event) => setNotes(event.target.value)}
                  placeholder="Paste lecture notes, meeting highlights, or reading summaries..."
                  className="min-h-[240px] w-full max-w-full"
                  required
                />
              </div>
            </div>
            <Button type="submit" disabled={mutation.isPending || !notes}>
              {mutation.isPending ? (
                <span className="inline-flex items-center gap-2">
                  Generating
                  <Sparkles className="h-4 w-4 animate-pulse" />
                </span>
              ) : (
                <>
                  Generate quiz
                  <Sparkles className="h-4 w-4" />
                </>
              )}
            </Button>
            {mutation.isError && (
              <p className="rounded-xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
                {(mutation.error as Error).message}
              </p>
            )}
            {mutation.data && (
              <div className="rounded-2xl border border-cyan-400/30 bg-cyan-500/10 px-4 py-3 text-sm text-cyan-100">
                Duplicate stem rate: {duplicateRate}.{' '}
                {mutation.data.fallback_used ? 'Template questions filled the gaps.' : 'All items generated fresh.'}
              </div>
            )}
          </form>
        </CardContent>
      </Card>

      {mutation.data && (
        <div className="space-y-6">
          {mutation.data.items.map((item, index) => {
            const isOpen = openRationaleIndex === index;
            return (
              <motion.div
                key={`${item.stem}-${index}`}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1], delay: index * 0.03 }}
                className="relative min-w-0 overflow-hidden rounded-3xl border border-white/12 bg-white/8 p-6 shadow-glow-md"
              >
                <div className="absolute inset-x-[-20%] -top-32 h-64 rounded-full bg-aurora/30 blur-[120px]" />
                <div className="relative space-y-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="space-y-2">
                      <Badge variant="outline" className="text-xs text-foreground/60">
                        Question {index + 1}
                      </Badge>
                      <h2 className="text-lg font-semibold text-foreground break-words">{item.stem}</h2>
                      {item.generated_from === 'template' && <Badge variant="warning">Template</Badge>}
                    </div>
                    <PartyPopper className="h-6 w-6 text-primary" />
                  </div>
                  <div className="space-y-2">
                    {item.options.map((option, optionIndex) => {
                      const isCorrect = optionIndex === item.answer_index;
                      return (
                        <motion.div
                          key={optionIndex}
                          whileHover={{ y: -2, scale: 1.01 }}
                          className={`flex items-center gap-3 rounded-2xl border px-4 py-3 text-sm transition duration-200 ${
                            isCorrect
                              ? 'border-emerald-400/50 bg-emerald-500/10 text-emerald-100'
                              : 'border-white/10 bg-white/4 text-foreground/80'
                          }`}
                        >
                          <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border border-white/10 bg-white/10 text-xs font-semibold uppercase tracking-[0.18em]">
                            {String.fromCharCode(65 + optionIndex)}
                          </span>
                          <span className="min-w-0 flex-1 break-words">{option}</span>
                          {isCorrect && <Badge variant="success">Correct</Badge>}
                        </motion.div>
                      );
                    })}
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    glow={false}
                    onClick={() => setOpenRationaleIndex(isOpen ? null : index)}
                    className="inline-flex items-center gap-2 rounded-lg text-sm text-foreground/70"
                  >
                    View rationale
                    <ChevronDown className={`h-4 w-4 transition ${isOpen ? 'rotate-180' : ''}`} />
                  </Button>
                  {isOpen && (
                    <motion.p
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="rounded-2xl border border-white/10 bg-white/6 px-4 py-3 text-sm text-foreground/75 whitespace-pre-wrap break-words"
                    >
                      {item.rationale}
                    </motion.p>
                  )}
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </section>
  );
}

