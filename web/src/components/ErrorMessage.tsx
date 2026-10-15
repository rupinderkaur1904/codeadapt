import { ApiError } from "../api/client";

export function ErrorMessage({ error }: { error: unknown }) {
  const text =
    error instanceof ApiError
      ? error.message
      : error instanceof Error
        ? error.message
        : "Something went wrong.";
  return (
    <p role="alert" className="error">
      {text}
    </p>
  );
}
