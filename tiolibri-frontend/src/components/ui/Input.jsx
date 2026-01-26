/*
================================================================================
USAGE EXAMPLES
================================================================================

import Input from '@/components/ui/Input';

// Basic
<Input placeholder="Enter your email" />

// Controlled
const [email, setEmail] = useState('');
<Input
  type="email"
  value={email}
  onChange={(e) => setEmail(e.target.value)}
  placeholder="email@example.com"
/>

// With label (wrap in div)
<div>
  <label className="block text-sm font-medium text-gray-700 mb-1">
    Email
  </label>
  <Input type="email" placeholder="email@example.com" />
</div>

// With error
<Input
  type="email"
  value={email}
  onChange={(e) => setEmail(e.target.value)}
  error="Please enter a valid email address"
/>

// Disabled
<Input disabled value="Cannot edit" />

// Password
<Input type="password" placeholder="Enter password" />

// With icon (wrap in relative div)
<div className="relative">
  <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
  <Input className="pl-10" placeholder="Search..." />
</div>

================================================================================
*/

import { forwardRef } from 'react';

const Input = forwardRef(function Input(
  {
    type = 'text',
    placeholder,
    value,
    onChange,
    disabled = false,
    error,
    className = '',
    ...props
  },
  ref
) {
  const baseStyles =
    'block w-full px-3 py-2 border rounded-lg text-gray-900 placeholder-gray-400 transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-offset-0 disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed';

  const normalStyles =
    'border-gray-300 focus:border-indigo-500 focus:ring-indigo-500';

  const errorStyles =
    'border-red-500 focus:border-red-500 focus:ring-red-500';

  return (
    <div className="w-full">
      <input
        ref={ref}
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
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

export default Input;
