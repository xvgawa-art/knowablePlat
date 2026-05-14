import type { KnowledgeBase } from "../../types";

export default function EditForm({
  editName,
  editDesc,
  setEditName,
  setEditDesc,
  onSave,
  onCancel,
  isPending,
}: {
  kb: KnowledgeBase;
  editName: string;
  editDesc: string;
  setEditName: (v: string) => void;
  setEditDesc: (v: string) => void;
  onSave: () => void;
  onCancel: () => void;
  isPending: boolean;
}) {
  return (
    <div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">名称</label>
          <input
            type="text"
            value={editName}
            onChange={(e) => setEditName(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">描述</label>
          <input
            type="text"
            value={editDesc}
            onChange={(e) => setEditDesc(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
          />
        </div>
      </div>
      <div className="flex gap-2 mt-3">
        <button
          onClick={onSave}
          disabled={isPending}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {isPending ? "保存中..." : "保存"}
        </button>
        <button onClick={onCancel} className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50">
          取消
        </button>
      </div>
    </div>
  );
}
