import { useState } from 'react';
import { motion } from 'framer-motion';
import { useMutation } from '@tanstack/react-query';
import { Code2, Sparkles, Copy, CheckCircle2 } from 'lucide-react';

import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Textarea } from '../../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { apiClient } from '../../api/client';

type CodeGenerationResponse = {
  code: string;
  language: string;
  explanation: string;
  fallback_used: boolean;
};

type ApiResult<T> = { data?: T; error?: { detail?: string } };

const LANGUAGES = [
  { value: 'python', label: 'Python' },
  { value: 'javascript', label: 'JavaScript' },
  { value: 'typescript', label: 'TypeScript' },
];

export function CodeGenerationPage() {
  const [prompt, setPrompt] = useState('');
  const [language, setLanguage] = useState('python');
  const [copied, setCopied] = useState(false);

  const mutation = useMutation({
    mutationFn: async () => {
      // @ts-expect-error - API endpoint exists but not in generated types
      const response = (await apiClient.POST('/code/generate', {
        body: { prompt, language },
      })) as ApiResult<CodeGenerationResponse>;
      if (response.error) {
        throw new Error(response.error.detail ?? 'Failed to generate code');
      }
      return response.data as CodeGenerationResponse;
    },
    onSuccess: () => setCopied(false),
  });

  const copyToClipboard = async () => {
    if (!mutation.data) return;
    await navigator.clipboard.writeText(mutation.data.code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section className="grid min-w-0 gap-6 lg:grid-cols-2">
      <Card className="min-w-0 border-foreground/12 bg-foreground/[0.08]">
        <CardHeader className="space-y-3">
          <Badge variant="glow">AI code generator</Badge>
          <CardTitle className="flex items-center gap-3 text-2xl">
            <Code2 className="h-6 w-6 text-primary" />
            Generate code from description
          </CardTitle>
          <CardDescription>
            Describe what you want in plain English, and AI will generate clean, working code for you.
          </CardDescription>
        </CardHeader>
        <CardContent className="min-w-0 space-y-6">
          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.28em] text-foreground/50">Programming Language</label>
            <Select value={language} onValueChange={setLanguage}>
              <SelectTrigger className="w-full max-w-md">
                <SelectValue placeholder="Select language..." />
              </SelectTrigger>
              <SelectContent>
                {LANGUAGES.map((lang) => (
                  <SelectItem key={lang.value} value={lang.value}>
                    {lang.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

            <div className="space-y-2">
              <label className="text-xs uppercase tracking-[0.28em] text-foreground/50">
                What do you want to code?
              </label>
              <Textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="e.g., A function to calculate fibonacci numbers recursively"
                className="min-h-[200px] w-full max-w-[calc(100%-50px)]"
              />
            </div>

          <Button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending || !prompt || !language}
            className="w-full"
          >
            {mutation.isPending ? (
              <span className="inline-flex items-center gap-2">
                Generating
                <Sparkles className="h-4 w-4 animate-pulse" />
              </span>
            ) : (
              <>
                Generate Code
                <Sparkles className="h-4 w-4" />
              </>
            )}
          </Button>

          {mutation.isError && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-100"
            >
              {(mutation.error as Error).message}
            </motion.div>
          )}

          {mutation.data?.fallback_used && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-xl border border-amber-400/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-100"
            >
              ⚠️ LLM unavailable. Showing example code.
            </motion.div>
          )}
        </CardContent>
      </Card>

      {mutation.data && (
        <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="min-w-0 space-y-4">
          <Card className="min-w-0 border-foreground/12 bg-foreground/[0.08]">
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
              <CardTitle className="text-lg">Generated Code</CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={copyToClipboard}
                className="flex items-center gap-2"
              >
                {copied ? (
                  <>
                    <CheckCircle2 className="h-4 w-4" />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy className="h-4 w-4" />
                    Copy
                  </>
                )}
              </Button>
            </CardHeader>
            <CardContent className="min-w-0">
              <div className="rounded-2xl border border-foreground/10 bg-black/40 p-4">
                <pre className="overflow-x-auto text-sm">
                  <code className="text-foreground/90">{mutation.data.code}</code>
                </pre>
              </div>
            </CardContent>
          </Card>

          {mutation.data.explanation && (
            <Card className="border-foreground/12 bg-foreground/[0.08]">
              <CardHeader>
                <CardTitle className="text-lg">Explanation</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-foreground/75">{mutation.data.explanation}</p>
              </CardContent>
            </Card>
          )}
        </motion.div>
      )}
    </section>
  );
}

