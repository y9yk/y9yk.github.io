# Aggregate statistics

Site pulse uses anonymous browser-tab sessions and pageviews, not identified people or GA4 users. The browser sends only a random event ID, tab-session ID, normalized page path, broad screen-size category, and referrer hostname. Query strings, full referrer URLs, names, raw IPs/user agents, and location trails are excluded from the database. DNT/GPC and non-production hosts skip collection.

The collector hashes session identifiers by day, deduplicates event IDs, and returns only grouped counts. Public path reports merge detail routes into broad sections, so individual detail-page paths are not exposed. The dashboard names the leading section using actual totals and handles ties without inventing a winner. Charts exclude unmeasured dates; no sample traffic is inserted.

The separate Railway collector uses the existing `/data` volume. Retention is 90 days. Source: `services/analytics/`. Deploy it only after linking the collector project in Railway CLI:

```sh
railway up services/analytics --path-as-root --service analytics --detach
```

Backend deploys are separate from Pages and must preserve the mounted volume. A volume is not a backup. Frontend origin and production hostname are configured in `content/profile.json`. Changing the public domain also requires reviewing the collector origin allowlist.
