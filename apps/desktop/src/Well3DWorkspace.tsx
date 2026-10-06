import {useState} from 'react';
import type {Revision} from './GeometryWorkspace';
type Props={revision:Revision|null;activeSurveyID?:string;datum:string;northReference:string;selectedMD:number|null;onSelectMD:(md:number)=>void;onGeometryPage:()=>void};
export function Well3DWorkspace({revision,activeSurveyID,datum,northReference,selectedMD,onSelectMD,onGeometryPage}:Props){
  const [yaw,setYaw]=useState(45),[pitch,setPitch]=useState(25),[zoom,setZoom]=useState(1),[layers,setLayers]=useState(true);
  if(!revision)return <div className="panel"><h2>No saved engineering geometry</h2><p>Import a survey and save a geometry revision before opening this model.</p><button className="button primary" onClick={onGeometryPage}>Open well geometry</button></div>;
  const points=revision.result.samples;
  const n=points.map(p=>p.north_m),e=points.map(p=>p.east_m),t=points.map(p=>p.tvd_m);
  const center=[(Math.min(...e)+Math.max(...e))/2,(Math.min(...n)+Math.max(...n))/2,(Math.min(...t)+Math.max(...t))/2];
  const extent=Math.max(1,Math.max(...e)-Math.min(...e),Math.max(...n)-Math.min(...n),Math.max(...t)-Math.min(...t));
  const project=(east:number,north:number,tvd:number)=>{const a=yaw*Math.PI/180,b=pitch*Math.PI/180,x=east-center[0],y=north-center[1],z=tvd-center[2];const xr=x*Math.cos(a)-y*Math.sin(a),yr=x*Math.sin(a)+y*Math.cos(a);const k=380/extent*zoom;return [400+xr*k,270+(yr*Math.sin(b)+z*Math.cos(b))*k];};
  const line=(ps:typeof points)=>ps.map((p,i)=>{const [x,y]=project(p.east_m,p.north_m,p.tvd_m);return (i?'L':'M')+x+','+y;}).join(' ');
  const picked=selectedMD===null?null:points.reduce((best,p)=>Math.abs(p.md_m-selectedMD)<Math.abs(best.md_m-selectedMD)?p:best,points[0]);
  const corner=extent*.25;
  return <div className="panel"><div className="panel-heading"><div><h2>3D well model · saved engineering revision</h2><p>Geometry {revision.id.slice(0,8)} · source hash {revision.sha256.slice(0,16)}…</p></div><button className="button secondary" onClick={onGeometryPage}>Edit geometry</button></div>
    {activeSurveyID!==revision.input.survey_dataset_id&&<p className="alert warning">Historical geometry: this revision references a different survey from the current source selection. Its coordinates remain bound to that earlier source.</p>}
    <p>CRS / local frame: {revision.input.coordinate_reference} · Datum: {datum} · {northReference} north · elevation origin {revision.input.wellhead_elevation_m} m · coordinates in metres, TVD positive down</p>
    <div className="scene-controls"><label>Orbit (°)<input aria-label="3D orbit angle" type="range" min="0" max="360" value={yaw} onChange={e=>setYaw(Number(e.target.value))}/></label><label>Pitch (°)<input aria-label="3D pitch angle" type="range" min="-85" max="85" value={pitch} onChange={e=>setPitch(Number(e.target.value))}/></label><label>Zoom<input aria-label="3D zoom" type="range" min=".4" max="2" step=".05" value={zoom} onChange={e=>setZoom(Number(e.target.value))}/></label><label><input type="checkbox" checked={layers} onChange={e=>setLayers(e.target.checked)}/>Formations / casing</label><button className="button secondary" onClick={()=>{setYaw(45);setPitch(25);setZoom(1);}}>Reset view</button></div>
    <svg viewBox="0 0 800 540" className="engineering-scene" role="img" aria-label="Three dimensional projection of saved kernel geometry with station selection">
      {layers&&revision.input.formations.map((f,i)=>{const corners=[[-corner,-corner],[corner,-corner],[corner,corner],[-corner,corner]].map(([x,y])=>project(center[0]+x,center[1]+y,f.top_tvd_m));return <g key={i}><polygon points={corners.map(p=>p.join(',')).join(' ')} fill="#0EA5B7" fillOpacity=".10" stroke="#94A3B8"/><text x={corners[0][0]} y={corners[0][1]} fontSize="11">{f.name} · interpreted top {f.top_tvd_m} m TVD</text></g>;})}
      {layers&&revision.input.casings.map((c,i)=><path key={i} d={line(points.filter(p=>p.md_m>=c.top_md_m&&p.md_m<=c.bottom_md_m))} fill="none" stroke={c.state==='planned'?'#94A3B8':'#374151'} strokeWidth="9" strokeOpacity=".5"><title>{c.name} · {c.state} · OD {c.outside_diameter_m*1000} mm (line width exaggerated)</title></path>)}
      <path d={line(points)} fill="none" stroke="#0B3D91" strokeWidth="3"/>
      {points.filter((_,i)=>i%Math.max(1,Math.ceil(points.length/100))===0||i===points.length-1).map(p=>{const [x,y]=project(p.east_m,p.north_m,p.tvd_m);return <circle key={p.md_m} cx={x} cy={y} r="4" fill="#0EA5B7" role="button" tabIndex={0} aria-label={'Select 3D MD '+p.md_m+' m'} onClick={()=>onSelectMD(p.md_m)} onKeyDown={ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();onSelectMD(p.md_m);}}}><title>MD {p.md_m} m</title></circle>;})}
      {picked&&<circle cx={project(picked.east_m,picked.north_m,picked.tvd_m)[0]} cy={project(picked.east_m,picked.north_m,picked.tvd_m)[1]} r="7" fill="#F97316"/>}
      <text x="15" y="520">Saved survey geometry · equal spatial scale · casing width exaggerated for visibility</text>
    </svg>
    {picked&&<p>Selected MD {selectedMD} m · nearest sample MD {picked.md_m} m · N {picked.north_m.toFixed(3)} m · E {picked.east_m.toFixed(3)} m · TVD {picked.tvd_m.toFixed(3)} m</p>}
    <p className="muted">This interim SVG projection renders persisted kernel coordinates. Survey uncertainty, offset comparison, targets and BHA are absent until revision-bound scene data is supplied. The Three.js workstation, clipping and representative-load validation remain open.</p>
  </div>;
}
