import { Moon, Sun } from 'lucide-react';
import { useEffect, useState } from 'react';

import { Button } from '../ui/button';
import { useTheme } from '../../providers/ThemeProvider';

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <Button variant="ghost" size="icon" aria-label="Toggle theme" glow={false} disabled>
        <Sun className="h-4 w-4" />
      </Button>
    );
  }

  return (
    <Button variant="ghost" size="icon" aria-label="Toggle theme" glow={false} onClick={toggleTheme}>
      {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
    </Button>
  );
}
