import { useState } from 'react';
import { motion } from 'framer-motion';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Mail, MailSearch, RefreshCw, Send } from 'lucide-react';

import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Input } from '../../components/ui/input';
import { Skeleton } from '../../components/ui/skeleton';
import { apiClient } from '../../api/client';
import { formatDateTime } from '../../lib/utils';

type DigestSection = {
  heading: string;
  items: string[];
};

type DigestPreview = {
  generated_at: string;
  sections: DigestSection[];
};

type EmailResponse = {
  success: boolean;
  message: string;
};

type ApiResult<T> = { data?: T; error?: { detail?: string } };

export function DigestPreviewPage() {
  const [email, setEmail] = useState('');
  const [showEmailInput, setShowEmailInput] = useState(false);

  const query = useQuery({
    queryKey: ['digest', 'preview'],
    queryFn: async () => {
      const response = (await apiClient.GET('/digest/preview', {})) as ApiResult<DigestPreview>;
      if (response.error) {
        throw new Error(response.error.detail ?? 'No digest available');
      }
      return response.data as DigestPreview;
    },
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    refetchOnWindowFocus: false,
  });

  const emailMutation = useMutation({
    mutationFn: async (recipientEmail: string) => {
      const response = (await apiClient.POST('/digest/send' as never, {
        body: {
          recipient_email: recipientEmail,
        },
      })) as ApiResult<EmailResponse>;
      if (response.error) {
        throw new Error(response.error.detail ?? 'Failed to send email');
      }
      return response.data as EmailResponse;
    },
    onSuccess: () => {
      setEmail('');
      setShowEmailInput(false);
    },
  });

  const handleRefresh = async () => {
    console.log('?? Digest refresh button clicked');
    await query.refetch();
    console.log('? Digest refresh complete');
  };

  const handleSendEmail = () => {
    if (email.trim()) {
      emailMutation.mutate(email.trim());
    }
  };

  if (query.isLoading) {
    return (
      <Card className="border-foreground/12 bg-foreground/[0.08]">
        <CardContent className="space-y-3">
          {Array.from({ length: 3 }).map((_, idx) => (
            <Skeleton key={idx} className="h-5 w-full rounded-xl" />
          ))}
        </CardContent>
      </Card>
    );
  }

  if (query.error) {
    return (
      <Card className="border-amber-400/30 bg-amber-500/10">
        <CardContent className="text-sm text-amber-100">{(query.error as Error).message}</CardContent>
      </Card>
    );
  }

  if (!query.data) {
    return (
      <Card className="border-foreground/12 bg-foreground/[0.08]">
        <CardContent className="text-sm text-foreground/70">No digest generated yet.</CardContent>
      </Card>
    );
  }

  return (
    <section className="space-y-8">
      <div className="flex items-end justify-between gap-6">
        <Card className="flex-1 border-foreground/12 bg-foreground/[0.08]">
          <CardHeader className="space-y-3">
            <Badge variant="glow">AI Digest</Badge>
            <CardTitle className="flex items-center gap-3 text-2xl">
              <MailSearch className="h-6 w-6 text-primary" />
              Email Digest (18 Recent Emails)
            </CardTitle>
            <CardDescription>
              AI-powered comprehensive summary � Generated at {formatDateTime(query.data.generated_at)}
            </CardDescription>
          </CardHeader>
        </Card>
        <div className="flex gap-2">
          <Button variant="ghost" glow={false} onClick={() => setShowEmailInput(!showEmailInput)}>
            Email
            <Mail className="h-4 w-4" />
          </Button>
          <Button variant="ghost" glow={false} onClick={handleRefresh} disabled={query.isPending || query.isFetching}>
            {query.isFetching ? 'Refreshing...' : 'Refresh'}
            <RefreshCw className={`h-4 w-4 ${query.isFetching ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      {/* Email Input Section */}
      {showEmailInput && (
        <Card className="border-foreground/12 bg-foreground/[0.08]">
          <CardContent className="pt-6">
            <div className="space-y-4">
              <div className="flex flex-col gap-3 sm:flex-row">
                <Input
                  type="email"
                  placeholder="Enter your email address"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSendEmail()}
                  className="flex-1"
                  disabled={emailMutation.isPending}
                />
                <div className="flex gap-2">
                  <Button
                    onClick={handleSendEmail}
                    disabled={emailMutation.isPending || !email.trim()}
                    className="gap-2"
                  >
                    {emailMutation.isPending ? (
                      <>Sending...</>
                    ) : (
                      <>
                        <Send className="h-4 w-4" />
                        Send
                      </>
                    )}
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={() => {
                      setShowEmailInput(false);
                      setEmail('');
                    }}
                    disabled={emailMutation.isPending}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
              {emailMutation.isError && (
                <p className="rounded-xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
                  {(emailMutation.error as Error).message}
                </p>
              )}
              {emailMutation.isSuccess && (
                <motion.p
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="rounded-xl border border-emerald-400/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-100"
                >
                  ? {emailMutation.data?.message || 'Digest sent successfully!'}
                </motion.p>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="space-y-4">
        {query.data.sections.map((section, sectionIndex) => (
          <motion.div
            key={section.heading}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: sectionIndex * 0.04 }}
          >
            <Card className="border-foreground/12 bg-foreground/[0.08]">
              <CardHeader>
                <CardTitle className="text-lg text-foreground">{section.heading}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm text-foreground/75">
                {section.items.map((item, idx) => (
                  <div
                    key={`${section.heading}-${idx}`}
                    className="rounded-2xl border border-foreground/10 bg-foreground/[0.06] px-4 py-3"
                  >
                    {item}
                  </div>
                ))}
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
