import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { MailSearch } from 'lucide-react';

import { Badge } from '../../components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
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

type ApiResult<T> = { data?: T; error?: { detail?: string } };

export function DigestPreviewPage() {
  const query = useQuery({
    queryKey: ['digest', 'preview'],
    queryFn: async () => {
      const response = (await apiClient.GET('/digest/preview', {})) as ApiResult<DigestPreview>;
      if (response.error) {
        throw new Error(response.error.detail ?? 'No digest available');
      }
      return response.data as DigestPreview;
    },
  });

  if (query.isLoading) {
    return (
      <Card className="border-white/12 bg-white/8">
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
      <Card className="border-white/12 bg-white/8">
        <CardContent className="text-sm text-foreground/70">No digest generated yet.</CardContent>
      </Card>
    );
  }

  return (
    <section className="space-y-8">
      <Card className="border-white/12 bg-white/8">
        <CardHeader className="space-y-3">
          <Badge variant="glow">Digest</Badge>
          <CardTitle className="flex items-center gap-3 text-2xl">
            <MailSearch className="h-6 w-6 text-primary" />
            Morning digest preview
          </CardTitle>
          <CardDescription>Generated at {formatDateTime(query.data.generated_at)}</CardDescription>
        </CardHeader>
      </Card>

      <div className="space-y-4">
        {query.data.sections.map((section, sectionIndex) => (
          <motion.div
            key={section.heading}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: sectionIndex * 0.04 }}
          >
            <Card className="border-white/12 bg-white/8">
              <CardHeader>
                <CardTitle className="text-lg text-foreground">{section.heading}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm text-foreground/75">
                {section.items.map((item, idx) => (
                  <div
                    key={`${section.heading}-${idx}`}
                    className="rounded-2xl border border-white/10 bg-white/6 px-4 py-3"
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
