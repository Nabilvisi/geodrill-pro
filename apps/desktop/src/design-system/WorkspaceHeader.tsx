import React from 'react';
export interface WorkspaceHeaderProps {
  projectName?:string;wellName?:string;wellboreName?:string;revisionName?:string;geometryRevision?:string;
  modelName?:string;modelVersion?:string;qualificationStatus?:'research'|'verified'|'qualified'|'withheld'|'stale';
  unitProfile?:string;crs?:string;lastRun?:string;onRefresh?:()=>void;
}
export const WorkspaceHeader:React.FC<WorkspaceHeaderProps>=({
  projectName='Not selected',wellName='Not selected',wellboreName='Not selected',revisionName='Not saved',
  geometryRevision='Not saved',modelName='Not selected',modelVersion='Not declared',qualificationStatus='research',
  unitProfile='Not declared',crs='Unreferenced',lastRun='Not calculated',onRefresh
})=><div className="workspace-context" aria-label="Engineering context">
  <dl>{[['Project',projectName],['Well',wellName],['Wellbore',wellboreName],['Revision',revisionName+' · '+geometryRevision],['CRS / frame',crs],['Units',unitProfile],['Model',modelName+' · '+modelVersion],['Saved',lastRun]].map(([label,value])=><div key={label}><dt>{label}:</dt><dd>{value}</dd></div>)}</dl>
  <span className="badge neutral">{qualificationStatus}</span>{onRefresh&&<button className="text-button" onClick={onRefresh}>Refresh context</button>}
</div>;
