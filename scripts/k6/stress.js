import { sleep } from 'k6';
import { cfg, get } from './common.js';

export const options = {
  scenarios: {
    ramp_rps: {
      executor: 'ramping-arrival-rate',
      startRate: 1,
      timeUnit: '1s',
      preAllocatedVUs: 10,
      maxVUs: 20,
      stages: [
        { target: 1, duration: '45s' },
        { target: 1, duration: '45s' },
        { target: 0, duration: '30s' }
      ],
    },
  },
  thresholds: {
    'http_req_failed': ['rate<0.01'],
    'http_req_duration': ['p(95)<7000'],
  },
};

export default function () {
  const { base, headers } = cfg();
  sleep(1);
  get(`${base}/api/healthz`, headers);
}
