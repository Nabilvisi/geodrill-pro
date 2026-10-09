/** Display transforms consume saved geometry; they never integrate a survey. */
export type Vec3 = [number, number, number];
export type SavedSceneSample = {md_m:number;north_m:number;east_m:number;tvd_m:number;elevation_m:number;reference_north_m?:number;reference_east_m?:number};
export type SceneFrame = {coordinate_reference:string;datum:string;north_reference:string;wellhead_north_m:number;wellhead_east_m:number;wellhead_elevation_m:number};
export type SceneSource = {id:string;sha256:string;wellbore_id?:string;trajectory_type?:string;frame:SceneFrame;samples:readonly SavedSceneSample[];surveyMDs?:readonly number[]};
export type SceneTransform = {origin:Vec3;metresToDisplay:number;verticalExaggeration:number};
export type StationIdentity = {revisionId:string;revisionHash:string;wellboreId:string|null;role:string;md_m:number;sampleIndex:number;surveyStation:boolean};
export type ScenePath = {source:SceneSource;positions:Float32Array;stations:StationIdentity[];bounds:{min:Vec3;max:Vec3}};
export type CanvasRect={left:number;top:number;width:number;height:number};
const finite=(values:readonly number[])=>values.every(Number.isFinite);
/** CSS client coordinates, independent of scroll position, nested event targets and device pixel ratio. */
export function canvasPointer(clientX:number,clientY:number,rect:CanvasRect):[number,number]|null {
  if(!finite([clientX,clientY,rect.left,rect.top,rect.width,rect.height])||rect.width<=0||rect.height<=0)return null;
  const x=(clientX-rect.left)/rect.width,y=(clientY-rect.top)/rect.height;
  if(x<0||x>1||y<0||y>1)return null;
  return [2*x-1,1-2*y];
}
export function closestRayVertex(hits:readonly {index?:number;distanceToRay?:number;distance:number}[]):number|null {
  let best:{index:number;distanceToRay:number;distance:number}|null=null;
  for(const {index,distanceToRay,distance} of hits){
    if(index===undefined||!Number.isInteger(index)||index<0||distanceToRay===undefined||!Number.isFinite(distanceToRay)||distanceToRay<0||!Number.isFinite(distance)||distance<0)continue;
    if(!best||distanceToRay<best.distanceToRay||(distanceToRay===best.distanceToRay&&distance<best.distance))best={index,distanceToRay,distance};
  }
  return best?.index??null;
}
export function validateFrame(frame:SceneFrame):void {
  if(!frame.coordinate_reference.trim()||!frame.datum.trim()||!['true','grid'].includes(frame.north_reference)||!finite([frame.wellhead_north_m,frame.wellhead_east_m,frame.wellhead_elevation_m]))throw new Error('A declared coordinate frame, datum, north reference and finite origin are required.');
}
export function sameFrame(a:SceneFrame,b:SceneFrame):boolean {
  return a.coordinate_reference===b.coordinate_reference&&a.datum===b.datum&&a.north_reference===b.north_reference;
}
/** Reference coordinates are [North, East, positive-down V]; origin elevation is positive up. */
export function canonicalNEV(sample:SavedSceneSample,frame:SceneFrame):Vec3 {
  if(!finite([sample.md_m,sample.north_m,sample.east_m,sample.tvd_m,sample.elevation_m]))throw new Error('Non-finite saved geometry cannot render.');
  const n=sample.north_m+frame.wellhead_north_m,e=sample.east_m+frame.wellhead_east_m,v=sample.tvd_m-frame.wellhead_elevation_m;
  if(Math.abs(sample.elevation_m+v)>1e-6||(sample.reference_north_m!==undefined&&(!Number.isFinite(sample.reference_north_m)||Math.abs(sample.reference_north_m-n)>1e-6))||(sample.reference_east_m!==undefined&&(!Number.isFinite(sample.reference_east_m)||Math.abs(sample.reference_east_m-e)>1e-6)))throw new Error('Saved local and reference coordinates disagree; rendering withheld.');
  return [n,e,v];
}
/** Three.js right-handed axes: +X East, +Y elevation/up, -Z North. */
export function displayPosition(nev:Vec3,transform:SceneTransform):Vec3 {
  if(!finite([...nev,...transform.origin,transform.metresToDisplay,transform.verticalExaggeration])||transform.metresToDisplay<=0||transform.verticalExaggeration<=0)throw new Error('Invalid scene display transform.');
  const [n,e,v]=nev,[on,oe,ov]=transform.origin,k=transform.metresToDisplay;
  return [(e-oe)*k,-(v-ov)*k*transform.verticalExaggeration,-(n-on)*k].map(value=>value===0?0:value) as Vec3;
}
export function undisplayPosition(position:Vec3,transform:SceneTransform):Vec3 {
  const [on,oe,ov]=transform.origin,k=transform.metresToDisplay;
  if(!finite(position)||!finite([...transform.origin,k,transform.verticalExaggeration])||k<=0||transform.verticalExaggeration<=0)throw new Error('Invalid scene display transform.');
  return [on-position[2]/k,oe+position[0]/k,ov-position[1]/(k*transform.verticalExaggeration)];
}
export function canonicalDistance(a:Vec3,b:Vec3):number {
  if(!finite([...a,...b]))throw new Error('Distance requires finite canonical coordinates.');
  return Math.hypot(a[0]-b[0],a[1]-b[1],a[2]-b[2]);
}
export function buildScenePath(source:SceneSource,transform:SceneTransform,referenceFrame:SceneFrame):ScenePath {
  validateFrame(source.frame);validateFrame(referenceFrame);
  if(!sameFrame(source.frame,referenceFrame))throw new Error('Scene sources require an explicitly shared frame, datum and north reference; no implicit CRS conversion.');
  if(!source.id||!source.sha256||!source.samples.length)throw new Error('A saved revision with identity, hash and samples is required.');
  const positions=new Float32Array(source.samples.length*3),stations:StationIdentity[]=[];
  const min:Vec3=[Infinity,Infinity,Infinity],max:Vec3=[-Infinity,-Infinity,-Infinity];
  const stationMDs=source.surveyMDs===undefined?null:new Set(source.surveyMDs);
  let previous=-Infinity;
  source.samples.forEach((sample,index)=>{
    if(sample.md_m<0||sample.md_m<=previous)throw new Error('Saved sample MD must strictly increase.');previous=sample.md_m;
    const position=displayPosition(canonicalNEV(sample,source.frame),transform);
    for(let axis=0;axis<3;axis++){positions[index*3+axis]=position[axis];if(!Number.isFinite(positions[index*3+axis]))throw new Error('Coordinates exceed renderer precision range.');min[axis]=Math.min(min[axis],position[axis]);max[axis]=Math.max(max[axis],position[axis]);}
    stations.push({revisionId:source.id,revisionHash:source.sha256,wellboreId:source.wellbore_id??null,role:source.trajectory_type??'legacy',md_m:sample.md_m,sampleIndex:index,surveyStation:stationMDs?.has(sample.md_m)??false});
  });
  return {source,positions,stations,bounds:{min,max}};
}
export function stationAtVertex(path:ScenePath,index:number):StationIdentity {
  if(!Number.isInteger(index)||index<0||index>=path.stations.length)throw new Error('Invalid picked station vertex.');return path.stations[index];
}
export function nearestSampleIndex(samples:readonly SavedSceneSample[],md:number):number {
  if(!samples.length||!Number.isFinite(md))throw new Error('Selection requires saved samples and finite MD.');
  let lo=0,hi=samples.length-1;while(lo<hi){const middle=Math.floor((lo+hi)/2);if(samples[middle].md_m<md)lo=middle+1;else hi=middle;}
  return lo>0&&Math.abs(samples[lo-1].md_m-md)<=Math.abs(samples[lo].md_m-md)?lo-1:lo;
}
