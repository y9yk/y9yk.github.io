'use strict';
window.sitePulseStory = (data, days) => {
  const names = { '/': 'The homepage', '/projects/': 'Projects', '/talks/': 'Talks', '/for-fun/': 'For fun', '/stats/': 'Site pulse', '/other/': 'Other pages' };
  const rows = data.pages.filter(row => row.count > 0);
  const total = data.range.pageviews;
  if (!rows.length || !total) return { headline: 'The story starts with the first visit.', detail: 'There are no recorded pageviews in this period yet.', share: null };
  const top = rows[0];
  const tied = rows.filter(row => row.count === top.count);
  const name = names[top.path] || 'Other pages';
  const share = Math.round(top.count / total * 100);
  if (tied.length > 1) {
    const labels = tied.map(row => names[row.path] || 'Other pages');
    const headline = tied.length === 2 ? `${labels[0]} and ${labels[1]} share the spotlight.` : `${tied.length} sections share the lead.`;
    return { headline, detail: `${labels.join(', ')} recorded ${top.count} pageviews each in this ${days}-day period.`, share: null };
  }
  const next = rows[1];
  return { headline: `${name} has the spotlight.`, detail: `${top.count} of ${total} pageviews (${share}%) went to this section in the selected ${days}-day period.${next ? ` ${names[next.path] || 'Other pages'} came next, with ${next.count}.` : ''}`, share };
};
