import { useState } from "react";

export function usePagination(initialPageSize = 20) {
  const [page, setPage] = useState(1);
  const pageSize = initialPageSize;
  const offset = (page - 1) * pageSize;
  return { page, pageSize, offset, setPage, reset: () => setPage(1) };
}
