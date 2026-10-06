import {useCallback,useEffect,useState} from 'react';
import {api} from '../api';
export interface TargetModel {
  id: string;
  name: string;
  geometry_type: string;
  center_tvd_m: number;
  center_north_m: number;
  center_east_m: number;
  radius_m: number;
  tolerance_m: number;
}

export interface WellboreModel {
  id: string;
  well_id: string;
  name: string;
  uwi: string;
  wellbore_type: 'original' | 'sidetrack' | 'bypass' | 'reentry';
  sidetrack_parent_id?: string | null;
  kickoff_md_m: number;
  planned_td_m: number;
  targets: TargetModel[];
}

export interface WellModel {
  id: string;
  project_id: string;
  field_id?: string | null;
  name: string;
  uwi: string;
  wellbores: WellboreModel[];
}

export interface FieldModel {
  id: string;
  name: string;
  basin: string;
  country: string;
  wells: WellModel[];
}

export interface ProjectTreeData {
  project: {
    id: string;
    name: string;
    datum: string;
  };
  fields: FieldModel[];
  unassigned_wells: WellModel[];
}

interface ProjectTreeProps {
  projectId: string;
  activeWellId?: string;
  activeWellboreId?: string;
  onSelectWell?: (well: WellModel) => void;
  onSelectWellbore?: (wellbore: WellboreModel, well: WellModel) => void;
  className?: string;
}


export function ProjectTree({projectId,onSelectWell,onSelectWellbore,className=''}:ProjectTreeProps){
  const [tree,setTree]=useState<ProjectTreeData|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
  const [draft,setDraft]=useState<{kind:'field'|'well'|'wellbore'|'target';parent:string}|null>(null);
  const refresh=useCallback(async()=>{try{setError('');setTree(await api<ProjectTreeData>('/v1/projects/'+projectId+'/tree'));}catch(e){setError((e as Error).message);}},[projectId]);
  useEffect(()=>{let active=true;setTree(null);setDraft(null);api<ProjectTreeData>('/v1/projects/'+projectId+'/tree').then(t=>{if(active)setTree(t);}).catch(e=>{if(active)setError(e.message);});return()=>{active=false;};},[projectId]);
  const create=async(event:React.FormEvent<HTMLFormElement>)=>{event.preventDefault();if(!draft)return;setBusy(true);setError('');const f=new FormData(event.currentTarget);
    try{let path='',payload:Record<string,unknown>={name:String(f.get('name'))};
      if(draft.kind==='field'){path='/v1/projects/'+projectId+'/fields';}
      if(draft.kind==='well'){path='/v1/projects/'+projectId+'/wells';payload.field_id=draft.parent||null;}
      if(draft.kind==='wellbore'){path='/v1/wells/'+draft.parent+'/wellbores';}
      if(draft.kind==='target'){path='/v1/wellbores/'+draft.parent+'/targets';Object.assign(payload,{center_tvd_m:Number(f.get('tvd')),center_north_m:Number(f.get('north')),center_east_m:Number(f.get('east')),radius_m:Number(f.get('radius'))});}
      await api(path,{method:'POST',body:JSON.stringify(payload)});setDraft(null);await refresh();
    }catch(e){setError((e as Error).message);}finally{setBusy(false);}
  };
  const renderWell=(well:WellModel)=><details key={well.id} open><summary>{well.name} · {well.uwi}</summary><div className="tree-actions"><button className="text-button" onClick={()=>onSelectWell?.(well)}>Inspect well</button><button className="text-button" onClick={()=>setDraft({kind:'wellbore',parent:well.id})}>Add wellbore</button></div>{well.wellbores.map(wb=><details key={wb.id} open><summary>{wb.name} · {wb.wellbore_type}</summary><div className="tree-actions"><button className="text-button" onClick={()=>onSelectWellbore?.(wb,well)}>Inspect wellbore</button><button className="text-button" onClick={()=>setDraft({kind:'target',parent:wb.id})}>Add target</button></div>{wb.targets.map(t=><p key={t.id}>{t.name} · TVD {t.center_tvd_m} m · N {t.center_north_m} m · E {t.center_east_m} m · radius {t.radius_m} m</p>)}</details>)}</details>;
  return <div className={'project-tree '+className}>{error&&<div className="alert warning" role="alert">{error}</div>}{!tree?<p>Loading project tree…</p>:<><div className="tree-actions"><button className="button secondary" onClick={()=>setDraft({kind:'field',parent:projectId})}>Add field</button><button className="button secondary" onClick={()=>setDraft({kind:'well',parent:''})}>Add well</button></div>{tree.fields.map(field=><details key={field.id} open><summary>{field.name}</summary><button className="text-button" onClick={()=>setDraft({kind:'well',parent:field.id})}>Add well in field</button>{field.wells.map(renderWell)}</details>)}{tree.unassigned_wells.map(renderWell)}</>}
    {draft&&<form onSubmit={create}><h3>Create {draft.kind}</h3><label className="field-label">Name<input name="name" required maxLength={100}/></label>{draft.kind==='target'&&<div className="form-columns">{[['tvd','TVD (m)'],['north','North (m)'],['east','East (m)'],['radius','Radius (m)']].map(([name,label])=><label className="field-label" key={name}>{label}<input name={name} type="number" step="any" required min={name==='tvd'?0:name==='radius'?.001:undefined}/></label>)}</div>}<div className="heading-actions"><button className="button primary" disabled={busy}>Save {draft.kind}</button><button className="button secondary" type="button" onClick={()=>setDraft(null)}>Cancel</button></div></form>}
  </div>;
}
