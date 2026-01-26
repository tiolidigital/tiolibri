/*
================================================================================
USAGE EXAMPLES
================================================================================

import Badge from '@/components/ui/Badge';

// Status badges (for projects)
<Badge variant="draft">Draft</Badge>
<Badge variant="in_progress">In Progress</Badge>
<Badge variant="completed">Completed</Badge>

// Generic badges
<Badge variant="gray">Default</Badge>
<Badge variant="blue">Info</Badge>
<Badge variant="green">Success</Badge>
<Badge variant="yellow">Warning</Badge>
<Badge variant="red">Error</Badge>

// Size variants
<Badge size="sm" variant="draft">Small</Badge>
<Badge size="md" variant="draft">Medium (default)</Badge>

// In a card header
<div className="flex justify-between items-center">
  <h3 className="font-semibold">My Project</h3>
  <Badge variant="in_progress">In Progress</Badge>
</div>

// Multiple badges
<div className="flex gap-2">
  <Badge variant="blue">EPUB</Badge>
  <Badge variant="blue">PDF</Badge>
</div>

================================================================================
*/

export default function Badge({
  children,
  variant = 'gray',
  size = 'md',
  className = '',
  ...props
}) {
  const baseStyles = 'inline-flex items-center font-medium rounded-full';

  const variants = {
    // Project status variants
    draft: 'bg-gray-100 text-gray-700',
    in_progress: 'bg-blue-100 text-blue-700',
    completed: 'bg-green-100 text-green-700',
    // Generic color variants
    gray: 'bg-gray-100 text-gray-700',
    blue: 'bg-blue-100 text-blue-700',
    green: 'bg-green-100 text-green-700',
    yellow: 'bg-yellow-100 text-yellow-800',
    red: 'bg-red-100 text-red-700',
    indigo: 'bg-indigo-100 text-indigo-700',
  };

  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-xs',
  };

  return (
    <span
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {children}
    </span>
  );
}
