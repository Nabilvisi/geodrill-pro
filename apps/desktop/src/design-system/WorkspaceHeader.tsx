import React from 'react';

export interface WorkspaceHeaderProps {
  projectName?: string;
  wellName?: string;
  wellboreName?: string;
  revisionName?: string;
  geometryRevision?: string;
  modelName?: string;
  modelVersion?: string;
  qualificationStatus?: 'research' | 'verified' | 'qualified' | 'withheld' | 'stale';
  unitProfile?: string;
  crs?: string;
  lastRun?: string;
  onRefresh?: () => void;
}

export const WorkspaceHeader: React.FC<WorkspaceHeaderProps> = ({
  projectName = 'Volve Alpha',
  wellName = '15/9-F-12',
  wellboreName = 'Main Bore',
  revisionName = 'Plan R03',
  geometryRevision = 'GR-01',
  modelName = 'Directional',
  modelVersion = '0.9.0',
  qualificationStatus = 'verified',
  unitProfile = 'Metric SI',
  crs = 'ED50 / UTM Zone 31N',
  lastRun = 'Just now',
  onRefresh,
}) => {
  const statusColors = {
    verified: 'bg-emerald-50 text-emerald-700 border-emerald-300',
    qualified: 'bg-blue-50 text-blue-700 border-blue-300',
    research: 'bg-cyan-50 text-cyan-700 border-cyan-300',
    stale: 'bg-purple-50 text-purple-700 border-purple-300',
    withheld: 'bg-slate-100 text-slate-700 border-slate-300',
  };

  return (
    <div className="bg-white border-b border-slate-200 px-4 py-2 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-600 select-none shadow-sm">
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-1.5 font-medium">
          <span className="text-slate-400 font-normal">Project:</span>
          <span className="text-slate-900 font-semibold">{projectName}</span>
        </div>

        <span className="text-slate-300">/</span>

        <div className="flex items-center gap-1.5 font-medium">
          <span className="text-slate-400 font-normal">Well:</span>
          <span className="text-slate-800">{wellName}</span>
        </div>

        <span className="text-slate-300">/</span>

        <div className="flex items-center gap-1.5 font-medium">
          <span className="text-slate-400 font-normal">Wellbore:</span>
          <span className="text-slate-800">{wellboreName}</span>
        </div>

        <span className="text-slate-300">|</span>

        <div className="flex items-center gap-1.5">
          <span className="text-slate-400">Rev:</span>
          <span className="px-1.5 py-0.5 rounded bg-slate-100 border border-slate-200 font-mono text-[11px] text-slate-700">
            {revisionName} ({geometryRevision})
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          <span className="text-slate-400">CRS:</span>
          <span className="font-mono text-[11px] text-slate-700">{crs}</span>
        </div>

        <div className="flex items-center gap-1.5">
          <span className="text-slate-400">Units:</span>
          <span className="text-slate-700">{unitProfile}</span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5">
          <span className="text-slate-400">Model:</span>
          <span className="font-medium text-slate-800">{modelName} v{modelVersion}</span>
          <span className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider border ${statusColors[qualificationStatus]}`}>
            {qualificationStatus}
          </span>
        </div>

        <div className="text-slate-400 text-[11px]">
          Run: {lastRun}
        </div>

        {onRefresh && (
          <button
            onClick={onRefresh}
            className="p-1 rounded hover:bg-slate-100 text-slate-500 hover:text-slate-700 transition"
            title="Recalculate workspace"
          >
            ↻
          </button>
        )}
      </div>
    </div>
  );
};
