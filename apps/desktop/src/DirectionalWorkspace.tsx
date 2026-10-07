import {useEffect, useState} from 'react';
import {api} from './api';
import type {Revision} from './GeometryWorkspace';
import {ProjectTree, type WellboreModel, type WellModel} from './components/ProjectTree';
import {WellboreWorkspace, type WellboreContext, type TrajectoryRole} from './WellboreWorkspace';

export type SurveySource = {id:string;filename:string;source_hash:string;rows?:Record<string,number|string|null>[]};
type Props = {projectId:string;projectName:string;datum:string;northReference:string;survey:SurveySource|null;revision:Revision|null;selectedMD:number|null;onSelectMD:(md:number)=>void;onError:(s:string)=>void;onGeometryPage:()=>void;onDataPage:()=>void;on3DPage:()=>void;wellboreId?:string;context:WellboreContext|null;datasets:{id:string;kind:string;filename:string}[];onSelectWellbore:(wb:WellboreModel,well:WellModel)=>void;onRole:(r:TrajectoryRole)=>void;onRefresh:()=>void;onLegacy:()=>void};
type Result = Record<string,unknown>;
const fmt=(n:unknown)=>typeof n==='number'&&Number.isFinite(n)?n.toLocaleString('en-US',{maximumFractionDigits:3}):'—';

export function DirectionalWorkspace({projectId,projectName,datum,northReference,survey,revision,selectedMD,onSelectMD,onError,onGeometryPage,onDataPage,on3DPage,wellboreId,context,datasets,onSelectWellbore,onRole,onRefresh,onLegacy}:Props){
  const [metadata,setMetadata]=useState('{}'),[result,setResult]=useState<Result|null>(null),[busy,setBusy]=useState(false);
  const rows=survey?.rows??[];
  const boundRevision=revision?.input.survey_dataset_id===survey?.id?revision:null;
  const binding=projectId+':'+(survey?.id??'')+':'+(revision?.id??'');
  useEffect(()=>{setResult(null);setMetadata('{}');},[binding]);
  const runUncertainty=async()=>{setBusy(true);onError('');try{
    const context=JSON.parse(metadata);
    if(!context||Array.isArray(context)||typeof context!=='object')throw new Error('Survey metadata must be a JSON object.');
    const response=await api<Result>('/projects/'+projectId+'/directional/uncertainty',{method:'POST',body:JSON.stringify({...context,stations:rows.map(r=>({md_m:r.md_m,inclination_deg:Number(r.inclination_rad)*180/Math.PI,azimuth_deg:Number(r.azimuth_rad)*180/Math.PI})),tool_model:'ISCWSA MWD Rev5.11',tool_revision:'Rev5.11',source_label:'iscwsa_calculated'})});
    setResult({...response,source_dataset_id:survey?.id,source_hash:survey?.source_hash,geometry_revision_id:boundRevision?.id??null});
  }catch(e){onError((e as Error).message);}finally{setBusy(false);}};
  const points=boundRevision?.result.samples??rows.map(r=>({md_m:Number(r.md_m),east_m:Number(r.east_m),north_m:Number(r.north_m),tvd_m:Number(r.tvd_m),elevation_m:0}));
  const east=points.map(p=>p.east_m),north=points.map(p=>p.north_m);
  const minE=Math.min(0,...east),maxE=Math.max(1,...east),minN=Math.min(0,...north),maxN=Math.max(1,...north);
  const scale=Math.min(520/Math.max(1,maxE-minE),270/Math.max(1,maxN-minN));
  const project=(p:{east_m:number;north_m:number})=>[40+(p.east_m-minE)*scale,310-(p.north_m-minN)*scale];
  const picked=selectedMD===null?null:points.reduce<typeof points[number]|null>((best,p)=>!best||Math.abs(p.md_m-selectedMD)<Math.abs(best.md_m-selectedMD)?p:best,null);
  return <div className="directional-workspace">
    <div className="panel"><div className="panel-heading"><div><h2>Project / well / wellbore</h2><p>{projectName} · {datum} · {northReference} north</p></div><button className="button secondary" onClick={onLegacy}>Use legacy project survey</button></div><ProjectTree projectId={projectId} activeWellboreId={wellboreId} onSelectWellbore={onSelectWellbore}/><p className="muted">Select a wellbore to use its saved source revisions. Project sources are assigned only through explicit adoption.</p></div>
    {wellboreId&&(context?<WellboreWorkspace key={wellboreId+context.trajectory_type} context={context} datasets={datasets} datum={datum} northReference={northReference} onRefresh={onRefresh} onError={onError} onRole={onRole} selectedMD={selectedMD} onSelectMD={onSelectMD}/>:<div className="panel"><p>Loading selected wellbore revisions…</p><button className="button secondary" onClick={onRefresh}>Reload wellbore</button></div>)}
    <div className="panel"><div className="panel-heading"><div><h2>Directional survey</h2><p>{survey?.filename??'No imported survey'} · {rows.length} source stations · SI kernel, degrees displayed</p></div><button className="button secondary" onClick={onDataPage}>Import / select survey</button></div>
      {survey&&<p className="record-id">Source SHA-256 <code>{survey.source_hash}</code></p>}
      <div className="table-scroll"><table className="data-table"><thead><tr>{['MD (m)','Inclination (°)','Azimuth (°)','TVD (m)','North displacement (m)','East displacement (m)','DLS (°/30 m)','Selection'].map(s=><th key={s}>{s}</th>)}</tr></thead><tbody>{rows.map((r,i)=><tr key={i} className={Number(r.md_m)===selectedMD?'selected-row':''}><td>{fmt(r.md_m)}</td><td>{fmt(Number(r.inclination_rad)*180/Math.PI)}</td><td>{fmt(Number(r.azimuth_rad)*180/Math.PI)}</td><td>{fmt(r.tvd_m)}</td><td>{fmt(r.north_m)}</td><td>{fmt(r.east_m)}</td><td>{fmt(Number(r.dogleg_rad_m)*180/Math.PI*30)}</td><td><button className="text-button" onClick={()=>onSelectMD(Number(r.md_m))}>Select MD {fmt(r.md_m)}</button></td></tr>)}</tbody></table></div>
      {!rows.length&&<p>Import a survey with explicit units to calculate a trajectory.</p>}
    </div>
    <div className="panel"><div className="panel-heading"><div><h2>Plan view · kernel geometry</h2><p>{boundRevision?'Saved geometry '+boundRevision.id.slice(0,8):'Imported survey displacement; local origin'} · North up, East right</p></div><div className="heading-actions"><button className="button secondary" onClick={onGeometryPage}>Edit / save geometry</button><button className="button secondary" onClick={on3DPage}>Open 3D model</button></div></div>
      {revision&&!boundRevision&&<p className="alert warning">The saved geometry references another survey. Save a geometry revision for the active survey before treating that model as current.</p>}
      <svg viewBox="0 0 620 350" className="engineering-plan" role="img" aria-label="Plan view of the imported survey with the selected measured depth"><path d={points.map((p,i)=>{const [x,y]=project(p);return (i?'L':'M')+x+','+y;}).join(' ')} fill="none" stroke="#0B3D91" strokeWidth="3"/>{picked&&<circle cx={project(picked)[0]} cy={project(picked)[1]} r="6" fill="#F97316"/>}<text x="40" y="337">East (m) · equal spatial scale</text></svg>
      {selectedMD!==null&&<p>Selected MD {fmt(selectedMD)} m{picked&&' · nearest rendered sample '+fmt(picked.md_m)+' m'}</p>}
    </div>
    {!wellboreId&&<div className="panel"><h2>Survey uncertainty · research diagnostic</h2><p>The pinned ISCWSA MWD Rev5.11 model requires declared tool applicability and geomagnetic reference inputs. Missing evidence withholds the calculation. These values do not establish field qualification.</p><label className="field-label">Geomagnetic and survey metadata (JSON)<textarea aria-label="Survey uncertainty metadata JSON" rows={7} value={metadata} onChange={e=>{setMetadata(e.target.value);setResult(null);}}/></label><button className="button primary" disabled={busy||rows.length<2} onClick={runUncertainty}>{busy?'Calculating…':'Calculate survey uncertainty'}</button>{result&&result.source_dataset_id===survey?.id&&result.geometry_revision_id===(boundRevision?.id??null)&&<><p className="alert warning">{result.withheld?'Withheld: '+String(result.withholding_reason):'Calculated research diagnostic · drilling clearance remains withheld.'}</p><details><summary>Calculation output / covariance evidence</summary><pre>{JSON.stringify(result,null,2)}</pre></details></>}
    </div>}
    {!wellboreId&&<div className="panel"><h2>Anti-collision</h2><p>Select a wellbore to save an explicit offset comparison. Drilling clearance is withheld.</p><span className="badge amber">Not analysed · no clearance</span></div>}
  </div>;
}
