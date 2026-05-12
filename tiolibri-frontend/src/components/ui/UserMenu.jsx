import { useState, useRef, useEffect } from 'react'

/* global __APP_VERSION__ */
const APP_VERSION = typeof __APP_VERSION__ !== 'undefined' ? __APP_VERSION__ : '?'

function getInitials(email) {
  if (!email) return '?'
  return email.charAt(0).toUpperCase()
}

export default function UserMenu({ user, onSignOut }) {
  const [open, setOpen] = useState(false)
  const menuRef = useRef(null)

  useEffect(() => {
    if (!open) return
    function handleClick(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [open])

  const handleSignOut = () => {
    setOpen(false)
    onSignOut()
  }

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setOpen(v => !v)}
        className="w-9 h-9 rounded-full bg-blue-600 text-white text-sm font-semibold flex items-center justify-center hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
        aria-label="Menu użytkownika"
        aria-expanded={open}
      >
        {getInitials(user?.email)}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-64 bg-white rounded-xl shadow-lg border border-gray-200 py-1 z-50">
          <div className="px-4 py-3 border-b border-gray-100">
            <p className="text-xs text-gray-500 mb-0.5">Zalogowany jako</p>
            <p className="text-sm font-medium text-gray-900 truncate">{user?.email}</p>
          </div>

          <button
            onClick={handleSignOut}
            className="w-full text-left px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Wyloguj
          </button>

          <div className="border-t border-gray-100 px-4 py-2 mt-1">
            <p className="text-xs text-gray-400">v{APP_VERSION}</p>
          </div>
        </div>
      )}
    </div>
  )
}
