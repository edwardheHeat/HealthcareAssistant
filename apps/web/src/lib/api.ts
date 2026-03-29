const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

<<<<<<< HEAD
function getAuthHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const userId = localStorage.getItem("user_id");
  return userId ? { "X-User-ID": userId } : {};
}

=======
>>>>>>> 32e7e8429f7cd41eff9a8ad873be60f1e5e19156
async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
<<<<<<< HEAD
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
      ...options.headers,
    },
=======
    headers: { "Content-Type": "application/json", ...options.headers },
>>>>>>> 32e7e8429f7cd41eff9a8ad873be60f1e5e19156
    ...options,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new ApiError(res.status, text);
  }
  return res.json() as Promise<T>;
}

<<<<<<< HEAD
export { request, ApiError, BASE_URL, getAuthHeaders };
=======
export { request, ApiError, BASE_URL };
>>>>>>> 32e7e8429f7cd41eff9a8ad873be60f1e5e19156
