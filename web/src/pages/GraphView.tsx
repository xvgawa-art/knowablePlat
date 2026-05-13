import { useEffect, useRef } from "react";
import { useParams, Link, useNavigate } from "react-router";
import { useQuery } from "@tanstack/react-query";
import * as d3 from "d3";
import { api } from "../api/client";
import type { GraphData } from "../types";

interface SimNode extends d3.SimulationNodeDatum {
  id: string;
  slug: string;
  title: string;
  type: string;
}

interface SimEdge extends d3.SimulationLinkDatum<SimNode> {
  source: SimNode | string;
  target: SimNode | string;
}

const TYPE_COLORS: Record<string, string> = {
  source: "#3b82f6",
  entity: "#10b981",
  concept: "#8b5cf6",
  comparison: "#f59e0b",
  tool: "#ef4444",
  tool_category: "#ec4899",
};

const TYPE_LABELS: Record<string, string> = {
  source: "来源摘要",
  entity: "实体",
  concept: "概念",
  comparison: "对比",
  tool: "工具",
  tool_category: "工具分类",
};

export default function GraphView() {
  const { kbSlug } = useParams();
  const navigate = useNavigate();
  const containerRef = useRef<HTMLDivElement>(null);
  const simulationRef = useRef<d3.Simulation<SimNode, SimEdge> | null>(null);

  const { data: graph, isLoading, error } = useQuery<GraphData>({
    queryKey: ["wikiGraph", kbSlug],
    queryFn: () => api.get(`/kb/${kbSlug}/wiki/graph`),
    enabled: !!kbSlug,
  });

  useEffect(() => {
    if (!graph || graph.nodes.length === 0 || !containerRef.current) return;
    const container = containerRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight;

    d3.select(container).select("svg").remove();
    const svg = d3.select(container).append("svg").attr("width", width).attr("height", height);
    const g = svg.append("g");

    svg.call(d3.zoom<SVGSVGElement, unknown>().scaleExtent([0.3, 4])
      .on("zoom", (event) => g.attr("transform", event.transform)));

    const nodes: SimNode[] = graph.nodes.map((n) => ({ ...n }));
    const edges: SimEdge[] = graph.edges.map((e) => ({ ...e }));

    simulationRef.current = d3.forceSimulation<SimNode>(nodes)
      .force("link", d3.forceLink<SimNode, SimEdge>(edges).id((d) => d.id).distance(100))
      .force("charge", d3.forceManyBody().strength(-250))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(35));

    g.append("g").selectAll("line").data(edges).join("line")
      .attr("stroke", "#d1d5db").attr("stroke-width", 1.5).attr("stroke-opacity", 0.6);

    const nodeGroup = g.append("g").selectAll<SVGGElement, SimNode>(".node")
      .data(nodes).join("g").attr("class", "node").attr("cursor", "pointer")
      .call(d3.drag<SVGGElement, SimNode>()
        .on("start", (event, d) => {
          if (!event.active) simulationRef.current?.alphaTarget(0.3).restart();
          d.fx = d.x; d.fy = d.y;
        })
        .on("drag", (event, d) => { d.fx = event.x; d.fy = event.y; })
        .on("end", (event, d) => {
          if (!event.active) simulationRef.current?.alphaTarget(0);
          d.fx = null; d.fy = null;
        }));

    nodeGroup.append("circle").attr("r", 10)
      .attr("fill", (d) => TYPE_COLORS[d.type] || "#6b7280")
      .attr("stroke", "#fff").attr("stroke-width", 2).attr("stroke-opacity", 0.8);

    nodeGroup.append("text")
      .text((d) => (d.title.length > 14 ? d.title.slice(0, 14) + "…" : d.title))
      .attr("dy", -16).attr("text-anchor", "middle").attr("font-size", "11px")
      .attr("fill", "#374151").attr("pointer-events", "none").attr("font-weight", 500);

    nodeGroup.on("click", (_event, d) => navigate(`/kb/${kbSlug}/wiki/${d.slug}`));

    simulationRef.current.on("tick", () => {
      g.selectAll<SVGLineElement, SimEdge>("line")
        .attr("x1", (d) => (d.source as SimNode).x ?? 0)
        .attr("y1", (d) => (d.source as SimNode).y ?? 0)
        .attr("x2", (d) => (d.target as SimNode).x ?? 0)
        .attr("y2", (d) => (d.target as SimNode).y ?? 0);
      nodeGroup.attr("transform", (d) => `translate(${d.x ?? 0},${d.y ?? 0})`);
    });

    return () => { simulationRef.current?.stop(); simulationRef.current = null; svg.remove(); };
  }, [graph, kbSlug, navigate]);

  if (isLoading) return <div className="p-8 text-gray-500">加载图谱数据...</div>;
  if (error) return <div className="p-8 text-red-600">加载失败</div>;

  const activeTypes = graph
    ? [...new Set(graph.nodes.map((n) => n.type))]
    : [];

  return (
    <div className="p-8 h-[calc(100vh-4rem)] flex flex-col">
      <div className="flex items-center justify-between mb-4 shrink-0">
        <div className="flex items-center gap-4">
          <Link to={`/kb/${kbSlug}/wiki`} className="text-sm text-blue-600 hover:text-blue-800">
            ← 返回 Wiki
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">知识图谱</h1>
          {graph && (
            <span className="text-sm text-gray-500">
              {graph.nodes.length} 个节点 · {graph.edges.length} 条连线
            </span>
          )}
        </div>
        <div className="flex items-center gap-4">
          {activeTypes.map((type) => (
            <div key={type} className="flex items-center gap-1.5">
              <span
                className="inline-block w-3 h-3 rounded-full"
                style={{ backgroundColor: TYPE_COLORS[type] || "#6b7280" }}
              />
              <span className="text-xs text-gray-600">{TYPE_LABELS[type] || type}</span>
            </div>
          ))}
        </div>
      </div>

      {graph && graph.nodes.length === 0 ? (
        <div className="text-center py-20 text-gray-400">
          <p className="text-lg">暂无 Wiki 页面</p>
          <p className="text-sm mt-2">提交来源后，Wiki 页面将自动生成并出现在图谱中</p>
        </div>
      ) : (
        <div
          ref={containerRef}
          className="flex-1 border border-gray-200 rounded-lg bg-white overflow-hidden"
        >
          <svg className="w-full h-full" />
        </div>
      )}
    </div>
  );
}
