/*
================================================================================
USAGE EXAMPLES
================================================================================

import Card from '@/components/ui/Card';

// Basic card
<Card>
  <h3>Card Title</h3>
  <p>Card content goes here</p>
</Card>

// Without hover effect
<Card hover={false}>
  <p>Static card</p>
</Card>

// With padding variants
<Card padding="none">
  <img src="cover.jpg" className="w-full" />
</Card>

<Card padding="sm">
  <p>Compact card</p>
</Card>

<Card padding="lg">
  <p>Spacious card</p>
</Card>

// Clickable card (as button)
<Card onClick={() => navigate('/project/1')} className="cursor-pointer">
  <h3>Project Name</h3>
</Card>

// Project card example
<Card>
  <div className="flex justify-between items-start">
    <div>
      <h3 className="font-semibold text-gray-900">My Ebook</h3>
      <p className="text-sm text-gray-500">Last edited 2 hours ago</p>
    </div>
    <Badge variant="draft">Draft</Badge>
  </div>
</Card>

================================================================================
*/

export default function Card({
  children,
  hover = true,
  padding = 'md',
  className = '',
  onClick,
  ...props
}) {
  const baseStyles = 'bg-white rounded-xl border border-gray-200 shadow-sm';

  const hoverStyles = hover
    ? 'transition-shadow duration-200 hover:shadow-md'
    : '';

  const paddingStyles = {
    none: '',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  };

  const clickableStyles = onClick ? 'cursor-pointer' : '';

  return (
    <div
      onClick={onClick}
      className={`${baseStyles} ${hoverStyles} ${paddingStyles[padding]} ${clickableStyles} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}
