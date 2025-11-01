import http from 'k6/http';
import { check, sleep } from 'k6';
import { b64encode } from 'k6/encoding';

export function cfg() {
  const host = __ENV.K6_HOST || 'cstr_traefik';
  const port = __ENV.K6_PORT || '80';
  const base = `http://${host}:${port}`;
  const user = __ENV.K6_USER || 'apiuser';
  const pass = __ENV.K6_PASS || 'apipass-CHANGE-ME';
  const auth = 'Basic ' + b64encode(`${user}:${pass}`);
  const headers = { Authorization: auth };
  return { base, headers };
}

export function get(url, headers) {
  const res = http.get(url, { headers, tags: { name: url } });
  check(res, {
    'status 200': (r) => r.status === 200,
  });
  if (res.status !== 200) {
    console.error(`unexpected status ${res.status} for ${url} body=${res.body}`);
  }
  return res;
}

export function smokeOnce() {
  const { base, headers } = cfg();
  get(`${base}/api/healthz`, headers);
  get(`${base}/api/measurements?limit=5`, headers);
  get(`${base}/api/observations?limit=5`, headers);
  sleep(1);
}
