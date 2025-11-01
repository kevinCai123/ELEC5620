import { useState } from 'react';
import { motion } from 'framer-motion';
import { useMutation } from '@tanstack/react-query';
import { Play, Terminal, AlertCircle, CheckCircle2, Clock, Sparkles } from 'lucide-react';

import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Textarea } from '../../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Input } from '../../components/ui/input';
import { apiClient } from '../../api/client';

type CodeAnalysis = {
  safety_score: number;
  potential_issues: string[];
  predicted_output: string;
  should_execute: boolean;
};

type OutputAnalysis = {
  summary: string;
  insights: string[];
  suggestions: string[];
};

type CodeExecutionResponse = {
  pre_analysis: CodeAnalysis;
  output: string;
  error: string | null;
  execution_time: number;
  success: boolean;
  post_analysis: OutputAnalysis;
  fallback_used: boolean;
};

type ApiResult<T> = { data?: T; error?: { detail?: string } };

const LANGUAGES = [
  { value: 'python', label: 'Python' },
  { value: 'javascript', label: 'JavaScript' },
];

const EXAMPLES = {
  python: `# Example: Print Fibonacci sequence
def fibonacci(n):
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    
    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    return fib

result = fibonacci(10)
print("Fibonacci sequence:", result)`,
  javascript: `// Example: Print Fibonacci sequence
function fibonacci(n) {
    if (n <= 0) return [];
    if (n === 1) return [0];
    if (n === 2) return [0, 1];
    
    const fib = [0, 1];
    for (let i = 2; i < n; i++) {
        fib.push(fib[i-1] + fib[i-2]);
    }
    return fib;
}

const result = fibonacci(10);
console.log("Fibonacci sequence:", result);`,
};

export function CodeSandboxPage() {
  const [code, setCode] = useState(EXAMPLES.python);
  const [language, setLanguage] = useState('python');
  const [timeout, setTimeout] = useState(5);

  const mutation = useMutation({
    mutationFn: async () => {
      // @ts-expect-error - API endpoint exists but not in generated types
      const response = (await apiClient.POST('/code/execute', {
        body: { code, language, timeout },
      })) as ApiResult<CodeExecutionResponse>;
      if (response.error) {
        throw new Error(response.error.detail ?? 'Failed to execute code');
      }
      return response.data as CodeExecutionResponse;
    },
  });

  const handleLanguageChange = (newLanguage: string) => {
    setLanguage(newLanguage);
    // Load example for the new language
    if (newLanguage === 'python') {
      setCode(EXAMPLES.python);
    } else if (newLanguage === 'javascript') {
      setCode(EXAMPLES.javascript);
    }
  };

  return (
    <section className="min-w-0 space-y-6">
      <Card className="min-w-0 border-foreground/12 bg-foreground/[0.08]">
        <CardHeader className="space-y-3">
          <Badge variant="glow">Code sandbox</Badge>
          <CardTitle className="flex items-center gap-3 text-2xl">
            <Terminal className="h-6 w-6 text-primary" />
            Execute code safely
          </CardTitle>
          <CardDescription>
            Write and run code in a safe sandboxed environment. Perfect for testing snippets and learning.
          </CardDescription>
        </CardHeader>
        <CardContent className="min-w-0 space-y-6">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <label className="text-xs uppercase tracking-[0.28em] text-foreground/50">Language</label>
              <Select value={language} onValueChange={handleLanguageChange}>
                <SelectTrigger className="w-full">
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
              <label className="text-xs uppercase tracking-[0.28em] text-foreground/50">Timeout (seconds)</label>
              <Input
                type="number"
                min={1}
                max={30}
                value={timeout}
                onChange={(e) => setTimeout(Number(e.target.value))}
                className="w-full max-w-[calc(100%-50px)]"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.28em] text-foreground/50">Code</label>
            <div className="rounded-2xl border border-foreground/10 bg-black/40">
              <Textarea
                value={code}
                onChange={(e) => setCode(e.target.value)}
                className="min-h-[300px] w-full max-w-[calc(100%-50px)] border-0 bg-transparent font-mono text-sm"
                style={{ resize: 'vertical' }}
              />
            </div>
          </div>

          <Button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending || !code}
            className="w-full sm:w-auto"
          >
            {mutation.isPending ? (
              <span className="inline-flex items-center gap-2">
                Running
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-foreground/20 border-t-white"></div>
              </span>
            ) : (
              <>
                Run Code
                <Play className="h-4 w-4" />
              </>
            )}
          </Button>

          {mutation.isError && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-100"
            >
              <div className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4" />
                {(mutation.error as Error).message}
              </div>
            </motion.div>
          )}
        </CardContent>
      </Card>

      {mutation.data && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
          {/* LLM fallback warning */}
          {mutation.data.fallback_used && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-xl border border-amber-400/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-100"
            >
              ⚠️ LLM unavailable. Analysis limited.
            </motion.div>
          )}

          {/* Pre-execution Analysis */}
          <Card className="min-w-0 border-foreground/12 bg-foreground/[0.08]">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Sparkles className="h-5 w-5 text-primary" />
                AI Safety Analysis
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-foreground/60">Safety Score</span>
                <div className="flex items-center gap-2">
                  <div className="h-2 w-32 overflow-hidden rounded-full bg-foreground/10">
                    <div
                      className={`h-full transition-all ${
                        mutation.data.pre_analysis.safety_score >= 7
                          ? 'bg-emerald-500'
                          : mutation.data.pre_analysis.safety_score >= 4
                            ? 'bg-amber-500'
                            : 'bg-red-500'
                      }`}
                      style={{ width: `${mutation.data.pre_analysis.safety_score * 10}%` }}
                    />
                  </div>
                  <span className="text-sm font-semibold">
                    {mutation.data.pre_analysis.safety_score}/10
                  </span>
                </div>
              </div>

              {mutation.data.pre_analysis.potential_issues.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs font-semibold uppercase tracking-wider text-foreground/50">
                    Potential Issues
                  </p>
                  <ul className="space-y-1">
                    {mutation.data.pre_analysis.potential_issues.map((issue, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm text-foreground/70">
                        <span className="mt-1 text-amber-400">▸</span>
                        <span>{issue}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="space-y-2">
                <p className="text-xs font-semibold uppercase tracking-wider text-foreground/50">
                  Predicted Output
                </p>
                <div className="rounded-xl border border-foreground/10 bg-black/40 p-3">
                  <pre className="overflow-x-auto text-sm text-foreground/80">
                    <code>{mutation.data.pre_analysis.predicted_output}</code>
                  </pre>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Execution Output */}
          <Card className="min-w-0 border-foreground/12 bg-foreground/[0.08]">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Terminal className="h-5 w-5" />
                  Execution Output
                </CardTitle>
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2 text-xs text-foreground/60">
                    <Clock className="h-3 w-3" />
                    {mutation.data.execution_time.toFixed(3)}s
                  </div>
                  {mutation.data.success ? (
                    <Badge variant="success" className="flex items-center gap-1">
                      <CheckCircle2 className="h-3 w-3" />
                      Success
                    </Badge>
                  ) : (
                    <Badge className="flex items-center gap-1 bg-red-500/90 text-white">
                      <AlertCircle className="h-3 w-3" />
                      Error
                    </Badge>
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent className="min-w-0">
              {mutation.data.error ? (
                <div className="space-y-4">
                  <div className="rounded-2xl border border-red-400/30 bg-red-500/10 p-4">
                    <div className="flex items-start gap-2">
                      <AlertCircle className="mt-0.5 h-4 w-4 text-red-300" />
                      <div>
                        <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-red-300">Error</p>
                        <pre className="overflow-x-auto text-sm text-red-100">
                          <code>{mutation.data.error}</code>
                        </pre>
                      </div>
                    </div>
                  </div>
                  {mutation.data.output && (
                    <div className="rounded-2xl border border-foreground/10 bg-black/40 p-4">
                      <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-foreground/50">
                        Stdout
                      </p>
                      <pre className="overflow-x-auto text-sm text-foreground/90">
                        <code>{mutation.data.output}</code>
                      </pre>
                    </div>
                  )}
                </div>
              ) : (
                <div className="rounded-2xl border border-emerald-400/30 bg-emerald-500/10 p-4">
                  <pre className="overflow-x-auto text-sm text-emerald-100">
                    <code>{mutation.data.output || '(no output)'}</code>
                  </pre>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Post-execution Analysis */}
          <Card className="min-w-0 border-foreground/12 bg-foreground/[0.08]">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Sparkles className="h-5 w-5 text-primary" />
                AI Insights
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <p className="text-xs font-semibold uppercase tracking-wider text-foreground/50">Summary</p>
                <p className="text-sm text-foreground/80">{mutation.data.post_analysis.summary}</p>
              </div>

              {mutation.data.post_analysis.insights.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs font-semibold uppercase tracking-wider text-foreground/50">Key Insights</p>
                  <ul className="space-y-1.5">
                    {mutation.data.post_analysis.insights.map((insight, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm text-foreground/75">
                        <span className="mt-1 text-primary">●</span>
                        <span>{insight}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {mutation.data.post_analysis.suggestions.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs font-semibold uppercase tracking-wider text-foreground/50">Suggestions</p>
                  <ul className="space-y-1.5">
                    {mutation.data.post_analysis.suggestions.map((suggestion, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm text-emerald-300/80">
                        <span className="mt-1">→</span>
                        <span>{suggestion}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      )}
    </section>
  );
}

