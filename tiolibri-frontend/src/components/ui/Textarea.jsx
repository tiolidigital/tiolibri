/*
================================================================================
USAGE EXAMPLES
================================================================================

import Textarea from '@/components/ui/Textarea';

// Basic
<Textarea placeholder="Enter description..." />

// Controlled
const [description, setDescription] = useState('');
<Textarea
  value={description}
  onChange={(e) => setDescription(e.target.value)}
  placeholder="Book description..."
/>

// With label
<div>
  <label className="block text-sm font-medium text-gray-700 mb-1">
    Description
  </label>
  <Textarea placeholder="Enter book description..." rows={6} />
</div>

// Custom rows
<Textarea rows={8} placeholder="Long content..." />

// With error
<Textarea
  value={description}
  onChange={(e) => setDescription(e.target.value)}
  error="Description is required"
/>

// Disabled
<Textarea disabled value="Cannot edit this content" />

// With character count (wrap in div)
<div>
  <Textarea
    value={text}
    onChange={(e) => setText(e.target.value)}
    maxLength={500}
  />
  <p className="mt-1 text-sm text-gray-500 text-right">
    {text.length}/500
  </p>
</div>

================================================================================
*/

import { forwardRef } from 'react';

const Textarea = forwardRef(function Textarea(
  {
    placeholder,
    value,
    onChange,
    rows = 4,
    disabled = false,
    error,
    className = '',
    ...props
  },
  ref
) {
  const baseStyles =
    'block w-full px-3 py-2 border rounded-lg text-gray-900 placeholder-gray-400 transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-offset-0 disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed resize-y';

  const normalStyles =
    'border-gray-300 focus:border-indigo-500 focus:ring-indigo-500';

  const errorStyles =
    'border-red-500 focus:border-red-500 focus:ring-red-500';

  return (
    <div className="w-full">
      <textarea
        ref={ref}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        rows={rows}
        disabled={disabled}
        className={`${baseStyles} ${error ? errorStyles : normalStyles} ${className}`}
        {...props}
      />
      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}
    </div>
  );
});

export default Textarea;
