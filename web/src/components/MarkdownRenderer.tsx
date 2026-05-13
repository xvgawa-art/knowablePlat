import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface MarkdownRendererProps {
  content: string;
  kbSlug?: string;
}

export default function MarkdownRenderer({ content, kbSlug }: MarkdownRendererProps) {
  return (
    <div className="prose prose-gray max-w-none">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a({ href, children }) {
            if (href?.startsWith("[[") || href?.startsWith("/")) {
              return (
                <a href={href} className="text-blue-600 hover:underline">
                  {children}
                </a>
              );
            }
            return (
              <a href={href} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                {children}
              </a>
            );
          },
          code({ className, children, ...props }) {
            const isInline = !className;
            if (isInline) {
              return (
                <code className="px-1.5 py-0.5 bg-gray-100 text-sm rounded text-pink-600" {...props}>
                  {children}
                </code>
              );
            }
            return (
              <code className={className} {...props}>
                {children}
              </code>
            );
          },
          pre({ children }) {
            return <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm">{children}</pre>;
          },
          blockquote({ children }) {
            return <blockquote className="border-l-4 border-blue-300 pl-4 italic text-gray-600">{children}</blockquote>;
          },
          table({ children }) {
            return (
              <div className="overflow-x-auto">
                <table className="min-w-full border border-gray-200">{children}</table>
              </div>
            );
          },
          th({ children }) {
            return (
              <th className="px-4 py-2 bg-gray-50 border border-gray-200 text-left text-sm font-semibold">{children}</th>
            );
          },
          td({ children }) {
            return <td className="px-4 py-2 border border-gray-200 text-sm">{children}</td>;
          },
          h1({ children }) {
            return <h1 className="text-3xl font-bold mt-8 mb-4 text-gray-900">{children}</h1>;
          },
          h2({ children }) {
            return <h2 className="text-2xl font-semibold mt-6 mb-3 text-gray-800">{children}</h2>;
          },
          h3({ children }) {
            return <h3 className="text-xl font-medium mt-4 mb-2 text-gray-700">{children}</h3>;
          },
          ul({ children }) {
            return <ul className="list-disc list-inside space-y-1 mb-4">{children}</ul>;
          },
          ol({ children }) {
            return <ol className="list-decimal list-inside space-y-1 mb-4">{children}</ol>;
          },
          p({ children }) {
            return <p className="mb-4 leading-relaxed">{children}</p>;
          },
        }}
      >
        {transformWikilinks(content, kbSlug)}
      </ReactMarkdown>
    </div>
  );
}

function transformWikilinks(content: string, kbSlug?: string): string {
  return content.replace(/\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g, (_match, slug, label) => {
    const displayText = label || slug;
    if (kbSlug) {
      return `[${displayText}](/kb/${kbSlug}/wiki/${slug})`;
    }
    return `**${displayText}**`;
  });
}
