import createClient from 'openapi-fetch';

import type { paths } from './generated';

const baseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export const apiClient = createClient<paths>({ baseUrl });

export type ApiClient = typeof apiClient;
