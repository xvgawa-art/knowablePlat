import { useParams } from "react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router";
import { api } from "../api/client";
import MarkdownRenderer from "../components/MarkdownRenderer";
import Pagination from "../components/Pagination";
import { usePagination } from "../hooks/usePagination";
import { useBatchSelect } from "../hooks/useBatchSelect";
import type { GeneratedDoc, PaginatedResponse } from "../types";

export default function GenerateHistory() {
  const { docId } = useParams();
  const queryClient = useQueryClient();

  const { data: selectedDoc, isLoading } = useQuery<GeneratedDoc>({
    queryKey: ["generatedDoc", docId],
    queryFn: () => api.get(`/generate/${docId}`),
    enabled: !!docId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data?.status === "generating") return 5000;
      return false;
    },
  });

  async function handleDelete(id: string) {
    if (!confirm("确定删除此生成文档？")) return;
    await api.del(`/generate/${id}`);
    queryClient.invalidateQueries({ queryKey: ["generatedDocs"] });
  }

  if (docId) {
    if (isLoading) return <div className="p-8 text-gray-500">加载中...</div>;
    if (!selectedDoc) return <div className="p-8 text-red-600">文档不存在</div>;
    return (
      <div className="p-8 max-w-4xl">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{selectedDoc.title}</h1>
            <p className="text-sm text-gray-500 mt-1">
              {selectedDoc.word_count} 字 · {new Date(selectedDoc.created_at).toLocaleDateString("zh-CN")}
            </p>
          </div>
          <Link to="/generate/history" className="text-sm text-blue-600 hover:text-blue-800">返回列表</Link>
        </div>
        {selectedDoc.content ? (
          <div className="bg-white p-6 rounded-lg border border-gray-200">
            <MarkdownRenderer content={selectedDoc.content} />
          </div>
        ) : (
          <div className="text-center py-12 text-gray-400">
            <p className="text-2xl mb-2">📝</p>
            <p>{selectedDoc.status === "generating" ? "文档正在生成中..." : "文档内容为空"}</p>
          </div>
        )}
      </div>
    );
  }

  return <DocListPage handleDelete={handleDelete} queryClient={queryClient} />;
}

function DocListPage({
  handleDelete,
  queryClient,
}: {
  handleDelete: (id: string) => Promise<void>;
  queryClient: ReturnType<typeof useQueryClient>;
}) {
  const pagination = usePagination(20);
  const batch = useBatchSelect();

  const { data, isLoading } = useQuery<PaginatedResponse<GeneratedDoc>>({
    queryKey: ["generatedDocs", pagination.offset, pagination.pageSize],
    queryFn: () => api.get("/generate", { offset: pagination.offset, limit: pagination.pageSize }),
  });

  const docs = data?.items ?? [];
  const total = data?.total ?? 0;

  const batchDeleteMutation = useMutation({
    mutationFn: (ids: string[]) => api.post("/generate/batch-delete", { ids }),
    onSuccess: () => {
      batch.clearAll();
      queryClient.invalidateQueries({ queryKey: ["generatedDocs"] });
    },
  });

  async function handleBatchDelete() {
    if (!confirm(`确定删除选中的 ${batch.selectedIds.size} 项？`)) return;
    batchDeleteMutation.mutate(Array.from(batch.selectedIds));
  }

  const allIds = docs.map((d) => d.id);

  return (
    <div className="p-8 max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">生成历史</h1>
        <div className="flex gap-3 items-center">
          {batch.selectedIds.size > 0 && (
            <button
              onClick={handleBatchDelete}
              disabled={batchDeleteMutation.isPending}
              className="px-3 py-1.5 text-sm bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
            >
              删除选中 ({batch.selectedIds.size})
            </button>
          )}
          <Link to="/generate" className="text-sm text-blue-600 hover:text-blue-800">新建生成</Link>
        </div>
      </div>

      {isLoading ? (
        <p className="text-gray-500">加载中...</p>
      ) : docs.length === 0 ? (
        <p className="text-gray-400 text-center py-12">暂无生成记录</p>
      ) : (
        <>
          <div className="mb-2 flex items-center gap-2">
            <input
              type="checkbox"
              checked={allIds.length > 0 && allIds.every((id) => batch.isSelected(id))}
              onChange={() => (allIds.every((id) => batch.isSelected(id)) ? batch.clearAll() : batch.selectAll(allIds))}
              className="rounded border-gray-300"
            />
            <span className="text-xs text-gray-500">全选</span>
          </div>
          <div className="space-y-3">
            {docs.map((doc) => (
              <div key={doc.id} className="flex items-center gap-3 bg-white rounded-lg border border-gray-200 p-4">
                <input
                  type="checkbox"
                  checked={batch.isSelected(doc.id)}
                  onChange={() => batch.toggle(doc.id)}
                  className="rounded border-gray-300"
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <Link to={`/generate/history/${doc.id}`} className="font-medium text-gray-900 hover:text-blue-600 truncate">
                      {doc.title}
                    </Link>
                    <span className={`px-2 py-0.5 text-xs rounded-full ${
                      doc.status === "completed" ? "bg-green-50 text-green-700"
                        : doc.status === "generating" ? "bg-yellow-50 text-yellow-700"
                          : "bg-red-50 text-red-700"
                    }`}>
                      {doc.status === "completed" ? "已完成" : doc.status === "generating" ? "生成中" : "失败"}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 mt-1">
                    {doc.word_count} 字 · {new Date(doc.created_at).toLocaleDateString("zh-CN")}
                  </p>
                </div>
                <button onClick={() => handleDelete(doc.id)} className="ml-4 px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded">
                  删除
                </button>
              </div>
            ))}
          </div>
          <Pagination page={pagination.page} pageSize={pagination.pageSize} total={total} onPageChange={pagination.setPage} />
        </>
      )}
    </div>
  );
}
