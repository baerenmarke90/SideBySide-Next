import { ResponseError } from '../api/generated/runtime';
import {
  classifyProblemStatus,
  ClientProblemError,
  normalizeClientError,
} from './problemDetails';

describe('ProblemDetails mapping', () => {
  it('maps stable HTTP states to privacy-safe client kinds', () => {
    expect(classifyProblemStatus(401)).toBe('unauthorized');
    expect(classifyProblemStatus(403)).toBe('permission');
    expect(classifyProblemStatus(404)).toBe('notFound');
    expect(classifyProblemStatus(409)).toBe('conflict');
    expect(classifyProblemStatus(429)).toBe('rateLimit');
    expect(classifyProblemStatus(503)).toBe('server');
  });

  it('keeps the stable code but never exposes backend detail as the error message', async () => {
    const response = new Response(
      JSON.stringify({
        type: 'conflict',
        title: 'Internal conflict title',
        status: 409,
        detail: 'Sensitive backend detail that must stay out of product copy',
        code: 'MEMORY_VERSION_CONFLICT',
      }),
      {
        status: 409,
        headers: { 'content-type': 'application/json' },
      },
    );

    const error = await normalizeClientError(new ResponseError(response));

    expect(error).toBeInstanceOf(ClientProblemError);
    expect(error.kind).toBe('conflict');
    expect(error.status).toBe(409);
    expect(error.code).toBe('MEMORY_VERSION_CONFLICT');
    expect(error.message).not.toContain('Sensitive backend detail');
    expect(error.message).not.toContain('Internal conflict title');
  });

  it('falls back to the response status for malformed error bodies', async () => {
    const error = await normalizeClientError(
      new ResponseError(new Response('not json', { status: 503 })),
    );

    expect(error.kind).toBe('server');
    expect(error.status).toBe(503);
    expect(error.code).toBeUndefined();
  });
});
