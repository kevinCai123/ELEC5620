import { useState } from 'react';
import { motion } from 'framer-motion';
import { useMutation } from '@tanstack/react-query';
import ReactMarkdown from 'react-markdown';
import { ClipboardCheck, ClipboardList, Sparkles, Wand2 } from 'lucide-react';

import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Input } from '../../components/ui/input';
import { Skeleton } from '../../components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Textarea } from '../../components/ui/textarea';
import { apiClient } from '../../api/client';

type SummarySection = {
  heading: string;
  bullets: string[];
};

type SummaryQnA = {
  q: string;
  a_hint: string;
};

type SummaryNote = {
  tldr: string;
  sections: SummarySection[];
  qna_seeds: SummaryQnA[];
};

type SummarizeResponse = {
  summary: SummaryNote;
  truncated: boolean;
};

type ApiResult<T> = { data?: T; error?: { detail?: string } };

type ActiveTab = 'text' | 'url';

export function SummarizePage() {
  const [text, setText] = useState('');
  const [url, setUrl] = useState('');
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState<ActiveTab>('text');

  const mutation = useMutation({
    mutationFn: async () => {
      const response = (await apiClient.POST('/study/summarize', {
        body: { text: text || undefined, url: url || undefined, user_request: null },
      })) as ApiResult<SummarizeResponse>;
      if (response.error) {
        throw new Error(response.error.detail ?? 'Failed to summarise content');
      }
      return response.data as SummarizeResponse;
    },
    onSuccess: () => setCopied(false),
  });

  const summaryMarkdown = mutation.data
    ? (() => {
        const note: SummaryNote = mutation.data.summary;
        const sectionBlocks = note.sections.map((section) => {
          const bullets = section.bullets.map((bullet) => `- ${bullet}`);
          return [`### ${section.heading}`, ...bullets].join('\n');
        });
        // Q&A Seeds removed from display
        return ['**TL;DR**', '', note.tldr, '', ...sectionBlocks].join('\n');
      })()
    : '';

  const copyToClipboard = async () => {
    if (!summaryMarkdown) return;
    await navigator.clipboard.writeText(summaryMarkdown);
    setCopied(true);
  };

  const isLoading = mutation.isPending;
  const hasResult = Boolean(summaryMarkdown);

  return (
    <section className="grid min-w-0 gap-6 lg:grid-cols-2">
      <Card className="min-w-0 border-foreground/12 bg-foreground/[0.08]">
        <CardHeader className="space-y-3">
          <Badge variant="glow">AI note maker</Badge>
          <CardTitle className="flex items-center gap-3 text-2xl">
            <Wand2 className="h-6 w-6 text-primary" />
            Summarise research or lecture notes in seconds
          </CardTitle>
          <CardDescription>
            Paste raw content or drop a URL up to 5k tokens. We generate a crisp TL;DR, organised sections, and revision-ready
            question prompts.
          </CardDescription>
        </CardHeader>
        <CardContent className="min-w-0 space-y-6">
          <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as ActiveTab)}>
            <TabsList className="mb-2">
              <TabsTrigger value="text">Raw text</TabsTrigger>
              <TabsTrigger value="url">Source URL</TabsTrigger>
            </TabsList>
            <TabsContent value="text" className="min-w-0 space-y-3">
              <label className="text-xs uppercase tracking-[0.28em] text-foreground/50">Paste content</label>
              <Textarea
                value={text}
                onChange={(event) => setText(event.target.value)}
                placeholder="Paste any study material or meeting notes..."
                className="min-h-[260px] w-full max-w-[calc(100%-50px)]"
              />
            </TabsContent>
            <TabsContent value="url" className="min-w-0 space-y-3">
              <label className="text-xs uppercase tracking-[0.28em] text-foreground/50">Public URL</label>
              <Input
                value={url}
                onChange={(event) => setUrl(event.target.value)}
                placeholder="https://example.com/article"
                className="w-full max-w-md"
              />
              <p className="text-xs text-foreground/45">We&apos;ll fetch the readable content from the page for you.</p>
            </TabsContent>
          </Tabs>

          <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
            <Button
              type="button"
              onClick={() => mutation.mutate()}
              disabled={isLoading || (!text && !url)}
            >
              {isLoading ? (
                <span className="inline-flex items-center gap-2">
                  <Skeleton className="h-4 w-4 rounded-full" />
                  Summarising...
                </span>
              ) : (
                <>
                  Summarise
                  <Sparkles className="h-4 w-4" />
                </>
              )}
            </Button>
            <Button type="button" variant="ghost" glow={false} onClick={copyToClipboard} disabled={!summaryMarkdown}>
              {copied ? (
                <>
                  Copied!
                  <ClipboardCheck className="h-4 w-4" />
                </>
              ) : (
                <>
                  Copy to notes
                  <ClipboardList className="h-4 w-4" />
                </>
              )}
            </Button>
          </div>

          {mutation.isError && (
            <p className="rounded-xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
              {(mutation.error as Error).message}
            </p>
          )}
          {mutation.data?.truncated && (
            <p className="rounded-xl border border-amber-400/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
              Input truncated to the first 5k tokens.
            </p>
          )}
        </CardContent>
      </Card>

      <Card className="flex min-h-[420px] min-w-0 flex-col border-foreground/12 bg-foreground/[0.08]">
        <CardHeader className="space-y-2">
          <CardTitle className="flex items-center gap-3 text-2xl">
            <Sparkles className="h-5 w-5 text-primary" />
            Structured notes
          </CardTitle>
          <CardDescription>
            TL;DR, bullet sections, and question prompts ready to paste into your personal notes.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex min-h-0 flex-1 flex-col gap-4">
          <div className="relative flex min-h-[320px] flex-1 flex-col overflow-hidden rounded-2xl border border-foreground/10 bg-background/40 p-6">
            {!hasResult && !isLoading && (
              <div className="flex h-full flex-col items-center justify-center gap-4 text-center text-foreground/60">
                <Sparkles className="h-10 w-10 text-primary" />
                <p className="max-w-sm text-sm">
                  Run a summarisation to see TL;DR, structured sections, and suggested Q&A prompts appear here.
                </p>
              </div>
            )}

            {isLoading && (
              <div className="space-y-4">
                {Array.from({ length: 4 }).map((_, idx) => (
                  <Skeleton key={idx} className="h-5 w-full rounded-xl" />
                ))}
              </div>
            )}

            {hasResult && !isLoading && (
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                className="prose prose-invert prose-sm max-w-none flex-1 overflow-y-auto overscroll-contain break-words text-foreground/80"
              >
                <ReactMarkdown>{summaryMarkdown}</ReactMarkdown>
              </motion.div>
            )}
          </div>
        </CardContent>
      </Card>
    </section>
  );
}
