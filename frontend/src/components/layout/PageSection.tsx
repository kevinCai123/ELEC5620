import * as React from 'react';

import { cn } from '../../lib/utils';

type PageSectionProps = React.HTMLAttributes<HTMLDivElement>;

export function PageSection({ className, ...props }: PageSectionProps) {
  return <div className={cn('mx-auto w-full max-w-[1350px] px-3 sm:px-5 lg:px-6 xl:px-8', className)} {...props} />;
}
