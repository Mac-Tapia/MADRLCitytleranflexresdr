"""Read-only OSV lookup of installed non-editable PyPI package versions.

Sends only public distribution names and versions. Does not install packages,
load models, inspect credentials or start services. A version match is not a
demonstration of exploitability in the project. Git/editable dependencies and
container/OS/driver vulnerabilities require separate review.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from importlib import metadata
import json
from pathlib import Path
import re

import requests

OUT = Path(__file__).resolve().parent
API = 'https://api.osv.dev/v1'


def main():
    distributions = []
    excluded = []
    for dist in metadata.distributions():
        name = dist.metadata.get('Name')
        if not name:
            continue
        direct = dist.read_text('direct_url.json')
        if direct and json.loads(direct).get('dir_info', {}).get('editable'):
            excluded.append(name)
            continue
        name = re.sub(r'[-_.]+', '-', name).lower()
        distributions.append({'name': name, 'installed_version': dist.version,
                              'queried_version': dist.version.split('+', 1)[0]})
    unique = {(d['name'], d['installed_version']): d for d in distributions}
    distributions = sorted(unique.values(), key=lambda d: d['name'])
    all_results = []
    for offset in range(0, len(distributions), 100):
        chunk = distributions[offset:offset + 100]
        queries = [{'package': {'ecosystem': 'PyPI', 'name': d['name']},
                    'version': d['queried_version']} for d in chunk]
        response = requests.post(API+'/querybatch', json={'queries': queries}, timeout=45)
        response.raise_for_status()
        results = response.json()['results']
        if len(results) != len(chunk):
            raise ValueError('OSV result count mismatch')
        all_results += [{**d, 'advisory_ids': [v['id'] for v in r.get('vulns', [])],
                         'next_page_token': r.get('next_page_token')}
                        for d, r in zip(chunk, results)]
    ids = sorted({id for row in all_results for id in row['advisory_ids']})

    def detail(id):
        try:
            result = requests.get(API+'/vulns/'+id, timeout=30)
            result.raise_for_status()
            data = result.json()
            return {'id': id, 'aliases': data.get('aliases', []), 'summary': data.get('summary', ''),
                    'published': data.get('published'), 'withdrawn': data.get('withdrawn'),
                    'severity': data.get('severity', []), 'database_specific': data.get('database_specific', {}),
                    'affected': data.get('affected', []), 'references': data.get('references', [])}
        except requests.RequestException as exc:
            return {'id': id, 'lookup_error': type(exc).__name__}

    with ThreadPoolExecutor(max_workers=5) as pool:
        details = list(pool.map(detail, ids))
    result = {'checked_at_utc': datetime.now(timezone.utc).isoformat(),
              'api': API, 'packages_queried': len(distributions),
              'editable_excluded': sorted(excluded),
              'flagged_packages': sum(bool(r['advisory_ids']) for r in all_results),
              'advisory_ids_before_alias_deduplication': len(ids),
              'pagination_pending': any(r['next_page_token'] for r in all_results),
              'detail_lookup_errors': sum('lookup_error' in d for d in details),
              'scope': 'Installed PyPI versions only; no exploitability proof, updates or complete supply-chain certification.',
              'packages': all_results, 'advisories': details}
    (OUT/'osv.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k not in {'packages', 'advisories'}}, indent=2))
    print(json.dumps([{'name': p['name'], 'version': p['installed_version'], 'ids': p['advisory_ids']}
                      for p in all_results if p['advisory_ids']], indent=2))


if __name__ == '__main__':
    main()
