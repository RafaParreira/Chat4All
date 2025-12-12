import http from 'k6/http';
import { check, fail } from 'k6';
import { Trend } from 'k6/metrics';

export const options = {
  stages: [
    { duration: '30s', target: 20 },   // subida
    { duration: '1m', target: 100 },   // carga estável
    { duration: '30s', target: 0 },    // ramp-down
  ],
};

// métrica personalizada
const latency = new Trend('latency_ms');

export default function () {
  const url = 'http://localhost:8000/messages'; // ajuste se sua rota for diferente

  const payload = JSON.stringify({
    room_id: 1,
    sender_id: 1,
    content: `Mensagem de teste k6 - ${Math.random()}`, // garante unicidade
  });

  const params = {
    headers: { 'Content-Type': 'application/json' },
  };

  let res;

  try {
    res = http.post(url, payload, params);
  } catch (e) {
    fail(`❌ Erro ao enviar requisição: ${e}`);
  }

  // registra latência SOMENTE se resposta existir
  if (res && res.timings && res.timings.duration !== undefined) {
    latency.add(res.timings.duration);
  }

  // validações seguras
  const ok = check(res, {
    'resposta não é nula': (r) => r !== null && r !== undefined,
    'status válido (200, 201 ou 202)': (r) => r && (r.status === 200 || r.status === 201 || r.status === 202),
    'tempo menor que 500ms': (r) => r && r.timings.duration < 500,
  });

  // log visível de erro específico
  if (!ok) {
    console.warn(`⚠ Falha: status=${res?.status} body=${res?.body}`);
  }
}
