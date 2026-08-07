const ACTION_LABELS = {
  'chapter.edit': (d) => `edytował(a) "${d.title || 'rozdział'}"`,
  'chapter.rename': (d) => `zmienił(a) nazwę "${d.old_title}" → "${d.new_title}"`,
  'chapter.delete': (d) => `przeniósł(a) "${d.title || 'rozdział'}" do kosza`,
  'chapter.restore': (d) => `przywrócił(a) "${d.title || 'rozdział'}"`,
  'chapter.restore_version': (d) => `przywrócił(a) wersję w "${d.title || 'rozdział'}"`,
  'chapter.status_change': (d) => `zmienił(a) status "${d.title || 'rozdział'}" → ${d.status}`,
  'chapter.lock': (d) => `zablokował(a) "${d.title || 'rozdział'}"`,
  'chapter.unlock': (d) => `odblokował(a) "${d.title || 'rozdział'}"`,
  'project.share': (d) => `udostępnił(a) projekt → ${d.shared_with_email}`,
  'project.unshare': (d) => `cofnął(a) dostęp dla ${d.shared_with_email}`,
  'project.restore_snapshot': () => 'przywrócił(a) projekt ze snapshot',
  'project.snapshot_manual': () => 'zapisał(a) ręczny snapshot projektu',
  'project.export': (d) => `wyeksportował(a) projekt${d.filename ? ` (${d.filename})` : ''}`,
  'project.import_from_tiolibri': (d) => `zaimportował(a) projekt "${d.original_title || ''}"`,
  'project.export_md': (d) => `wyeksportował(a) książkę do Redaktora (${d.chapter_count ?? '?'} rozdz.)`,
}

export function actionLabel(event) {
  const fn = ACTION_LABELS[event.action_type]
  if (fn) return fn(event.details || {})
  return event.action_type.replace('.', ' ')
}

export function authorInitial(email) {
  if (!email) return '?'
  return email.charAt(0).toUpperCase()
}
