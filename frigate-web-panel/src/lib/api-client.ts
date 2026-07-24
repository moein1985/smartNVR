import createClient from "openapi-fetch";
import type { paths } from "./api/generated";

const BASE_URL = "";

export const apiClient = createClient<paths>({
  baseUrl: BASE_URL,
});
