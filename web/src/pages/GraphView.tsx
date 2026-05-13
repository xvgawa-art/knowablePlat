import { useEffect, useRef, useState, useCallback } from "react";
import { useParams, Link } from "react-router";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { GraphData } from "../types";

interface SimNode {
  id: string;
  slug: string;
  title: string;
  type: string;
  x: number;
  y: number;
  vx: number;
  vy: number;
}

const TYPE_COLORS: Record<string, string> = {
  source: "#3b82f6",
  entity: "#10b981",
  concept: "#8b5cf6",
  comparison: "#f59e0b",
  tool: "#ef4444",
  tool_category: "#ec4899",
};

export default function GraphView() {
  const { kbSlug } = useParams();
  const svgRef = useRef<SVGSVGElement>(null);
  const [hoveredNode, setHoveredNode] = useState<SimNode | null>(null);
  const nodesRef = useRef<SimNode[]>([]);
  const animRef = useRef<number>(0);

  const { data: graph, isLoading } = useQuery<GraphData>({
    queryKey: ["wikiGraph", kbSlug],
    queryFn: () => api.get(`/kb/${kbSlug}/wiki/graph`),
    enabled: !!kbSlug,
  });

  const simulate = useCallback(() => {
    const nodes = nodesRef.current;
    if (nodes.length === 0) return;

    const centerX = 400;
    const centerY = 300;
    const repulsion = 2000;
    const attraction = 0.01;
    const damping = 0.9;

    for (const node of nodes) {
      node.vx += (centerX - node.x) * 0.001;
      node.vy += (centerY - node.y) * 0.001;
    }

    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const ni = nodes[i]!;
        const nj = nodes[j]!;
        const dx = nj.x - ni.x;
        const dy = nj.y - ni.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = repulsion / (dist * dist);
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        ni.vx -= fx;
        ni.vy -= fy;
        nj.vx += fx;
        nj.vy += fy;
      }
    }

    if (graph) {
      const nodeMap = new Map(nodes.map((n) => [n.id, n]));
      for (const edge of graph.edges) {
        const src = nodeMap.get(edge.source);
        const tgt = nodeMap.get(edge.target);
        if (src && tgt) {
          const dx = tgt.x - src.x;
          const dy = tgt.y - src.y;
          src.vx += dx * attraction;
          src.vy += dy * attraction;
          tgt.vx -= dx * attraction;
          tgt.vy -= dy * attraction;
        }
      }
    }

    for (const node of nodes) {
      node.vx *= damping;
      node.vy *= damping;
      node.x += node.vx;
      node.y += node.vy;
    }
  }, [graph]);

  useEffect(() => {
    if (!graph || graph.nodes.length === 0) return;

    const simNodes: SimNode[] = graph.nodes.map((n, i) => {
      const angle = (2 * Math.PI * i) / graph.nodes.length;
      return {
        ...n,
        x: 400 + Math.cos(angle) * 150,
        y: 300 + Math.sin(angle) * 150,
        vx: 0,
        vy: 0,
      };
    });
    nodesRef.current = simNodes;

    function tick() {
      simulate();
      const svg = svgRef.current;
      if (!svg) return;

      const nodeMap = new Map(simNodes.map((n) => [n.id, n]));

      svg.querySelectorAll<SVGLineElement>(".graph-edge").forEach((line) => {
        const src = nodeMap.get(line.dataset.source ?? "");
        const tgt = nodeMap.get(line.dataset.target ?? "");
        if (src && tgt) {
          line.setAttribute("x1", String(src.x));
          line.setAttribute("y1", String(src.y));
          line.setAttribute("x2", String(tgt.x));
          line.setAttribute("y2", String(tgt.y));
        }
      });

      svg.querySelectorAll<SVGGElement>(".graph-node").forEach((g) => {
        const node = nodeMap.get(g.dataset.id ?? "");
        if (node) {
          g.setAttribute("transform", `translate(${node.x},${node.y})`);
        }
      });

      animRef.current = requestAnimationFrame(tick);
    }

    animRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(animRef.current);
  }, [graph, simulate]);

  if (isLoading) return <div className="p-8 text-gray-500">加载图谱数据...</div>;

  if (!graph || graph.nodes.length === 0) {
    return (
      <div className="p-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">知识图谱</h1>
        <p className="text-gray-400 text-center py-12">暂无 Wiki 页面，无法生成图谱</p>
      </div>
    );
  }

  const nodeMap = new Map(nodesRef.current.map((n) => [n.id, n]));

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-gray-900">知识图谱</h1>
        <Link to={`/kb/${kbSlug}/wiki`} className="text-sm text-blue-600 hover:text-blue-800">
          返回 Wiki 列表
        </Link>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <svg ref={svgRef} width="100%" viewBox="0 0 800 600" className="block">
          {graph.edges.map((edge, i) => (
            <line
              key={i}
              className="graph-edge"
              data-source={edge.source}
              data-target={edge.target}
              stroke="#d1d5db"
              strokeWidth={1}
            />
          ))}

          {graph.nodes.map((node) => {
            const simNode = nodeMap.get(node.id);
            const color = TYPE_COLORS[node.type] ?? "#6b7280";
            return (
              <g
                key={node.id}
                className="graph-node cursor-pointer"
                data-id={node.id}
                transform={`translate(${simNode?.x ?? 400},${simNode?.y ?? 300})`}
                onMouseEnter={() => simNode && setHoveredNode(simNode)}
                onMouseLeave={() => setHoveredNode(null)}
              >
                <a href={`/kb/${kbSlug}/wiki/${node.slug}`}>
                  <circle r={8} fill={color} stroke="white" strokeWidth={2} />
                  <text
                    textAnchor="middle"
                    y={-14}
                    className="text-[10px] fill-gray-700 pointer-events-none"
                  >
                    {node.title.length > 12 ? node.title.slice(0, 12) + "…" : node.title}
                  </text>
                </a>
              </g>
            );
          })}
        </svg>

        {hoveredNode && (
          <div className="absolute bottom-4 left-4 bg-white border border-gray-200 rounded-lg p-3 shadow-lg">
            <p className="font-medium text-gray-900">{hoveredNode.title}</p>
            <p className="text-xs text-gray-500">{hoveredNode.type}</p>
            <Link
              to={`/kb/${kbSlug}/wiki/${hoveredNode.slug}`}
              className="text-xs text-blue-600 hover:text-blue-800"
            >
              查看页面
            </Link>
          </div>
        )}
      </div>

      <div className="mt-4 flex flex-wrap gap-3">
        {Object.entries(TYPE_COLORS).map(([type, color]) => (
          <div key={type} className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
            <span className="text-xs text-gray-600">{type}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
