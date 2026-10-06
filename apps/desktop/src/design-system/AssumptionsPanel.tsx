import React, { useState } from 'react';

export interface AssumptionsPanelProps {
  modelScope?: string[];
  inputEvidence?: { label: string; status: string }[];
  limitations?: string[];
  qualification?: string;
  defaultExpanded?: boolean;
}

export const AssumptionsPanel: React.FC<AssumptionsPanelProps> = ({
  modelScope = ['Steady state', 'Single phase', 'Current active geometry revision'],
  inputEvidence = [
    { label: 'Survey Program', status: 'Accepted & Verified' },
    { label: 'Mud Program', status: 'Supplied & Checked' },
    { label: 'Drill String Geometry', status: 'Validated Contiguous' },
  ],
  limitations = [
    'No multiphase flow dynamics or gas influx modeled in steady state',
    'No thermal coupling or non-isothermal rheology variation',
    'Advisory calculation only: does NOT generate equipment authority or well control clearances',
  ],
  qualification = 'Verified against published analytical and numerical benchmarks. Independent engineering qualification pending.',
  defaultExpanded = false,
}) => {
  const [expanded, setExpanded] = useState(defaultExpanded);

  return (
    <div className="border border-slate-200 rounded-lg bg-slate-50 overflow-hidden text-xs my-3 shadow-xs">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="w-full px-3 py-2 bg-slate-100/80 hover:bg-slate-200/60 flex items-center justify-between text-left text-slate-700 font-medium transition cursor-pointer select-none"
      >
        <div className="flex items-center gap-2">
          <span className="text-amber-600 font-bold">ℹ</span>
          <span>Engineering Assumptions, Evidence & Declared Limitations</span>
        </div>
        <span className="text-slate-400 text-[10px] font-mono">{expanded ? '▲ Collapse' : '▼ View Details'}</span>
      </button>

      {expanded && (
        <div className="p-3 grid grid-cols-1 md:grid-cols-4 gap-4 bg-white border-t border-slate-200">
          <div>
            <h4 className="font-semibold text-slate-500 uppercase tracking-wider text-[10px] mb-1.5">Model Scope</h4>
            <ul className="space-y-1 text-slate-700">
              {modelScope.map((item, idx) => (
                <li key={idx} className="flex items-start gap-1.5">
                  <span className="text-slate-400">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="font-semibold text-slate-500 uppercase tracking-wider text-[10px] mb-1.5">Input Evidence</h4>
            <ul className="space-y-1.5 text-slate-700">
              {inputEvidence.map((ev, idx) => (
                <li key={idx} className="flex flex-col">
                  <span className="text-[11px] font-medium text-slate-800">{ev.label}</span>
                  <span className="text-[10px] text-emerald-700">{ev.status}</span>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="font-semibold text-amber-700 uppercase tracking-wider text-[10px] mb-1.5">Physical Limitations</h4>
            <ul className="space-y-1 text-slate-600">
              {limitations.map((lim, idx) => (
                <li key={idx} className="flex items-start gap-1.5">
                  <span className="text-amber-500">⚠</span>
                  <span>{lim}</span>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="font-semibold text-sky-700 uppercase tracking-wider text-[10px] mb-1.5">Qualification Status</h4>
            <p className="text-slate-700 leading-relaxed mb-2">{qualification}</p>
            <div className="text-[10px] text-slate-400 border-t border-slate-100 pt-1.5 font-mono">
              Deterministic SI Engine Authority
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
