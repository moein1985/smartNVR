import createClient from "openapi-fetch";
import type { paths } from "./api/generated";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://192.168.85.202:8088";

export const apiClient = createClient<paths>({
  baseUrl: BASE_URL,
});
