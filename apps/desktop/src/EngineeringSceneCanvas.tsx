import {useEffect,useMemo,useRef} from 'react';
import {Canvas,useThree,events,type CanvasProps,type ThreeEvent} from '@react-three/fiber';
import {OrbitControls} from '@react-three/drei';
import {BufferAttribute,BufferGeometry,Line as ThreeLine,LineBasicMaterial,Vector3,DoubleSide} from 'three';
import type {Revision} from './GeometryWorkspace';
import {canvasPointer,closestRayVertex,canonicalNEV,displayPosition,nearestSampleIndex,stationAtVertex,type ScenePath,type SceneTransform,type StationIdentity} from './sceneModel';
const sceneEvents:NonNullable<CanvasProps['events']> = state=>({...events(state),compute(event,current){
  const point=canvasPointer(event.clientX,event.clientY,current.gl.domElement.getBoundingClientRect());
  current.pointer.set(point?.[0]??2,point?.[1]??2);current.raycaster.setFromCamera(current.pointer,current.camera);
},filter(intersections,current){return Math.abs(current.pointer.x)>1||Math.abs(current.pointer.y)>1?[]:intersections;}});
type Props={path:ScenePath;revision:Revision;transform:SceneTransform;selectedMD:number|null;onPick:(station:StationIdentity)=>void;fitRequest:number;fitSelected:boolean;formations:boolean;casings:boolean;onReady:()=>void;onLost:()=>void};
function PathLine({positions,color}:{positions:Float32Array;color:string}){
  const object=useMemo(()=>{const geometry=new BufferGeometry();geometry.setAttribute('position',new BufferAttribute(positions,3));return new ThreeLine(geometry,new LineBasicMaterial({color}));},[positions,color]);
  useEffect(()=>()=>{object.geometry.dispose();object.material.dispose();},[object]);return <primitive object={object}/>;
}
function Camera({path,selectedMD,request,fitSelected}:{path:ScenePath;selectedMD:number|null;request:number;fitSelected:boolean}){
  const {camera,invalidate}=useThree(),controls=useRef<React.ComponentRef<typeof OrbitControls>>(null);
  useEffect(()=>{const {min,max}=path.bounds,target=new Vector3(...min).add(new Vector3(...max)).multiplyScalar(.5);let extent=Math.max(1,max[0]-min[0],max[1]-min[1],max[2]-min[2]);
    if(fitSelected&&selectedMD!==null){const i=nearestSampleIndex(path.source.samples,selectedMD);target.fromArray(path.positions,i*3);extent=Math.max(10,extent*.12);}
    camera.position.copy(target).add(new Vector3(extent*.85,extent*.45,extent*.85));camera.near=Math.max(.001,extent/10000);camera.far=Math.max(100,extent*100);camera.updateProjectionMatrix();if(controls.current){controls.current.target.copy(target);controls.current.update();}camera.lookAt(target);invalidate();
  },[path,request,fitSelected,camera,invalidate]);
  return <OrbitControls ref={controls} makeDefault enableDamping={false}/>;
}
function World(props:Props){
  const {path,revision,transform,selectedMD,onPick,formations,casings}=props,extent=Math.max(1,...path.bounds.max.map((value,i)=>value-path.bounds.min[i]));
  const selected=selectedMD===null?null:nearestSampleIndex(path.source.samples,selectedMD);
  const pointGeometry=useMemo(()=>{const geometry=new BufferGeometry();geometry.setAttribute('position',new BufferAttribute(path.positions,3));return geometry;},[path]);
  const casingLines=useMemo(()=>revision.input.casings.map(c=>{const coordinates:number[]=[];path.source.samples.forEach((sample,i)=>{if(sample.md_m>=c.top_md_m&&sample.md_m<=c.bottom_md_m)coordinates.push(path.positions[i*3],path.positions[i*3+1],path.positions[i*3+2]);});return {name:c.name,color:c.state==='planned'?'#94A3B8':'#374151',positions:new Float32Array(coordinates)};}),[path,revision]);
  useEffect(()=>()=>pointGeometry.dispose(),[pointGeometry]);
  return <><Camera path={path} selectedMD={selectedMD} request={props.fitRequest} fitSelected={props.fitSelected}/><ambientLight intensity={1.4}/><directionalLight position={[1,2,3]} intensity={2}/>
    <group name="WellsGroup"><PathLine positions={path.positions} color="#0B3D91"/><points geometry={pointGeometry} onClick={(event:ThreeEvent<MouseEvent>)=>{event.stopPropagation();const index=closestRayVertex(event.intersections.filter(hit=>hit.object===event.object));if(index!==null)onPick(stationAtVertex(path,index));}}><pointsMaterial color="#0EA5B7" size={Math.max(.5,extent*.008)} sizeAttenuation/></points>
      {selected!==null&&<mesh position={Array.from(path.positions.slice(selected*3,selected*3+3)) as [number,number,number]}><sphereGeometry args={[Math.max(.8,extent*.012),16,12]}/><meshBasicMaterial color="#F97316"/></mesh>}
      {casings&&casingLines.map(c=><PathLine key={c.name} positions={c.positions} color={c.color}/>)}</group>
    <group name="GeologicalGroup">{formations&&revision.input.formations.map(top=>{const sample={md_m:0,north_m:0,east_m:0,tvd_m:top.top_tvd_m,elevation_m:path.source.frame.wellhead_elevation_m-top.top_tvd_m};const position=displayPosition(canonicalNEV(sample,path.source.frame),transform);return <mesh key={top.name} position={position} rotation={[-Math.PI/2,0,0]}><planeGeometry args={[extent*.5,extent*.5]}/><meshStandardMaterial color="#0EA5B7" transparent opacity={.12} side={DoubleSide} depthWrite={false}/></mesh>;})}</group><axesHelper args={[extent*.1]}/></>;
}
export default function EngineeringSceneCanvas(props:Props){return <div style={{height:540,background:'#F4F7FA'}} role="img" aria-label="Three.js saved trajectory scene; orbit with drag, pan with right drag, zoom with scroll"><Canvas events={sceneEvents} frameloop="demand" dpr={[1,2]} raycaster={{params:{Mesh:{},Line:{threshold:1},LOD:{},Sprite:{},Points:{threshold:Math.max(.5,(props.path.bounds.max[1]-props.path.bounds.min[1])*.008)}}}} onCreated={({gl})=>{gl.domElement.addEventListener('webglcontextlost',props.onLost,{once:true});props.onReady();}} fallback={<p role="alert">WebGL is unavailable. Saved coordinates and selection remain available in the table.</p>}><World {...props}/></Canvas></div>;}
