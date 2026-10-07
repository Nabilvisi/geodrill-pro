import React from 'react';
import {
  ArrowRight, CheckCircle2, CircleAlert, Database, Gauge, Layers3,
  Radio, ShieldCheck, WifiOff, Activity, FileCheck2, Clock3, Target,
  Crosshair, Boxes, BookOpen, LockKeyhole, Settings2
} from 'lucide-react';
import type {Revision} from './GeometryWorkspace';
import {
  IconProjects, IconWellPlanning, IconDirectional, IconSurvey, IconAntiCollision,
  Icon3DWell, IconHydraulics, IconTorqueDrag, IconCasing, IconBHA,
  IconGeomechanics, IconRealtime, IconOffsets, IconEvidence, IconReports,
  IconQualification, IconAdmin,
} from './design-system';

type Row = Record<string, number|string|null>;
type Dataset = {id:string;kind?:string;filename:string;row_count:number;source_hash:string;rows?:Row[]};
type ProjectLike = {id:string;name:string;well_name:string;datum:string;north_reference:string;origin:string};
type IconType = React.ComponentType<{size?:number|string;color?:string}>;
type OpenPage = (page:string)=>void;

const fmt=(value:unknown,digits=1)=>typeof value==='number'&&Number.isFinite(value)
  ? value.toLocaleString('en-US',{maximumFractionDigits:digits,minimumFractionDigits:digits})
  : '—';
const n=(row:Row|undefined,key:string)=>typeof row?.[key]==='number'?Number(row[key]):null;

const workflows:{category:string;items:{label:string;page:string;description:string;icon:IconType}[]}[]=[
  {category:'PLAN & DESIGN',items:[
    {label:'Well Planning',page:'Well geometry',description:'Targets, trajectories, hole sections and design revisions.',icon:IconWellPlanning},
    {label:'Directional',page:'Directional engineering',description:'Survey geometry, DLS, coordinate context and uncertainty diagnostics.',icon:IconDirectional},
    {label:'Survey',page:'Data workspace',description:'Import, inspect and preserve survey evidence with explicit units.',icon:IconSurvey},
    {label:'Anti-Collision',page:'Anti-Collision',description:'Offset selection, proximity context and uncertainty-aware separation.',icon:IconAntiCollision},
    {label:'3D Well Model',page:'3D well engineering',description:'Spatial review of trajectory, formations, casing and selected MD.',icon:Icon3DWell},
  ]},
  {category:'ENGINEERING',items:[
    {label:'Hydraulics',page:'Hydraulics',description:'Pressure-loss, rheology and pressure-window research scenarios.',icon:IconHydraulics},
    {label:'Torque & Drag',page:'Torque & drag',description:'Soft-string operating states, friction sensitivity and residuals.',icon:IconTorqueDrag},
    {label:'Casing',page:'Casing program',description:'Programme geometry, load cases and evidence-linked envelopes.',icon:IconCasing},
    {label:'BHA',page:'BHA dynamics',description:'BHA configuration context and bounded dynamics research.',icon:IconBHA},
    {label:'Geomechanics',page:'Formation geomechanics',description:'Survey-bound formation inputs, stresses and research pressure intervals.',icon:IconGeomechanics},
  ]},
  {category:'OPERATIONS & REVIEW',items:[
    {label:'Realtime',page:'Realtime',description:'Historical replay now; read-only WITSML/ETP remains a deployment gate.',icon:IconRealtime},
    {label:'Offsets',page:'Offset benchmarks',description:'Evidence-preserving cohort comparison and empirical benchmarks.',icon:IconOffsets},
    {label:'Evidence',page:'Evidence search',description:'Source hashes, calculations, programme versions and citations.',icon:IconEvidence},
    {label:'Reports',page:'Reports',description:'Fixed evidence snapshots and reproducible exports.',icon:IconReports},
    {label:'Qualification',page:'Capability roadmap',description:'Model scope, verification state and open qualification gates.',icon:IconQualification},
    {label:'Admin',page:'Audit trail',description:'Audit chain, governance context and workstation integrity.',icon:IconAdmin},
  ]},
];

export function WorkflowLauncher({
  project,surveyStations,telemetryRecords,geometryReady,pendingEvents,onOpen
}:{project:ProjectLike;surveyStations:number;telemetryRecords:number;geometryReady:boolean;pendingEvents:number;onOpen:OpenPage}){
  return <section className="workflow-launcher" aria-label="GeoDrill workflow launcher">
    <div className="workflow-hero">
      <div>
        <span className="eyebrow">DRILLING ENGINEERING WORKSTATION</span>
        <h2>Plan, design, analyse and review the well in one workspace.</h2>
        <p>{project.name} · {project.well_name}. Existing engineering kernels remain the calculation authority; this layer organizes them around drilling workflows.</p>
      </div>
      <div className="workflow-health">
        <div><strong>{surveyStations}</strong><span>survey stations</span></div>
        <div><strong>{telemetryRecords}</strong><span>telemetry records</span></div>
        <div><strong>{geometryReady?'Ready':'Pending'}</strong><span>saved geometry</span></div>
        <div><strong>{pendingEvents}</strong><span>review events</span></div>
      </div>
    </div>
    {workflows.map(group=><div className="workflow-section" key={group.category}>
      <div className="workflow-section-heading"><span>{group.category}</span><i/></div>
      <div className="workflow-card-grid">{group.items.map(({label,page,description,icon:Icon})=>
        <button className="workflow-card" key={label} onClick={()=>onOpen(page)}>
          <span className="workflow-icon"><Icon size={24}/></span>
          <span className="workflow-card-copy"><strong>{label}</strong><small>{description}</small></span>
          <ArrowRight size={16}/>
        </button>
      )}</div>
    </div>)}
  </section>;
}

function SubjectPlan({revision,selectedMD,onSelectMD}:{revision:Revision|null;selectedMD:number|null;onSelectMD:(md:number)=>void}){
  const points=revision?.result.samples??[];
  if(!points.length)return <div className="empty-engineering-state"><Crosshair size={34}/><strong>No saved subject-well geometry</strong><span>Save a geometry revision before creating an anti-collision study.</span></div>;
  const minE=Math.min(...points.map(p=>p.east_m)),maxE=Math.max(...points.map(p=>p.east_m));
  const minN=Math.min(...points.map(p=>p.north_m)),maxN=Math.max(...points.map(p=>p.north_m));
  const dx=Math.max(1,maxE-minE),dy=Math.max(1,maxN-minN);
  const scale=Math.min(470/dx,300/dy);
  const x=(e:number)=>70+(e-minE)*scale;
  const y=(nn:number)=>345-(nn-minN)*scale;
  const d=points.map((p,i)=>`${i?'L':'M'}${x(p.east_m).toFixed(1)},${y(p.north_m).toFixed(1)}`).join(' ');
  const picked=selectedMD===null?null:points.reduce((best,p)=>Math.abs(p.md_m-selectedMD)<Math.abs(best.md_m-selectedMD)?p:best,points[0]);
  return <svg className="anticollision-plot" viewBox="0 0 620 390" role="img" aria-label="Subject well plan view; no offset wells loaded">
    {[0,1,2,3,4].map(i=><React.Fragment key={i}><line x1={70+i*118} x2={70+i*118} y1="30" y2="345"/><line x1="70" x2="542" y1={30+i*78.75} y2={30+i*78.75}/></React.Fragment>)}
    <path d={d} fill="none" stroke="#0B3D91" strokeWidth="4" strokeLinecap="round"/>
    {points.filter((_,i)=>i%Math.max(1,Math.ceil(points.length/20))===0||i===points.length-1).map(p=><circle key={p.md_m} cx={x(p.east_m)} cy={y(p.north_m)} r="4" fill="#0EA5B7" onClick={()=>onSelectMD(p.md_m)}><title>MD {fmt(p.md_m,1)} m</title></circle>)}
    {picked&&<circle cx={x(picked.east_m)} cy={y(picked.north_m)} r="8" fill="#F97316" stroke="white" strokeWidth="3"/>}
    <text x="70" y="375">East → · North ↑ · source-bound geometry</text>
    <text x="540" y="45" textAnchor="end">No offset trajectory supplied</text>
  </svg>;
}

export function AntiCollisionWorkspace({
  project,survey,revision,selectedMD,onSelectMD,onDirectional,onData,on3D
}:{project:ProjectLike;survey:Dataset|null;revision:Revision|null;selectedMD:number|null;onSelectMD:(md:number)=>void;onDirectional:()=>void;onData:()=>void;on3D:()=>void}){
  const geometryCurrent=Boolean(revision&&revision.input.survey_dataset_id===survey?.id);
  return <div className="v09-workspace">
    <div className="workspace-toolbar">
      <div><span className="workspace-kicker">ANTI-COLLISION / RESEARCH WORKFLOW</span><strong>{project.well_name}</strong></div>
      <div className="toolbar-actions"><button className="button secondary" onClick={onDirectional}>Directional</button><button className="button secondary" onClick={on3D}>Open 3D</button></div>
    </div>
    <div className="workspace-three-column">
      <aside className="workspace-rail">
        <div className="rail-section"><span>SUBJECT WELL</span><strong>{project.well_name}</strong><small>{survey?.filename??'No active survey'}</small></div>
        <div className="rail-section"><span>GEOMETRY</span><div className={geometryCurrent?'state-row ok':'state-row warn'}>{geometryCurrent?<CheckCircle2 size={15}/>:<CircleAlert size={15}/>}<b>{geometryCurrent?'Current':'Missing / stale'}</b></div><small>{revision?revision.id.slice(0,8):'No saved revision'}</small></div>
        <div className="rail-section"><span>OFFSETS</span><div className="state-row muted"><Database size={15}/><b>0 selected</b></div><small>Offset surveys are not yet bound to this workspace.</small></div>
        <button className="button secondary rail-button" onClick={onData}>Import / review sources</button>
      </aside>
      <section className="workspace-canvas">
        <div className="canvas-heading"><div><h3>Plan view</h3><p>Subject trajectory only. No separation factor is generated without offset geometry and uncertainty evidence.</p></div><span className="badge amber">Clearance withheld</span></div>
        <SubjectPlan revision={revision} selectedMD={selectedMD} onSelectMD={onSelectMD}/>
        <div className="engineering-empty-band"><IconAntiCollision size={24}/><div><strong>Offset comparison is intentionally empty.</strong><span>Add coordinate-compatible offset surveys and error-model evidence before calculating proximity.</span></div></div>
      </section>
      <aside className="workspace-inspector">
        <div className="inspector-heading"><Target size={18}/><strong>Study readiness</strong></div>
        <div className="check-list">
          <div className={survey?'done':''}>{survey?<CheckCircle2/>:<CircleAlert/>}<span>Subject survey</span></div>
          <div className={geometryCurrent?'done':''}>{geometryCurrent?<CheckCircle2/>:<CircleAlert/>}<span>Current geometry revision</span></div>
          <div><CircleAlert/><span>Coordinate-compatible offsets</span></div>
          <div><CircleAlert/><span>Offset uncertainty evidence</span></div>
        </div>
        <div className="inspector-note"><ShieldCheck size={18}/><p><strong>No drilling clearance.</strong> Proximity, uncertainty and operational approval remain separate qualification gates.</p></div>
        <dl className="compact-dl"><div><dt>CRS / frame</dt><dd>{revision?.input.coordinate_reference??'Not declared'}</dd></div><div><dt>Datum</dt><dd>{project.datum}</dd></div><div><dt>North</dt><dd>{project.north_reference}</dd></div></dl>
      </aside>
    </div>
    <div className="panel"><div className="panel-heading"><div><h2>Offset separation table</h2><p>Rows appear only after source-backed offsets are attached.</p></div></div><div className="table-scroll"><table><thead><tr><th>Offset well</th><th>Closest approach</th><th>Subject MD</th><th>Uncertainty</th><th>Separation factor</th><th>Status</th></tr></thead><tbody><tr><td colSpan={6} className="empty-table-cell">No offset wells selected. Nothing has been calculated.</td></tr></tbody></table></div></div>
  </div>;
}

function Sparkline({rows,channel,factor=1,color='#0EA5B7'}:{rows:Row[];channel:string;factor?:number;color?:string}){
  const values=rows.map(r=>n(r,channel)).filter((v):v is number=>v!==null).map(v=>v*factor);
  if(values.length<2)return <div className="spark-empty">No channel data</div>;
  const lo=Math.min(...values),hi=Math.max(...values),range=Math.max(hi-lo,1e-9);
  const pts=values.map((v,i)=>`${(i/(values.length-1)*280).toFixed(1)},${(65-(v-lo)/range*54).toFixed(1)}`).join(' ');
  return <svg className="sparkline" viewBox="0 0 280 72" aria-hidden="true"><polyline points={pts} fill="none" stroke={color} strokeWidth="2.5" strokeLinejoin="round"/><line x1="0" x2="280" y1="66" y2="66"/></svg>;
}

export function RealtimeWorkspace({
  project,telemetry,pendingEvents,onData,onEvents
}:{project:ProjectLike;telemetry:Dataset|null;pendingEvents:number;onData:()=>void;onEvents:()=>void}){
  const rows=telemetry?.rows??[],latest=rows.at(-1);
  const channels=[
    {key:'rop_m_s',label:'ROP',unit:'m/h',factor:3600,color:'#0EA5B7'},
    {key:'spp_pa',label:'SPP',unit:'MPa',factor:1e-6,color:'#F97316'},
    {key:'wob_n',label:'WOB',unit:'kN',factor:1e-3,color:'#0B3D91'},
    {key:'torque_nm',label:'Torque',unit:'kN·m',factor:1e-3,color:'#10B981'},
  ];
  const valid=rows.filter(r=>r.quality==='valid').length;
  return <div className="v09-workspace realtime-workspace">
    <div className="workspace-toolbar">
      <div><span className="workspace-kicker">OPERATIONS / READ-ONLY</span><strong>Realtime & replay</strong></div>
      <div className="toolbar-actions"><span className="badge neutral"><WifiOff size={13}/>Live rig adapter not connected</span><button className="button secondary" onClick={onData}>Data sources</button></div>
    </div>
    <div className="realtime-status-strip">
      <div><Radio size={17}/><span>Mode</span><strong>Historical replay</strong></div>
      <div><Database size={17}/><span>Source</span><strong>{telemetry?.filename??'No telemetry'}</strong></div>
      <div><Clock3 size={17}/><span>Records</span><strong>{rows.length}</strong></div>
      <div><ShieldCheck size={17}/><span>Quality</span><strong>{rows.length?fmt(valid/rows.length*100,1)+'%':'—'}</strong></div>
      <button onClick={onEvents}><CircleAlert size={17}/><span>Events</span><strong>{pendingEvents} pending</strong></button>
    </div>
    <div className="realtime-kpi-grid">{channels.map(c=><div className="realtime-kpi" key={c.key}><div><span>{c.label}</span><strong>{n(latest,c.key)===null?'—':fmt((n(latest,c.key)??0)*c.factor,c.label==='ROP'?1:2)} <small>{c.unit}</small></strong></div><Sparkline rows={rows} channel={c.key} factor={c.factor} color={c.color}/></div>)}</div>
    <div className="workspace-two-column">
      <section className="panel">
        <div className="panel-heading"><div><h2>Depth / time channel review</h2><p>Source-time records; gaps and missing values remain visible.</p></div><span className="badge neutral">read only</span></div>
        <div className="channel-matrix">{[
          ['MD','md_m','m'],['TVD','tvd_m','m'],['Flow','flow_m3_s','m³/s'],['RPM','rotation_rad_s','rad/s'],['MSE','mse_pa','Pa'],['State','state','']
        ].map(([label,key,unit])=><div key={key}><span>{label}</span><strong>{typeof latest?.[key]==='number'?fmt(latest[key],key==='mse_pa'?0:3):String(latest?.[key]??'—')}</strong><small>{unit}</small></div>)}</div>
      </section>
      <aside className="panel realtime-readiness">
        <div className="panel-heading"><div><h2>Live integration readiness</h2><p>UI is prepared for normalized read-only channels.</p></div><Radio size={20}/></div>
        <div className="readiness-list">
          <div className="ready"><CheckCircle2/><span>Historical canonical channel model</span></div>
          <div className="ready"><CheckCircle2/><span>Source-time replay</span></div>
          <div><CircleAlert/><span>WITSML adapter · pending</span></div>
          <div><CircleAlert/><span>ETP subscription / reconnect · pending</span></div>
          <div><CircleAlert/><span>Arrival-time persistence · pending</span></div>
        </div>
        <div className="inspector-note"><LockKeyhole size={18}/><p>No write path or equipment authority is exposed by this workspace.</p></div>
      </aside>
    </div>
  </div>;
}

const capabilities=[
  {name:'Directional & Survey',status:'Internal verification',tone:'green',scope:'Source-bound minimum-curvature geometry, geodesy and uncertainty diagnostics.',page:'Directional engineering'},
  {name:'Anti-Collision',status:'Research diagnostic',tone:'amber',scope:'Proximity workflow UI; clearance remains withheld without qualified offsets and uncertainty.',page:'Anti-Collision'},
  {name:'3D Well Model',status:'Source-bound preview',tone:'amber',scope:'Persisted kernel coordinates and engineering layers; WebGL production engine remains open.',page:'3D well engineering'},
  {name:'Hydraulics',status:'Research envelope',tone:'amber',scope:'Declared steady-flow envelopes with explicit applicability limits.',page:'Hydraulics'},
  {name:'Torque & Drag',status:'Research envelope',tone:'amber',scope:'Quasi-static soft-string cases with supplied friction and residual evidence.',page:'Torque & drag'},
  {name:'Casing',status:'Research envelope',tone:'amber',scope:'Load catalogues and evidence-linked body / connection screening.',page:'Casing program'},
  {name:'Geomechanics',status:'Research workflow',tone:'amber',scope:'Survey-bound core / closure evidence and bounded stress scenarios.',page:'Formation geomechanics'},
  {name:'Realtime',status:'Replay only',tone:'neutral',scope:'Historical replay is implemented; read-only WITSML / ETP remains pending.',page:'Realtime'},
  {name:'Evidence & Recovery',status:'Release-tested',tone:'green',scope:'Hash-linked evidence, reports, backup / restore and package checks.',page:'Evidence search'},
  {name:'Enterprise',status:'Planned',tone:'neutral',scope:'OIDC, shared deployment, database services and external security review.',page:'Audit trail'},
];

export function QualificationWorkspace({onOpen}:{onOpen:OpenPage}){
  const research=[
    ['Wellbore stability','Wellbore stability'],['Cuttings transport','Cuttings transport'],['Surge & swab','Surge & swab'],
    ['Buckling','Buckling assessment'],['Dynamics','BHA dynamics'],['Bit condition','Bit condition'],
    ['Wear & fatigue','Wear & fatigue'],['Flow anomaly research','Flow anomalies'],['Gas & phase','Gas & phase studies'],
    ['Supervisory simulation','Supervisory research'],['Log clustering','Log clustering'],['Shaly sand','Shaly sand'],['EM vendor review','EM vendor results']
  ];
  return <div className="v09-workspace qualification-workspace">
    <div className="qualification-banner"><ShieldCheck size={28}/><div><span className="workspace-kicker">QUALIFICATION & REVIEW</span><h2>Capability state is separate from operational authority.</h2><p>Implemented, verified, benchmarked and independently qualified are intentionally different states. Tests do not create field authority.</p></div></div>
    <div className="qualification-grid">{capabilities.map(c=><button className="qualification-card" key={c.name} onClick={()=>onOpen(c.page)}>
      <div><strong>{c.name}</strong><span className={'badge '+c.tone}>{c.status}</span></div><p>{c.scope}</p><span className="open-link">Open workflow <ArrowRight size={14}/></span>
    </button>)}</div>
    <div className="panel research-library"><div className="panel-heading"><div><h2>Advanced research library</h2><p>Specialist studies remain available without driving the primary product navigation.</p></div><BookOpen size={21}/></div><div className="research-link-grid">{research.map(([label,page])=><button key={label} onClick={()=>onOpen(page)}><Activity size={16}/><span>{label}</span><ArrowRight size={13}/></button>)}</div></div>
    <div className="workspace-two-column"><div className="panel governance-card"><div className="panel-heading"><div><h2>Release gates</h2><p>Required before stronger claims can be made.</p></div><FileCheck2 size={21}/></div><ul><li>Original engineering observations and applicability evidence</li><li>Independent named engineering review</li><li>Representative operator acceptance</li><li>Trusted publisher signing</li><li>Scoped external security assessment</li></ul></div><div className="panel governance-card"><div className="panel-heading"><div><h2>Authority boundary</h2><p>Hard product constraints in the current release.</p></div><Settings2 size={21}/></div><ul><li>Equipment control: unavailable</li><li>Automated drilling clearance: unavailable</li><li>Realtime ingestion: read-only target</li><li>Research outputs require human engineering review</li></ul></div></div>
  </div>;
}
