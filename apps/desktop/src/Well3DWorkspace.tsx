import {useEffect,useMemo,useState} from 'react';
import {
  Box, Camera, CheckCircle2, CircleAlert, Crosshair, Database, Eye, Layers3,
  Link2, LoaderCircle, MapPin, RotateCcw, ShieldCheck, SlidersHorizontal, Target,
} from 'lucide-react';
import {api} from './api';
import type {Revision} from './GeometryWorkspace';
import type {ProjectTreeData,WellboreModel} from './components/ProjectTree';
import {
  GeoDrill3DScene,
  type CameraPreset,
  type ClosestApproach,
  type SceneLayers,
  type SpatialPoint,
  type SpatialTarget,
  type SpatialUncertainty,
} from './GeoDrill3DScene';

type Row=Record<string,number|string|null>;
type Dataset={
  id:string;kind:string;filename:string;row_count:number;source_hash:string;
  metadata:Record<string,unknown>;rows?:Row[];parquet_sha256?:string;
};
type Calculation<T=Record<string,unknown>>={
  id:string;model:string;inputs_si:Record<string,unknown>;result:T;created_at:string;
};
type UncertaintyStation={
  md_m:number;tvd_m:number;northing_m:number;easting_m:number;
  semi_major_2sigma_m:number;semi_minor_2sigma_m:number;vertical_2sigma_m:number;azimuth_major_deg:number;
};
type UncertaintyStudy={
  withheld:boolean;withholding_reason:string|null;stations:UncertaintyStation[];
  dataset_id:string;source_filename:string;source_sha256:string;geometry_revision_id:string|null;
  clearance_generated:false;equipment_authority:'none';
};
type ProximityStudy={
  closest_approach:ClosestApproach;stations:Record<string,unknown>[];min_c2c_distance_m:number;
  geometry_type:string;clearance_generated:false;clearance_statement:string;correlation_mode:string;
  correlation_applied:boolean;correlation_notes:string[];
  reference_dataset_id:string;reference_source_filename:string;reference_source_sha256:string;
  offset_dataset_id:string;offset_source_filename:string;offset_source_sha256:string;
  geometry_revision_id:string;geometry_sha256:string;coordinate_reference:string;depth_datum:string;
  north_reference:string;offset_start_nev:[number,number,number];offset_source_note:string;
  uncertainty_evidence:{
    reference_calculation_id:string|null;reference_withheld:boolean|null;
    offset_calculation_id:string|null;offset_withheld:boolean|null;both_linked_and_calculated:boolean;
  };
  equipment_authority:'none';
};

type Props={
  projectId:string;projectName:string;revision:Revision|null;survey:Dataset|null;datasets:Dataset[];
  datum:string;northReference:string;selectedMD:number|null;onSelectMD:(md:number)=>void;
  onGeometryPage:()=>void;onDataPage:()=>void;onAntiCollisionPage:()=>void;
  onError:(message:string)=>void;onNotice:(message:string)=>void;
};

const nf=(v:number|null|undefined,d=2)=>v==null||!Number.isFinite(v)?'—':v.toLocaleString('en-US',{maximumFractionDigits:d,minimumFractionDigits:d});
const numeric=(row:Row,key:string)=>typeof row[key]==='number'?Number(row[key]):Number.NaN;
const pointNorth=(p:SpatialPoint)=>Number.isFinite(p.reference_north_m)?Number(p.reference_north_m):p.north_m;
const pointEast=(p:SpatialPoint)=>Number.isFinite(p.reference_east_m)?Number(p.reference_east_m):p.east_m;

const initialLayers:SceneLayers={
  subject:true,offset:true,formations:true,casing:true,targets:true,
  subjectUncertainty:true,offsetUncertainty:true,closestApproach:true,stations:true,grid:true,
};

export function Well3DWorkspace({
  projectId,projectName,revision,survey,datasets,datum,northReference,selectedMD,onSelectMD,
  onGeometryPage,onDataPage,onAntiCollisionPage,onError,onNotice,
}:Props){
  const [referenceSource,setReferenceSource]=useState<Dataset|null>(null);
  const [offsetId,setOffsetId]=useState('');
  const [offsetSource,setOffsetSource]=useState<Dataset|null>(null);
  const [tree,setTree]=useState<ProjectTreeData|null>(null);
  const [targetWellboreId,setTargetWellboreId]=useState('');
  const [uncertaintyHistory,setUncertaintyHistory]=useState<Calculation<UncertaintyStudy>[]>([]);
  const [antiHistory,setAntiHistory]=useState<Calculation<ProximityStudy>[]>([]);
  const [study,setStudy]=useState<Calculation<ProximityStudy>|null>(null);
  const [busy,setBusy]=useState<'uncertainty'|'proximity'|''>('');
  const [cameraPreset,setCameraPreset]=useState<CameraPreset>('perspective');
  const [layers,setLayers]=useState<SceneLayers>(initialLayers);
  const [clipEnabled,setClipEnabled]=useState(false);
  const [clipTvd,setClipTvd]=useState(0);
  const [offsetNorth,setOffsetNorth]=useState(0);
  const [offsetEast,setOffsetEast]=useState(0);
  const [offsetTvd,setOffsetTvd]=useState(0);
  const [offsetFrame,setOffsetFrame]=useState('');
  const [offsetDatum,setOffsetDatum]=useState('');
  const [offsetSourceNote,setOffsetSourceNote]=useState('');
  const [offsetName,setOffsetName]=useState('');
  const [correlationMode,setCorrelationMode]=useState<'independent'|'systematic_geomagnetic'|'fully_correlated'>('independent');
  const [geomag,setGeomag]=useState({latitude_deg:'',longitude_deg:'',b_total_nt:'',dip_deg:'',declination_deg:''});

  const surveySummaries=useMemo(()=>datasets.filter(d=>d.kind==='survey'),[datasets]);
  const offsetCandidates=useMemo(()=>revision?surveySummaries.filter(d=>d.id!==revision.input.survey_dataset_id):[],[surveySummaries,revision]);

  useEffect(()=>{
    let active=true;
    setReferenceSource(null);setOffsetSource(null);setStudy(null);setUncertaintyHistory([]);setAntiHistory([]);
    setOffsetId('');setOffsetNorth(0);setOffsetEast(0);setOffsetTvd(0);setOffsetSourceNote('');setOffsetName('');
    setTargetWellboreId('');setTree(null);
    if(!revision)return()=>{active=false;};
    setOffsetFrame(revision.input.coordinate_reference);setOffsetDatum(datum);
    Promise.all([
      api<Dataset>('/projects/'+projectId+'/datasets/'+revision.input.survey_dataset_id),
      api<ProjectTreeData>('/v1/projects/'+projectId+'/tree'),
      api<Calculation<UncertaintyStudy>[]>('/projects/'+projectId+'/calculations?model=directional-uncertainty'),
      api<Calculation<ProximityStudy>[]>('/projects/'+projectId+'/calculations?model=anticollision'),
    ]).then(([source,treeData,unc,anti])=>{
      if(!active)return;
      setReferenceSource(source);setTree(treeData);setUncertaintyHistory(unc);setAntiHistory(anti);
      const saved=anti.find(c=>c.result.geometry_revision_id===revision.id&&c.result.reference_dataset_id===source.id)??null;
      if(saved){
        setStudy(saved);
        const input=saved.inputs_si;
        const offsetDataset=String(input.offset_dataset_id??'');
        setOffsetId(offsetDataset);
        const start=Array.isArray(input.offset_start_nev)?input.offset_start_nev:[0,0,0];
        setOffsetNorth(Number(start[0]??0));setOffsetEast(Number(start[1]??0));setOffsetTvd(Number(start[2]??0));
        setOffsetFrame(String(input.offset_coordinate_reference??revision.input.coordinate_reference));
        setOffsetDatum(String(input.offset_datum??datum));
        setOffsetSourceNote(String(input.offset_source_note??''));
        setOffsetName(String(input.offset_well_name??''));
        const mode=String(input.correlation_mode??'independent');
        if(mode==='independent'||mode==='systematic_geomagnetic'||mode==='fully_correlated')setCorrelationMode(mode);
        const gm=input.geomagnetic;
        if(gm&&typeof gm==='object'){
          const v=gm as Record<string,unknown>;
          setGeomag({
            latitude_deg:String(v.latitude_deg??''),longitude_deg:String(v.longitude_deg??''),
            b_total_nt:String(v.b_total_nt??''),dip_deg:String(v.dip_deg??''),declination_deg:String(v.declination_deg??''),
          });
        }
      }
      const wellbores=[...treeData.fields.flatMap(f=>f.wells.flatMap(w=>w.wellbores)),...treeData.unassigned_wells.flatMap(w=>w.wellbores)];
      if(wellbores.length===1)setTargetWellboreId(wellbores[0].id);
    }).catch(e=>{if(active)onError((e as Error).message);});
    return()=>{active=false;};
  },[projectId,revision?.id,datum]);

  useEffect(()=>{
    let active=true;setOffsetSource(null);
    if(!offsetId)return()=>{active=false;};
    api<Dataset>('/projects/'+projectId+'/datasets/'+offsetId).then(source=>{
      if(!active)return;setOffsetSource(source);
      setOffsetName(v=>v||String(source.metadata?.well_name??source.filename));
    }).catch(e=>{if(active)onError((e as Error).message);});
    return()=>{active=false;};
  },[projectId,offsetId]);

  if(!revision)return <div className="panel spatial-empty"><Box size={34}/><h2>No saved engineering geometry</h2><p>Import a survey and save a geometry revision before opening the spatial workstation.</p><button className="button primary" onClick={onGeometryPage}>Open well geometry</button></div>;

  const subjectPoints=revision.result.samples as SpatialPoint[];
  const offsetFrameReady=Boolean(offsetSource&&offsetFrame.trim()===revision.input.coordinate_reference.trim()&&offsetDatum.trim()===datum.trim()&&offsetSourceNote.trim().length>=3);
  const offsetPoints:SpatialPoint[]=offsetFrameReady?(offsetSource?.rows??[]).map(row=>({
    md_m:numeric(row,'md_m'),
    north_m:numeric(row,'north_m')+offsetNorth,
    east_m:numeric(row,'east_m')+offsetEast,
    tvd_m:numeric(row,'tvd_m')+offsetTvd,
  })).filter(p=>[p.md_m,p.north_m,p.east_m,p.tvd_m].every(Number.isFinite)):[];

  const refUncertainty=uncertaintyHistory.find(c=>c.inputs_si.dataset_id===revision.input.survey_dataset_id)??null;
  const offUncertainty=offsetId?uncertaintyHistory.find(c=>c.inputs_si.dataset_id===offsetId)??null:null;

  const subjectUncertainty:SpatialUncertainty[]=refUncertainty&&!refUncertainty.result.withheld?refUncertainty.result.stations.map(u=>({
    md_m:u.md_m,tvd_m:u.tvd_m,
    north_m:u.northing_m+revision.input.wellhead_north_m,
    east_m:u.easting_m+revision.input.wellhead_east_m,
    semi_major_2sigma_m:u.semi_major_2sigma_m,semi_minor_2sigma_m:u.semi_minor_2sigma_m,
    vertical_2sigma_m:u.vertical_2sigma_m,azimuth_major_deg:u.azimuth_major_deg,
  })):[];
  const offsetUncertainty:SpatialUncertainty[]=offUncertainty&&!offUncertainty.result.withheld&&offsetFrameReady?offUncertainty.result.stations.map(u=>({
    md_m:u.md_m,tvd_m:u.tvd_m+offsetTvd,north_m:u.northing_m+offsetNorth,east_m:u.easting_m+offsetEast,
    semi_major_2sigma_m:u.semi_major_2sigma_m,semi_minor_2sigma_m:u.semi_minor_2sigma_m,
    vertical_2sigma_m:u.vertical_2sigma_m,azimuth_major_deg:u.azimuth_major_deg,
  })):[];
  const closest=study?.result.closest_approach??null;

  const wells=tree?[...tree.fields.flatMap(f=>f.wells),...tree.unassigned_wells]:[];
  const wellbores:WellboreModel[]=wells.flatMap(w=>w.wellbores);
  const selectedWellbore=wellbores.find(w=>w.id===targetWellboreId)??null;
  const targets:SpatialTarget[]=(selectedWellbore?.targets??[]).map(t=>({
    id:t.id,name:t.name,center_tvd_m:t.center_tvd_m,center_north_m:t.center_north_m,center_east_m:t.center_east_m,
    radius_m:t.radius_m,tolerance_m:t.tolerance_m,
  }));

  const allTvds=[...subjectPoints.map(p=>p.tvd_m),...offsetPoints.map(p=>p.tvd_m)].filter(Number.isFinite);
  const maxTvd=Math.max(1,...allTvds);
  if(clipTvd===0&&maxTvd>0)setTimeout(()=>setClipTvd(maxTvd),0);

  const selected=selectedMD===null?null:subjectPoints.reduce((best,p)=>Math.abs(p.md_m-selectedMD)<Math.abs(best.md_m-selectedMD)?p:best,subjectPoints[0]);
  const subjectStale=Boolean(survey&&survey.id!==revision.input.survey_dataset_id);

  const metadataPayload=()=>{
    const result:Record<string,number|string>={tool_model:'ISCWSA MWD Rev5.11',tool_revision:'Rev5.11'};
    for(const [key,value] of Object.entries(geomag)){
      if(value.trim()==='')continue;
      const parsed=Number(value);
      if(!Number.isFinite(parsed))throw new Error(key.replaceAll('_',' ')+' must be a finite number.');
      result[key]=parsed;
    }
    return result;
  };

  const calculateUncertainty=async()=>{
    if(!referenceSource)return;
    setBusy('uncertainty');onError('');
    try{
      const metadata=metadataPayload();
      const requests=[
        api<Calculation<UncertaintyStudy>>('/projects/'+projectId+'/directional/uncertainty-study',{
          method:'POST',body:JSON.stringify({dataset_id:referenceSource.id,geometry_revision_id:revision.id,metadata}),
        }),
      ];
      if(offsetSource)requests.push(api<Calculation<UncertaintyStudy>>('/projects/'+projectId+'/directional/uncertainty-study',{
        method:'POST',body:JSON.stringify({dataset_id:offsetSource.id,metadata}),
      }));
      const results=await Promise.all(requests);
      setUncertaintyHistory(current=>[...results,...current.filter(c=>!results.some(r=>r.id===c.id))]);
      const withheld=results.filter(r=>r.result.withheld);
      onNotice(withheld.length
        ? 'Uncertainty evidence saved with explicit withholding reason. Generic ellipsoids were not substituted.'
        : 'Source-bound ISCWSA uncertainty studies saved to the project evidence trail.');
    }catch(e){onError((e as Error).message);}finally{setBusy('');}
  };

  const calculateProximity=async()=>{
    if(!referenceSource||!offsetSource)return;
    setBusy('proximity');onError('');
    try{
      const gm=metadataPayload();
      const geomagnetic=('b_total_nt' in gm&&'dip_deg' in gm)?gm:null;
      const result=await api<Calculation<ProximityStudy>>('/projects/'+projectId+'/directional/anticollision-study',{
        method:'POST',
        body:JSON.stringify({
          reference_dataset_id:referenceSource.id,
          reference_geometry_revision_id:revision.id,
          offset_dataset_id:offsetSource.id,
          offset_well_name:offsetName||offsetSource.filename,
          offset_start_nev:[offsetNorth,offsetEast,offsetTvd],
          offset_coordinate_reference:offsetFrame,
          offset_datum:offsetDatum,
          offset_source_note:offsetSourceNote,
          correlation_mode:correlationMode,
          geomagnetic,
          reference_uncertainty_calculation_id:refUncertainty?.id??null,
          offset_uncertainty_calculation_id:offUncertainty?.id??null,
        }),
      });
      setStudy(result);setAntiHistory(current=>[result,...current.filter(c=>c.id!==result.id)]);
      onNotice('Closest-approach study saved. No drilling clearance was generated.');
    }catch(e){onError((e as Error).message);}finally{setBusy('');}
  };

  const layerToggle=(key:keyof SceneLayers)=><label className="scene-layer-toggle" key={key}><input type="checkbox" checked={layers[key]} onChange={e=>setLayers(v=>({...v,[key]:e.target.checked}))}/><span>{key.replace(/([A-Z])/g,' $1').replace(/^./,c=>c.toUpperCase())}</span></label>;

  return <div className="spatial-workstation">
    <div className="spatial-titlebar">
      <div><span className="workspace-kicker">3D SPATIAL ENGINE / SOURCE-BOUND</span><h2>{projectName} · WebGL well model</h2><p>Geometry {revision.id.slice(0,8)} · equal metric scale · E / N / TVD project coordinates</p></div>
      <div className="toolbar-actions"><span className="badge green"><CheckCircle2 size={13}/>Three.js</span><span className="badge amber"><ShieldCheck size={13}/>Clearance withheld</span><button className="button secondary" onClick={onGeometryPage}>Geometry</button></div>
    </div>

    {subjectStale&&<div className="alert warning">Historical geometry: the current survey selection differs from revision {revision.id.slice(0,8)}. The 3D subject path remains bound to preserved source {revision.input.survey_dataset_id.slice(0,8)}.</div>}

    <div className="spatial-status-strip">
      <div><Database/><span>Subject source</span><strong>{referenceSource?.filename??'Loading…'}</strong></div>
      <div><Link2/><span>Offset source</span><strong>{offsetSource?.filename??'Not selected'}</strong></div>
      <div><Crosshair/><span>Closest approach</span><strong>{closest?nf(closest.c2c_distance_m)+' m':'Not calculated'}</strong></div>
      <div><ShieldCheck/><span>Uncertainty</span><strong>{refUncertainty?(refUncertainty.result.withheld?'Subject withheld':offUncertainty?(offUncertainty.result.withheld?'Offset withheld':'Linked'):'Subject only'):'Not calculated'}</strong></div>
      <div><CircleAlert/><span>Operational authority</span><strong>None</strong></div>
    </div>

    <div className="spatial-camera-bar">
      <div className="segmented spatial-presets">{([
        ['perspective','Perspective'],['plan','Plan'],['north-section','N section'],['east-section','E section']
      ] as [CameraPreset,string][]).map(([value,label])=><button key={value} className={cameraPreset===value?'selected':''} onClick={()=>setCameraPreset(value)}><Camera size={13}/>{label}</button>)}</div>
      <div className="spatial-clip"><label><input type="checkbox" checked={clipEnabled} onChange={e=>setClipEnabled(e.target.checked)}/>TVD section</label><input aria-label="3D TVD clipping depth" type="range" min="0" max={maxTvd} step={Math.max(1,maxTvd/250)} value={Math.min(clipTvd,maxTvd)} disabled={!clipEnabled} onChange={e=>setClipTvd(Number(e.target.value))}/><strong>{clipEnabled?nf(clipTvd,0)+' m':'Full depth'}</strong></div>
      <button className="button secondary" onClick={()=>{setCameraPreset('perspective');setClipEnabled(false);setLayers(initialLayers);}}><RotateCcw size={14}/>Reset scene</button>
    </div>

    <div className="spatial-main-grid">
      <section className="spatial-scene-panel">
        <GeoDrill3DScene
          subjectPoints={subjectPoints}
          offsetPoints={offsetPoints}
          formations={revision.input.formations}
          casings={revision.input.casings}
          targets={targets}
          subjectUncertainty={subjectUncertainty}
          offsetUncertainty={offsetUncertainty}
          closestApproach={closest}
          selectedMD={selectedMD}
          onSelectMD={onSelectMD}
          layers={layers}
          cameraPreset={cameraPreset}
          clipTvdM={clipEnabled?clipTvd:null}
        />
        <div className="spatial-legend">
          <span><i className="legend-subject"/>Subject</span><span><i className="legend-offset"/>Offset</span><span><i className="legend-cpa"/>Closest approach</span><span><i className="legend-target"/>Target</span><span><i className="legend-unc"/>2σ uncertainty</span>
        </div>
      </section>

      <aside className="spatial-inspector">
        <div className="inspector-heading"><Crosshair size={18}/><strong>Engineering inspector</strong></div>
        {selected?<dl className="spatial-dl">
          <div><dt>Selected MD</dt><dd>{nf(selectedMD,1)} m</dd></div>
          <div><dt>Nearest sample</dt><dd>{nf(selected.md_m,1)} m MD</dd></div>
          <div><dt>North</dt><dd>{nf(pointNorth(selected),3)} m</dd></div>
          <div><dt>East</dt><dd>{nf(pointEast(selected),3)} m</dd></div>
          <div><dt>TVD</dt><dd>{nf(selected.tvd_m,3)} m</dd></div>
        </dl>:<div className="spatial-inspector-empty"><MapPin size={22}/><span>Pick a cyan survey station in the 3D scene.</span></div>}
        <div className="inspector-divider"/>
        <h3>Closest approach</h3>
        {closest?<dl className="spatial-dl">
          <div><dt>Center-to-center</dt><dd>{nf(closest.c2c_distance_m,3)} m</dd></div>
          <div><dt>Horizontal</dt><dd>{nf(closest.horizontal_distance_m,3)} m</dd></div>
          <div><dt>Vertical</dt><dd>{nf(closest.vertical_distance_m,3)} m</dd></div>
          <div><dt>Subject MD</dt><dd>{nf(closest.ref_md_m,2)} m</dd></div>
          <div><dt>Offset MD</dt><dd>{nf(closest.offset_md_m,2)} m</dd></div>
        </dl>:<p className="muted">No saved source-bound proximity study for the selected offset.</p>}
        <div className="inspector-note"><ShieldCheck size={18}/><p><strong>No drilling clearance.</strong>{study?.result.clearance_statement??'Spatial review is informational until source, uncertainty, engineering review and operational clearance gates are independently satisfied.'}</p></div>
        {study&&<code className="spatial-record-id">Study {study.id.slice(0,8)} · geometry {study.result.geometry_revision_id.slice(0,8)}</code>}
      </aside>
    </div>

    <div className="spatial-layer-panel panel">
      <div className="panel-heading"><div><h2>Scene layers</h2><p>Only evidence-backed layers are rendered. Casing visual radius is exaggerated when the physical OD is sub-pixel at whole-well scale.</p></div><Layers3 size={20}/></div>
      <div className="scene-layer-grid">{(Object.keys(layers) as (keyof SceneLayers)[]).map(layerToggle)}</div>
      <div className="scene-reference-line"><span>Frame <strong>{revision.input.coordinate_reference}</strong></span><span>Datum <strong>{datum}</strong></span><span>North <strong>{northReference}</strong></span><span>Wellhead N/E <strong>{nf(revision.input.wellhead_north_m,2)} / {nf(revision.input.wellhead_east_m,2)} m</strong></span></div>
    </div>

    <div className="spatial-evidence-grid">
      <section className="panel spatial-evidence-card">
        <div className="panel-heading"><div><h2>Offset well evidence</h2><p>Select a second preserved survey and declare its project-frame tie-in. GeoDrill does not infer surface coordinates.</p></div><Link2 size={20}/></div>
        <label className="field-label">Preserved offset survey<select value={offsetId} onChange={e=>{setOffsetId(e.target.value);setStudy(null);setOffsetSourceNote('');setOffsetName('');}}><option value="">Select offset survey</option>{offsetCandidates.map(d=><option value={d.id} key={d.id}>{d.filename} · {d.row_count} stations</option>)}</select></label>
        {offsetSource&&<div className="source-evidence-chip"><Database size={15}/><div><strong>{offsetSource.filename}</strong><code>SHA-256 {offsetSource.source_hash}</code></div></div>}
        <div className="form-columns spatial-tie-grid">
          <label className="field-label">Offset well name<input value={offsetName} maxLength={100} onChange={e=>setOffsetName(e.target.value)}/></label>
          <label className="field-label">Surface / tie-in North (m)<input type="number" step="any" value={offsetNorth} onChange={e=>setOffsetNorth(Number(e.target.value))}/></label>
          <label className="field-label">Surface / tie-in East (m)<input type="number" step="any" value={offsetEast} onChange={e=>setOffsetEast(Number(e.target.value))}/></label>
          <label className="field-label">Tie-in TVD (m)<input type="number" step="any" value={offsetTvd} onChange={e=>setOffsetTvd(Number(e.target.value))}/></label>
        </div>
        <label className="field-label">Offset coordinate frame / CRS<input value={offsetFrame} maxLength={200} onChange={e=>setOffsetFrame(e.target.value)}/></label>
        <label className="field-label">Offset depth datum<input value={offsetDatum} maxLength={100} onChange={e=>setOffsetDatum(e.target.value)}/></label>
        <label className="field-label">Tie-in coordinate source / survey note<textarea rows={3} value={offsetSourceNote} maxLength={500} placeholder="e.g. Survey control report, revision, date and responsible source" onChange={e=>setOffsetSourceNote(e.target.value)}/></label>
        <label className="field-label">Survey-error correlation treatment<select value={correlationMode} onChange={e=>setCorrelationMode(e.target.value as typeof correlationMode)}><option value="independent">Independent</option><option value="systematic_geomagnetic">Shared systematic geomagnetic reference</option><option value="fully_correlated">Fully correlated · retained as unsupported unless evidence exists</option></select></label>
        {!offsetFrameReady&&offsetSource&&<div className="alert warning">Offset overlay withheld until its frame and datum match the saved subject geometry and a tie-in source note is recorded.</div>}
        <div className="heading-actions"><button className="button secondary" onClick={onDataPage}>Import offset survey</button><button className="button primary" disabled={!offsetSource||busy!==''} onClick={calculateProximity}>{busy==='proximity'?<LoaderCircle className="spin" size={15}/>:<Crosshair size={15}/>}Calculate & save closest approach</button></div>
      </section>

      <section className="panel spatial-evidence-card">
        <div className="panel-heading"><div><h2>Survey uncertainty evidence</h2><p>ISCWSA MWD Rev5.11 only. Missing geomagnetic inputs produce a saved withheld result; no generic ellipsoid is substituted.</p></div><ShieldCheck size={20}/></div>
        <div className="form-columns uncertainty-fields">
          <label className="field-label">Latitude (deg)<input type="number" step="any" value={geomag.latitude_deg} onChange={e=>setGeomag(v=>({...v,latitude_deg:e.target.value}))}/></label>
          <label className="field-label">Longitude (deg)<input type="number" step="any" value={geomag.longitude_deg} onChange={e=>setGeomag(v=>({...v,longitude_deg:e.target.value}))}/></label>
          <label className="field-label">B-total (nT)<input type="number" step="any" value={geomag.b_total_nt} onChange={e=>setGeomag(v=>({...v,b_total_nt:e.target.value}))}/></label>
          <label className="field-label">Dip (deg)<input type="number" step="any" value={geomag.dip_deg} onChange={e=>setGeomag(v=>({...v,dip_deg:e.target.value}))}/></label>
          <label className="field-label">Declination (deg)<input type="number" step="any" value={geomag.declination_deg} onChange={e=>setGeomag(v=>({...v,declination_deg:e.target.value}))}/></label>
        </div>
        <button className="button primary" disabled={!referenceSource||busy!==''} onClick={calculateUncertainty}>{busy==='uncertainty'?<LoaderCircle className="spin" size={15}/>:<ShieldCheck size={15}/>}Calculate & save uncertainty {offsetSource?'for both surveys':'for subject'}</button>
        <div className="uncertainty-status-grid">
          <div className={refUncertainty&&!refUncertainty.result.withheld?'ok':'warn'}><strong>Subject</strong><span>{refUncertainty?(refUncertainty.result.withheld?'Withheld':'2σ ellipsoids available'):'Not calculated'}</span>{refUncertainty?.result.withholding_reason&&<small>{refUncertainty.result.withholding_reason}</small>}</div>
          <div className={offUncertainty&&!offUncertainty.result.withheld?'ok':'warn'}><strong>Offset</strong><span>{offUncertainty?(offUncertainty.result.withheld?'Withheld':'2σ ellipsoids available'):offsetSource?'Not calculated':'No offset selected'}</span>{offUncertainty?.result.withholding_reason&&<small>{offUncertainty.result.withholding_reason}</small>}</div>
        </div>
        <div className="inspector-note"><CircleAlert size={18}/><p>Uncertainty ellipsoids are statistical position bounds, not collision clearance. Tool-model evidence and independent engineering review remain separate gates.</p></div>
      </section>

      <section className="panel spatial-evidence-card">
        <div className="panel-heading"><div><h2>Subsurface targets</h2><p>Targets come from the persisted project hierarchy and are rendered only for the explicitly selected wellbore.</p></div><Target size={20}/></div>
        <label className="field-label">Target wellbore<select value={targetWellboreId} onChange={e=>setTargetWellboreId(e.target.value)}><option value="">Do not render project targets</option>{wells.flatMap(w=>w.wellbores.map(wb=><option value={wb.id} key={wb.id}>{w.name} / {wb.name}</option>))}</select></label>
        {selectedWellbore?<div className="target-list">{selectedWellbore.targets.map(t=><div key={t.id}><MapPin size={14}/><span><strong>{t.name}</strong> · TVD {nf(t.center_tvd_m,1)} m · radius {nf(t.radius_m,1)} m · tolerance ±{nf(t.tolerance_m,1)} m</span></div>)}{!selectedWellbore.targets.length&&<p className="muted">The selected wellbore has no persisted targets.</p>}</div>:<p className="muted">Choose a wellbore to establish the target-layer identity explicitly.</p>}
        <button className="button secondary" onClick={onAntiCollisionPage}><Eye size={15}/>Open Anti-Collision readiness view</button>
      </section>
    </div>

    {study&&<section className="panel anti-study-table">
      <div className="panel-heading"><div><h2>Saved anti-collision evidence</h2><p>Calculation {study.id.slice(0,8)} · {new Date(study.created_at).toUTCString()} · correlation {study.result.correlation_mode.replaceAll('_',' ')}</p></div><span className="badge amber">No clearance</span></div>
      <div className="spatial-result-grid">
        <div><span>Minimum C2C</span><strong>{nf(study.result.min_c2c_distance_m,3)} m</strong></div>
        <div><span>Geometry</span><strong>{study.result.geometry_type.replaceAll('_',' ')}</strong></div>
        <div><span>Subject source</span><code>{study.result.reference_source_sha256.slice(0,16)}…</code></div>
        <div><span>Offset source</span><code>{study.result.offset_source_sha256.slice(0,16)}…</code></div>
        <div><span>Both uncertainties linked</span><strong>{study.result.uncertainty_evidence.both_linked_and_calculated?'Yes':'No / withheld'}</strong></div>
        <div><span>Equipment authority</span><strong>{study.result.equipment_authority}</strong></div>
      </div>
      {study.result.correlation_notes.map(n=><p className="inset-note" key={n}>{n}</p>)}
      <p className="inset-note">{study.result.clearance_statement}</p>
    </section>}

    {antiHistory.length>1&&<details className="panel spatial-history"><summary>Earlier preserved anti-collision studies ({antiHistory.length-1})</summary><div className="table-scroll"><table><thead><tr><th>Created</th><th>Offset source</th><th>Minimum C2C</th><th>Geometry</th><th/></tr></thead><tbody>{antiHistory.filter(c=>c.id!==study?.id).map(c=><tr key={c.id}><td>{new Date(c.created_at).toISOString().slice(0,19).replace('T',' ')}</td><td>{c.result.offset_source_filename}</td><td>{nf(c.result.min_c2c_distance_m,3)} m</td><td>{c.result.geometry_type.replaceAll('_',' ')}</td><td><button className="text-button" onClick={()=>setStudy(c)}>Open</button></td></tr>)}</tbody></table></div></details>}
  </div>;
}
