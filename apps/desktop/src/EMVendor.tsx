import {useEffect,useState} from 'react';
import {engineeringApi,scopeQuery,type EngineeringScope} from './api';
import {CalculationFreshness} from './CalculationFreshness';
import type {Revision} from './GeometryWorkspace';

type Interval={lower:number;upper:number;meaning:string};
type Display={rh_ohm_m:number|null;rv_ohm_m:number|null;boundary_distance_m:number|null;rh_interval:Interval|null;rv_interval:Interval|null;boundary_interval:Interval|null;boundary_reference:string|null};
type Sample={source_index:number;native_md_m:number;aligned_md_m:number;status:string;reasons:string[];display:Display|null;receipt_delay_s:number|null;supplied:Record<string,unknown>};
type Source={id:string;kind:string;filename:string;source_hash:string;metadata:Record<string,unknown>;row_count:number};
type Study={id:string;created_at:string;inputs_si:Record<string,unknown>;result:{status:string;origin:string;model:string;eligible_count:number;withheld_count:number;missing_resistivity_interval_count:number;source_sha256:string;geometry_sha256:string;tool:Record<string,unknown>;source_reference:string;data_rights_note:string;integration_readiness:Record<string,boolean>;warnings:string[];rows:Sample[]}};
type Props=EngineeringScope & {project:{id:string;datum:string;origin:string};online:boolean;onError:(s:string)=>void;onNotice:(s:string)=>void};
const format=(x:number|null,d=3)=>x==null?'Not supplied':x.toLocaleString('en-US',{maximumFractionDigits:d});
function ResultPlot({rows,boundary=false}:{rows:Sample[];boundary?:boolean}){
  const eligible=rows.filter(r=>r.display!==null&&(boundary?r.display!.boundary_distance_m:r.display!.rh_ohm_m)!==null);
  if(!eligible.length)return <div className="empty-inline">No eligible supplied {boundary?'boundary distances':'horizontal resistivities'}.</div>;
  const point=(r:Sample)=>boundary?r.display!.boundary_distance_m!:r.display!.rh_ohm_m!;
  const interval=(r:Sample)=>boundary?r.display!.boundary_interval:r.display!.rh_interval;
  const values=eligible.flatMap(r=>interval(r)?[point(r),interval(r)!.lower,interval(r)!.upper]:[point(r)]);
  let low=Math.min(...values),high=Math.max(...values);
  const pad=Math.max((high-low)*.1,Math.abs(high)*.05,.1);
  low-=pad;high+=pad;if(!boundary)low=Math.max(0,low);
  const depths=rows.map(r=>r.aligned_md_m),left=62,right=24,top=24,bottom=45,width=600,height=280;
  const start=Math.min(...depths),end=Math.max(...depths);
  const x=(v:number)=>left+(v-start)/Math.max(end-start,1)*(width-left-right);
  const y=(v:number)=>top+(high-v)/(high-low)*(height-top-bottom);
  return <svg viewBox={'0 0 '+width+' '+height} role="img" aria-label={boundary?'Supplied boundary distances and supplied ranges versus aligned measured depth':'Supplied horizontal resistivity and supplied ranges versus aligned measured depth'}>
    {[0,1,2,3].map(i=>{const v=low+(high-low)*i/3;return <g key={i}><line x1={left} x2={width-right} y1={y(v)} y2={y(v)} stroke="#e3e9e5"/><text x={left-8} y={y(v)+4} textAnchor="end">{format(v,1)}</text></g>;})}
    {eligible.map(r=>{const range=interval(r);return <g key={r.source_index}>{range&&<><line x1={x(r.aligned_md_m)} x2={x(r.aligned_md_m)} y1={y(range.lower)} y2={y(range.upper)} stroke="#4f8d80" strokeWidth="2"/><line x1={x(r.aligned_md_m)-5} x2={x(r.aligned_md_m)+5} y1={y(range.lower)} y2={y(range.lower)} stroke="#4f8d80"/><line x1={x(r.aligned_md_m)-5} x2={x(r.aligned_md_m)+5} y1={y(range.upper)} y2={y(range.upper)} stroke="#4f8d80"/></>}<circle cx={x(r.aligned_md_m)} cy={y(point(r))} r="4" fill="#216f5d"><title>Native MD {r.native_md_m}; aligned MD {r.aligned_md_m}; supplied value {point(r)}{range?'; '+range.meaning:'; uncertainty not supplied'}</title></circle></g>;})}
    {[0,1,2,3].map(i=>{const v=start+(end-start)*i/3;return <text x={x(v)} y={height-bottom+20} textAnchor="middle" key={i}>{format(v,0)}</text>;})}
    <text x={width/2} y={height-7} textAnchor="middle">Aligned MD (m)</text><text x={left} y={15}>{boundary?'Signed supplied distance (m)':'Horizontal resistivity (ohm.m)'}</text>
  </svg>;
}
export function EMVendor({project,online,onError,onNotice,wellboreId,trajectoryRole}:Props){
  const api=engineeringApi({wellboreId,trajectoryRole});
  const scoped=scopeQuery({wellboreId,trajectoryRole});
  const base='/projects/'+project.id;
  const [sources,setSources]=useState<Source[]>([]),[source,setSource]=useState('');
  const [revisions,setRevisions]=useState<Revision[]>([]),[revision,setRevision]=useState('');
  const [history,setHistory]=useState<Study[]>([]),[result,setResult]=useState<Study|null>(null);
  const [study,setStudy]=useState(''),[datum,setDatum]=useState(project.datum),[alignment,setAlignment]=useState('unverified'),[offset,setOffset]=useState('0'),[alignmentNote,setAlignmentNote]=useState(''),[reviewNote,setReviewNote]=useState('');
  const [file,setFile]=useState<File|null>(null),[busy,setBusy]=useState(false),[dirty,setDirty]=useState(false);
  useEffect(()=>{let active=true;Promise.all([api<Source[]>(base+'/datasets'),api<Revision[]>(base+'/engineering-revisions?module=M1'+scoped),api<Study[]>(base+'/calculations?model=em_vendor'+scoped)]).then(([s,r,h])=>{if(active){setSources(s.filter(x=>x.kind==='em_vendor'));setSource(s.find(x=>x.kind==='em_vendor')?.id??'');setRevisions(r);setRevision(r[0]?.id??'');setHistory(h);}}).catch(e=>{if(active)onError(e.message);});return()=>{active=false;};},[base,scoped]);
  const refreshSources=async(id:string)=>{setSources((await api<Source[]>(base+'/datasets')).filter(x=>x.kind==='em_vendor'));setSource(id);setAlignment('unverified');setAlignmentNote('');setReviewNote('');setDirty(true);};
  const example=async()=>{setBusy(true);try{const imported=await api<{id:string}>(base+'/examples/em-vendor',{method:'POST'});await refreshSources(imported.id);setStudy('Synthetic vendor-result review');setAlignment('supplied_confirmed');setOffset('0');setAlignmentNote('Generated native MD aligned with the synthetic project; no tool offset applied');setReviewNote('Synthetic software example only; no physical EM instrument, forward solve or qualified inversion');onNotice('Synthetic import loaded with vendor quality, missing values and unqualified tool metadata.');}catch(e){onError((e as Error).message);}finally{setBusy(false);}};
  const selected=sources.find(x=>x.id===source);
  return <><CalculationFreshness projectId={project.id} calculationId={result?.id}/><div className="scope-note"><div><strong>M5 · Imported EM vendor results</strong><p>Inspect supplied resistivity and boundary interpretations against saved well geometry. Acquisition time, receipt delay, uncertainty and tool metadata stay attached to the source. Native EM inversion requires a qualified instrument and forward model.</p></div></div>
    <section className="panel em-import"><div className="panel-heading"><div><h2>Preserve the vendor interchange</h2><p>Strict JSON contract · maximum 1,000 native samples · original file and SHA-256 retained</p></div><a className="button secondary" href={'/api'+base+'/em-vendor/template'} download>Download example JSON</a></div>
      <form className="em-upload" onSubmit={async e=>{e.preventDefault();if(!file)return;setBusy(true);onError('');try{const body=new FormData();body.append('file',file);const imported=await api<{id:string;duplicate:boolean}>(base+'/em-vendor/imports',{method:'POST',body});await refreshSources(imported.id);onNotice(imported.duplicate?'Identical source already preserved.':'EM vendor source preserved. Confirm depth alignment before review.');}catch(e){onError((e as Error).message);}finally{setBusy(false);}}}>
        <label className="field-label">Vendor result JSON<input type="file" accept=".json,application/json" required onChange={e=>setFile(e.target.files?.[0]??null)}/></label><button className="button primary" disabled={busy||!online||!file}>Import vendor results</button>
        {project.origin==='synthetic'&&<button type="button" className="button secondary" disabled={busy||!online} onClick={example}>Load synthetic EM example</button>}
      </form><p className="well-note">The example declares its synthetic origin. Historical imports must match this project's well name and datum and must truthfully identify their origin, source and data rights.</p>
    </section>
    <section className="panel em-editor"><div className="panel-heading"><div><h2>Depth alignment & review context</h2><p>Keep measurement-reference MD separate from tool-to-bit spacing.</p></div></div>
      <form onSubmit={async e=>{e.preventDefault();setBusy(true);onError('');try{const inputs={study_name:study,dataset_id:source,geometry_revision_id:revision,depth_datum:datum,alignment_status:alignment,md_offset_m:Number(offset),depth_alignment_note:alignmentNote,reviewer_note:reviewNote};const saved=await api<Study>(base+'/calculations/em-vendor',{method:'POST',body:JSON.stringify(inputs)});setResult(saved);setHistory(await api<Study[]>(base+'/calculations?model=em_vendor'+scoped));setDirty(false);onNotice('Vendor review saved with original evidence and geometry hashes.');}catch(e){onError((e as Error).message);}finally{setBusy(false);}}}>
        <div className="lab-fields"><label className="field-label">Study name<input required maxLength={100} minLength={3} value={study} onChange={e=>{setStudy(e.target.value);setDirty(true);}}/></label>
          <label className="field-label">EM vendor source<select required value={source} onChange={e=>{setSource(e.target.value);setAlignment('unverified');setAlignmentNote('');setReviewNote('');setDirty(true);}}><option value="">Import a source</option>{sources.map(s=><option key={s.id} value={s.id}>{s.filename+' · '+s.row_count+' samples'}</option>)}</select></label>
          <label className="field-label">Geometry context<select required value={revision} onChange={e=>{setRevision(e.target.value);setAlignment('unverified');setAlignmentNote('');setDirty(true);}}><option value="">Save M1 geometry first</option>{revisions.map(r=><option key={r.id} value={r.id}>{r.id.slice(0,8)+' · '+r.change_note}</option>)}</select></label>
          <label className="field-label">Declared EM MD datum<input required value={datum} onChange={e=>{setDatum(e.target.value);setAlignment('unverified');setDirty(true);}}/></label>
          <label className="field-label">Depth alignment state<select value={alignment} onChange={e=>{setAlignment(e.target.value);setDirty(true);}}><option value="unverified">Unverified — withhold interpretations</option><option value="supplied_confirmed">Supplied alignment confirmed</option></select></label>
          <label className="field-label">MD alignment offset (m)<input required type="number" step="any" min={-1000} max={1000} value={offset} onChange={e=>{setOffset(e.target.value);setAlignment('unverified');setDirty(true);}}/></label>
          <label className="field-label">Depth alignment evidence<textarea required minLength={3} maxLength={500} value={alignmentNote} onChange={e=>{setAlignmentNote(e.target.value);setDirty(true);}}/></label>
          <label className="field-label">Review note<textarea required minLength={3} maxLength={1000} value={reviewNote} onChange={e=>{setReviewNote(e.target.value);setDirty(true);}}/></label>
        </div><button className="button primary" disabled={busy||!online||!source||!revision}>{busy?'Saving review…':'Save EM review'}</button>
      </form>{selected&&<details className="calculation-evidence"><summary>Selected source and supplied tool metadata</summary><pre>{JSON.stringify({source_sha256:selected.source_hash,...selected.metadata},null,2)}</pre></details>}
    </section>
    {result&&<section className="panel em-result"><div className="panel-heading"><div><h2>Preserved vendor review <span className="badge neutral">{result.result.origin}</span></h2><p>{String(result.inputs_si.study_name)} · {result.result.eligible_count} displayed / {result.result.withheld_count} withheld · {result.result.missing_resistivity_interval_count} samples lack a supplied resistivity interval</p></div><span className="badge amber">No interpretation approval</span></div>
      {dirty&&<p className="alert">Inputs have changed. This result retains the original saved inputs and source.</p>}
      <div className="em-plots"><div><h3>Horizontal resistivity</h3><ResultPlot rows={result.result.rows}/></div><div><h3>Boundary distance in its supplied reference</h3><ResultPlot rows={result.result.rows} boundary/></div></div><p className="well-note">Bars show supplied ranges with their original meaning. Points use native sample spacing; missing and withheld values are not connected.</p>
      <div className="em-readiness">{Object.entries(result.result.integration_readiness).map(([k,v])=><div key={k}><span className={'badge '+(v?'neutral':'amber')}>{v?'Supplied':'Missing / unverified'}</span><span>{k.replaceAll('_',' ')}</span></div>)}</div>
      <div className="table-scroll"><table><thead><tr><th>Native / aligned MD (m)</th><th>State</th><th>Rh / Rv (ohm.m)</th><th>Signed distance (m)</th><th>Receipt delay (s)</th><th>Evidence / reasons</th></tr></thead><tbody>{result.result.rows.slice(0,100).map(r=><tr key={r.source_index}><td>{format(r.native_md_m)+' / '+format(r.aligned_md_m)}</td><td>{r.status.replaceAll('_',' ')}</td><td>{r.display?format(r.display.rh_ohm_m)+' / '+format(r.display.rv_ohm_m):'Withheld'}</td><td>{r.display?format(r.display.boundary_distance_m):'Withheld'}</td><td>{format(r.receipt_delay_s)}</td><td><details><summary>{r.reasons.join(' ')||'Supplied evidence'}</summary><pre>{JSON.stringify({supplied:r.supplied,display:r.display},null,2)}</pre></details></td></tr>)}</tbody></table></div>
      {result.result.rows.length>100&&<p className="well-note">First 100 rows displayed; all native samples remain in the saved result and report.</p>}
      <ul className="model-warnings">{result.result.warnings.map(w=><li key={w}>{w}</li>)}</ul><details className="calculation-evidence"><summary>Saved inputs, source hashes & tool evidence</summary><pre>{JSON.stringify({id:result.id,created_at:result.created_at,inputs:result.inputs_si,source_sha256:result.result.source_sha256,geometry_sha256:result.result.geometry_sha256,tool:result.result.tool,source_reference:result.result.source_reference,data_rights_note:result.result.data_rights_note},null,2)}</pre></details>
    </section>}
    <section className="panel"><div className="panel-heading"><div><h2>Saved EM reviews</h2><p>Reopen original results and their source evidence.</p></div></div>{history.length?<div className="em-history">{history.map(h=><button className="button secondary" key={h.id} onClick={()=>{setResult(h);setDirty(true);}}>{String(h.inputs_si.study_name)+' · '+h.result.eligible_count+'/'+h.result.rows.length+' displayed · '+new Date(h.created_at).toLocaleString()}</button>)}</div>:<div className="empty-inline">No saved EM reviews.</div>}</section>
  </>;
}
