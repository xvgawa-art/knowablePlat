import { useParams } from "react-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router";
import { api } from "../api/client";
import type { GeneratedDoc } from "../types";

export default function GenerateHistory() {
  const { docId } = useParams();
  const queryClient = useQueryClient();

  const { data: docs = [] } = useQuery<GeneratedDoc[]>({
    queryKey: ["generatedDocs"],
    queryFn: () => api.get("/generate"),
  });

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
          <Link to="/generate/history" className="text-sm text-blue-600 hover:text-blue-800">
            返回列表
          </Link>
        </div>

        {selectedDoc.content ? (
          <pre className="whitespace-pre-wrap text-sm bg-gray-50 p-6 rounded-lg border border-gray-200 leading-relaxed">
            {selectedDoc.content}
          </pre>
        ) : (
          <div className="text-center py-12 text-gray-400">
            <p className="text-2xl mb-2">📝</p>
            <p>
              {selectedDoc.status === "generating" ? "文档正在生成中..." : "文档内容为空"}
            </p>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="p-8 max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">生成历史</h1>
        <Link to="/generate" className="text-sm text-blue-600 hover:text-blue-800">
          新建生成
        </Link>
      </div>

      {docs.length === 0 ? (
        <p className="text-gray-400 text-center py-12">暂无生成记录</p>
      ) : (
        <div className="space-y-3">
          {docs.map((doc) => (
            <div key={doc.id} className="flex items-center justify-between bg-white rounded-lg border border-gray-200 p-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <Link
                    to={`/generate/history/${doc.id}`}
                    className="font-medium text-gray-900 hover:text-blue-600 truncate"
                  >
                    {doc.title}
                  </Link>
                  <span
                    className={`px-2 py-0.5 text-xs rounded-full ${
                      doc.status === "completed"
                        ? "bg-green-50 text-green-700"
                        : doc.status === "generating"
                          ? "bg-yellow-50 text-yellow-700"
                          : "bg-red-50 text-red-700"
                    }`}
                  >
                    {doc.status === "completed" ? "已完成" : doc.status === "generating" ? "生成中" : "失败"}
                  </span>
                </div>
                <p className="text-sm text-gray-500 mt-1">
                  {doc.word_count} 字 · {new Date(doc.created_at).toLocaleDateString("zh-CN")}
                </p>
              </div>
              <button
                onClick={() => handleDelete(doc.id)}
                className="ml-4 px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded"
              >
                删除
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
