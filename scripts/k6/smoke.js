import { sleep } from 'k6';
import { smokeOnce } from './common.js';

export const options = {
  vus: 1,
  duration: '20s',
  thresholds: {
    'http_req_failed': ['rate<0.01'],
    'http_req_duration': ['p(95)<9000'],
  },
};

export default function () {
  sleep(2);
  smokeOnce();
}
