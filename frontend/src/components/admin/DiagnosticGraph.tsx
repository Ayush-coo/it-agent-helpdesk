import { useMemo } from 'react';
import ReactFlow, { Background, Controls, Node, Edge } from 'reactflow';
import 'reactflow/dist/style.css';

interface DiagnosticStep {
  step: number;
  action: string;
  result: string;
  timestamp: string;
}

interface DiagnosticGraphProps {
  trail: DiagnosticStep[];
}

export default function DiagnosticGraph({ trail }: DiagnosticGraphProps) {
  const { nodes, edges } = useMemo(() => {
    if (!trail || trail.length === 0) return { nodes: [], edges: [] };

    const newNodes: Node[] = trail.map((item, index) => {
      const isLast = index === trail.length - 1;
      const isEscalation = item.action.toLowerCase().includes('escalation');
      const isError = item.result.toLowerCase().includes('error') || item.result.toLowerCase().includes('failed');
      
      let bg = '#1e293b'; // slate-800
      let border = '#334155'; // slate-700
      let text = '#f1f5f9'; // slate-100

      if (isEscalation || isError) {
        bg = '#4c0519'; // rose-950
        border = '#be123c'; // rose-700
        text = '#fda4af'; // rose-300
      } else if (isLast) {
        bg = '#064e3b'; // emerald-950
        border = '#047857'; // emerald-700
        text = '#6ee7b7'; // emerald-300
      }

      return {
        id: `step-${item.step}`,
        position: { x: 50 + index * 220, y: 150 + (index % 2 === 0 ? 0 : 50) },
        data: { 
          label: (
            <div className="flex flex-col items-start text-left p-1">
              <div className="text-[10px] font-bold uppercase tracking-wider mb-1 opacity-70">Step {item.step}</div>
              <div className="text-sm font-semibold mb-1">{item.action}</div>
              <div className="text-xs opacity-90 line-clamp-3 leading-snug">{item.result}</div>
            </div>
          )
        },
        style: {
          background: bg,
          color: text,
          border: `1px solid ${border}`,
          borderRadius: '12px',
          width: 180,
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.5)',
        }
      };
    });

    const newEdges: Edge[] = trail.slice(0, -1).map((item, index) => ({
      id: `edge-${item.step}-${trail[index + 1].step}`,
      source: `step-${item.step}`,
      target: `step-${trail[index + 1].step}`,
      animated: true,
      style: { stroke: '#8bd4ff', strokeWidth: 2, opacity: 0.5 },
    }));

    return { nodes: newNodes, edges: newEdges };
  }, [trail]);

  return (
    <div className="w-full h-full min-h-[300px] bg-slate-950/50 rounded-xl border border-slate-800 overflow-hidden">
      <ReactFlow nodes={nodes} edges={edges} fitView attributionPosition="bottom-right">
        <Background color="#334155" gap={20} size={1} />
        <Controls className="fill-slate-400 bg-slate-900 border-slate-800" />
      </ReactFlow>
    </div>
  );
}
