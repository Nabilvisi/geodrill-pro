import {useEffect,useRef,useState} from 'react';
import {api} from './api';

type Citation={domain:string;entity_id:string;title:string;sha256_hash:string;revision_id:string|null;interval_or_depth:string|null;matched_snippet:string;model_version:string|null;created_at:string|null};
type SearchResult={query:string;project_id:string;authorized:boolean;authorization_error:string|null;abstention:boolean;abstention_reason:string|null;answer_summary:string|null;citations:Citation[];conflicting_versions:{parameter_name:string;conflict_summary:string;revisions:Record<string,unknown>[]}[]};
type Props={project:{id:string};online:boolean;onError:(message:string)=>void};
function preview(value:unknown):unknown{
  if(Array.isArray(value))return value.length>12?{retained_records:value.length,display:'First 12 records',records:value.slice(0,12).map(preview)}:value.map(preview);
  if(value&&typeof value==='object')return Object.fromEntries(Object.entries(value).map(([key,v])=>[key,preview(v)]));
  return value;
}
const hashBasis=(domain:string)=>domain==='calculations'?'Canonical complete saved calculation':domain==='geometry'?'Immutable geometry revision':domain==='datasets'?'Original imported file bytes':domain==='programmes'?'Programme version content':'Supplied evidence reference';
export function EvidenceSearch({project,online,onError}:Props){
  const [query,setQuery]=useState(''),[busy,setBusy]=useState(false),[result,setResult]=useState<SearchResult|null>(null),[record,setRecord]=useState<{title:string;value:unknown}|null>(null);
  const generation=useRef(0);const base='/projects/'+project.id;
  useEffect(()=>()=>{generation.current++;},[base]);
  async function inspect(c:Citation){
    const seq=++generation.current;setBusy(true);setRecord(null);onError('');
    try{
      let value:unknown;
      if(c.domain==='datasets')value=await api(base+'/datasets/'+encodeURIComponent(c.entity_id));
      else if(c.domain==='geometry')value=await api(base+'/geometry/'+encodeURIComponent(c.entity_id));
      else if(c.domain==='calculations'){
        const records=await api<{id:string}[]>(base+'/calculations');value=records.find(r=>r.id===c.entity_id);
        if(!value)throw new Error('Cited saved calculation is unavailable in this project.');
      }else if(c.domain==='programmes')value=await api(base+'/programmes/'+encodeURIComponent(c.entity_id));
      else throw new Error('This citation has no supported saved-record view.');
      if(seq===generation.current)setRecord({title:c.title,value});
    }catch(error){if(seq===generation.current)onError((error as Error).message);}finally{if(seq===generation.current)setBusy(false);}
  }
  return <><div className="scope-note"><div><strong>Search the selected project's preserved evidence</strong><p>Search filenames, study names, identifiers and geometry notes. Citations identify stored records and their hash basis. Historical geometry differences remain visible; these matches do not independently qualify engineering conclusions.</p></div></div>
    <section className="panel"><form onSubmit={async e=>{e.preventDefault();const q=query.trim();if(!q)return;const seq=++generation.current;setBusy(true);setResult(null);setRecord(null);onError('');try{const value=await api<SearchResult>(base+'/evidence/search?q='+encodeURIComponent(q));if(seq===generation.current)setResult(value);}catch(error){if(seq===generation.current)onError((error as Error).message);}finally{if(seq===generation.current)setBusy(false);}}}>
      <label className="field-label">Search project evidence<input aria-label="Search project evidence" value={query} maxLength={500} required placeholder="Study name, file, casing or record ID" onChange={e=>{generation.current++;setQuery(e.target.value);setResult(null);setRecord(null);setBusy(false);}}/></label>
      <button type="submit" className="button primary" disabled={busy||!online||!query.trim()}>{busy?'Loading evidence…':'Search preserved evidence'}</button>
    </form></section>
    {result&&<><section className="panel" aria-live="polite"><div className="panel-heading"><div><h2>Results for “{result.query}”</h2><p>{result.answer_summary??'No matching evidence summary is available.'}</p></div><span className={'badge '+(result.abstention?'amber':'neutral')}>{result.abstention?'Answer withheld':'Evidence matches'}</span></div>{result.abstention_reason&&<p>{result.abstention_reason}</p>}{result.authorization_error&&<p>{result.authorization_error}</p>}</section>
      {result.conflicting_versions.map((conflict,i)=><section className="panel" key={i}><h2>{conflict.parameter_name}</h2><p>{conflict.conflict_summary}</p><div className="table-scroll"><table><thead><tr><th>Revision</th><th>Shoe MD (m)</th><th>Inside diameter (m)</th><th>Change note</th><th>SHA-256</th></tr></thead><tbody>{conflict.revisions.map((r,j)=><tr key={j}><td>{String(r.revision_id)}</td><td>{String(r.shoe_md_m)}</td><td>{String(r.id_m)}</td><td>{String(r.change_note??'')}</td><td><code>{String(r.sha256)}</code></td></tr>)}</tbody></table></div></section>)}
      {result.citations.map((c,i)=><section className="panel" key={c.domain+c.entity_id+(c.revision_id??'')+i}><div className="panel-heading"><div><h2>{c.title}</h2><p>{c.matched_snippet}</p></div><span className="badge neutral">{c.domain}</span></div><dl className="research-evidence"><div><dt>Record</dt><dd>{c.entity_id}</dd></div><div><dt>Revision</dt><dd>{c.revision_id??'Not supplied'}</dd></div><div><dt>Scope</dt><dd>{c.interval_or_depth??'Not supplied'}</dd></div><div><dt>Model version</dt><dd>{c.model_version??'Not applicable'}</dd></div><div><dt>SHA-256 basis</dt><dd>{hashBasis(c.domain)}</dd></div><div><dt>SHA-256</dt><dd><code>{c.sha256_hash}</code></dd></div></dl><button type="button" className="button secondary" disabled={busy||!online} onClick={()=>inspect(c)}>Inspect cited record</button></section>)}
    </>}
    {record&&<section className="panel"><h2>Cited record · {record.title}</h2><p>Preview of the stored record. Large arrays show the first 12 entries; the complete record is retained by the workspace and fixed reports. An imported-file hash identifies original source bytes, not this JSON view.</p><pre className="research-json">{JSON.stringify(preview(record.value),null,2)}</pre></section>}
  </>;
}
