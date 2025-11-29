import http from 'k6/http';
import { check, Trend } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 20 },
    { duration: '1m', target: 100 },
    { duration: '30s', target: 0 },
  ],
};

const latency = new Trend('latency_ms');

export default function () {
  const url = 'http://localhost:8000/messages'; // ajuste se sua rota for outra
  const payload = JSON.stringify({
    room_id: 10,
    sender_id: 1,
    content: 'Mensagem de teste k6',
  });
  const params = {
    headers: { 'Content-Type': 'application/json' },
  };
  const res = http.post(url, payload, params);
  latency.add(res.timings.duration);

  check(res, {
    'status is 201': (r) => r.status === 201, // ajuste pro status que sua API retorna
  });
}
