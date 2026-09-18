// Namespaced Tag identifiers reuse the existing set-based facet engine.
export function fields(config, type) {
  return type === 'Tag'
    ? (config.tagFacets || []).map(t => ({id:'tag:'+t.name, label:t.label || t.name}))
    : config.facets.map(f => ({id:String(f), label:config.headers[f].split('(')[0]}));
}
export function fieldLabel(config, id) {
  const type = id.startsWith('tag:') ? 'Tag' : 'Metadata';
  return type+'：'+(fields(config,type).find(f=>f.id===id)?.label || id);
}
