import {useEffect,useRef,useState} from 'react';
// Three.js is pinned in package.json; the runtime ships its ES modules but not TypeScript declarations.
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';

export type SpatialPoint={
  md_m:number;
  north_m:number;
  east_m:number;
  tvd_m:number;
  reference_north_m?:number;
  reference_east_m?:number;
};
export type SpatialFormation={name:string;top_tvd_m:number;uncertainty_m:number};
export type SpatialCasing={name:string;top_md_m:number;bottom_md_m:number;outside_diameter_m:number;state:string};
export type SpatialTarget={id:string;name:string;center_tvd_m:number;center_north_m:number;center_east_m:number;radius_m:number;tolerance_m:number};
export type SpatialUncertainty={
  md_m:number;
  tvd_m:number;
  north_m:number;
  east_m:number;
  semi_major_2sigma_m:number;
  semi_minor_2sigma_m:number;
  vertical_2sigma_m:number;
  azimuth_major_deg:number;
};
export type ClosestApproach={
  ref_md_m:number;
  offset_md_m:number;
  c2c_distance_m:number;
  horizontal_distance_m:number;
  vertical_distance_m:number;
  ref_pos_nev:[number,number,number];
  offset_pos_nev:[number,number,number];
};
export type SceneLayers={
  subject:boolean;offset:boolean;formations:boolean;casing:boolean;targets:boolean;
  subjectUncertainty:boolean;offsetUncertainty:boolean;closestApproach:boolean;stations:boolean;grid:boolean;
};
export type CameraPreset='perspective'|'plan'|'north-section'|'east-section';

type Props={
  subjectPoints:SpatialPoint[];
  offsetPoints:SpatialPoint[];
  formations:SpatialFormation[];
  casings:SpatialCasing[];
  targets:SpatialTarget[];
  subjectUncertainty:SpatialUncertainty[];
  offsetUncertainty:SpatialUncertainty[];
  closestApproach:ClosestApproach|null;
  selectedMD:number|null;
  onSelectMD:(md:number)=>void;
  layers:SceneLayers;
  cameraPreset:CameraPreset;
  clipTvdM:number|null;
  className?:string;
};

const colors={
  background:0x071426,grid:0x29415c,subject:0x38bdf8,offset:0xfb923c,selected:0xf97316,
  casing:0x94a3b8,target:0x34d399,formation:0x0ea5b7,subjectUncertainty:0x22d3ee,
  offsetUncertainty:0xfbbf24,closest:0xf43f5e,text:0xe2e8f0,
};

function finitePoint(p:SpatialPoint){
  return [p.md_m,p.north_m,p.east_m,p.tvd_m].every(Number.isFinite);
}
function engineeringNorth(p:SpatialPoint){return Number.isFinite(p.reference_north_m)?Number(p.reference_north_m):p.north_m;}
function engineeringEast(p:SpatialPoint){return Number.isFinite(p.reference_east_m)?Number(p.reference_east_m):p.east_m;}

export function GeoDrill3DScene({
  subjectPoints,offsetPoints,formations,casings,targets,subjectUncertainty,offsetUncertainty,
  closestApproach,selectedMD,onSelectMD,layers,cameraPreset,clipTvdM,className=''
}:Props){
  const host=useRef<HTMLDivElement>(null);
  const [failure,setFailure]=useState('');
  const [renderInfo,setRenderInfo]=useState({objects:0,triangles:0});

  useEffect(()=>{
    const container=host.current;
    if(!container)return;
    setFailure('');

    let renderer:any,controls:any,frame=0,resizeObserver:ResizeObserver|null=null;
    try{
      const subject=subjectPoints.filter(finitePoint);
      const offset=offsetPoints.filter(finitePoint);
      if(subject.length<2)throw new Error('At least two source-bound subject trajectory samples are required.');

      const coordRows=[
        ...subject.map(p=>[engineeringEast(p),engineeringNorth(p),p.tvd_m] as [number,number,number]),
        ...offset.map(p=>[engineeringEast(p),engineeringNorth(p),p.tvd_m] as [number,number,number]),
        ...targets.map(t=>[t.center_east_m,t.center_north_m,t.center_tvd_m] as [number,number,number]),
      ].filter(v=>v.every(Number.isFinite));
      if(closestApproach){
        coordRows.push(
          [closestApproach.ref_pos_nev[1],closestApproach.ref_pos_nev[0],closestApproach.ref_pos_nev[2]],
          [closestApproach.offset_pos_nev[1],closestApproach.offset_pos_nev[0],closestApproach.offset_pos_nev[2]],
        );
      }
      const minE=Math.min(...coordRows.map(v=>v[0])),maxE=Math.max(...coordRows.map(v=>v[0]));
      const minN=Math.min(...coordRows.map(v=>v[1])),maxN=Math.max(...coordRows.map(v=>v[1]));
      const minT=Math.min(0,...coordRows.map(v=>v[2])),maxT=Math.max(...coordRows.map(v=>v[2]));
      const origin={east:(minE+maxE)/2,north:(minN+maxN)/2,tvd:(minT+maxT)/2};
      const horizontalExtent=Math.max(50,maxE-minE,maxN-minN);
      const verticalExtent=Math.max(50,maxT-minT);
      const extent=Math.max(horizontalExtent,verticalExtent);
      const markerRadius=Math.max(.8,extent*.0035);

      const toWorld=(north:number,east:number,tvd:number)=>new THREE.Vector3(
        east-origin.east,
        -(tvd-origin.tvd),
        north-origin.north,
      );
      const visible=(tvd:number)=>clipTvdM===null||tvd<=clipTvdM+1e-9;

      const scene=new THREE.Scene();
      scene.background=new THREE.Color(colors.background);
      scene.fog=new THREE.FogExp2(colors.background,1/Math.max(extent*6,1000));

      const width=Math.max(1,container.clientWidth),height=Math.max(1,container.clientHeight);
      const camera=new THREE.PerspectiveCamera(42,width/height,Math.max(.05,extent/10000),Math.max(5000,extent*40));
      renderer=new THREE.WebGLRenderer({antialias:true,powerPreference:'high-performance'});
      renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
      renderer.setSize(width,height,false);
      renderer.outputColorSpace=THREE.SRGBColorSpace;
      container.replaceChildren(renderer.domElement);

      scene.add(new THREE.HemisphereLight(0xcfe8ff,0x122033,1.25));
      const keyLight=new THREE.DirectionalLight(0xffffff,1.35);keyLight.position.set(extent,extent*1.3,extent);scene.add(keyLight);
      const fillLight=new THREE.DirectionalLight(0x67e8f9,.45);fillLight.position.set(-extent*.7,extent*.3,-extent);scene.add(fillLight);

      if(layers.grid){
        const gridSize=Math.max(200,Math.ceil(horizontalExtent/100)*100)*1.4;
        const divisions=Math.max(8,Math.min(40,Math.round(gridSize/100)));
        const grid=new THREE.GridHelper(gridSize,divisions,colors.grid,colors.grid);
        grid.position.y=origin.tvd;
        grid.material.opacity=.5;grid.material.transparent=true;
        scene.add(grid);
      }
      const axes=new THREE.AxesHelper(Math.max(25,extent*.08));axes.position.set(-horizontalExtent*.48,origin.tvd,-horizontalExtent*.48);scene.add(axes);

      const selectable:any[]=[];
      const materials:any[]=[];
      const geometries:any[]=[];
      const remember=(object:any)=>{if(object.geometry)geometries.push(object.geometry);if(object.material)materials.push(object.material);return object;};

      const makeLine=(points:any[],color:number,opacity=1,dashed=false)=>{
        const geom=new THREE.BufferGeometry().setFromPoints(points);geometries.push(geom);
        const mat=dashed?new THREE.LineDashedMaterial({color,transparent:opacity<1,opacity,dashSize:Math.max(2,extent*.01),gapSize:Math.max(1,extent*.006)}):new THREE.LineBasicMaterial({color,transparent:opacity<1,opacity});
        materials.push(mat);
        const line=new THREE.Line(geom,mat);if(dashed)line.computeLineDistances();return line;
      };

      const subjectVisible=subject.filter(p=>visible(p.tvd_m));
      if(layers.subject&&subjectVisible.length>=2){
        const line=makeLine(subjectVisible.map(p=>toWorld(engineeringNorth(p),engineeringEast(p),p.tvd_m)),colors.subject);
        line.userData={kind:'subject-trajectory'};scene.add(line);
      }
      const offsetVisible=offset.filter(p=>visible(p.tvd_m));
      if(layers.offset&&offsetVisible.length>=2){
        const line=makeLine(offsetVisible.map(p=>toWorld(engineeringNorth(p),engineeringEast(p),p.tvd_m)),colors.offset,.95);
        line.userData={kind:'offset-trajectory'};scene.add(line);
      }

      if(layers.casing){
        for(const c of casings){
          const ps=subject.filter(p=>p.md_m>=c.top_md_m&&p.md_m<=c.bottom_md_m&&visible(p.tvd_m));
          if(ps.length<2)continue;
          const curve=new THREE.CatmullRomCurve3(ps.map(p=>toWorld(engineeringNorth(p),engineeringEast(p),p.tvd_m)),false,'centripetal',.5);
          const radius=Math.max(c.outside_diameter_m/2,extent*.0018);
          const geom=new THREE.TubeGeometry(curve,Math.max(8,Math.min(180,ps.length*2)),radius,8,false);geometries.push(geom);
          const mat=new THREE.MeshStandardMaterial({color:c.state==='planned'?0x64748b:colors.casing,transparent:true,opacity:.42,roughness:.6,metalness:.2});materials.push(mat);
          const mesh=new THREE.Mesh(geom,mat);mesh.userData={kind:'casing',name:c.name};scene.add(mesh);
        }
      }

      if(layers.formations){
        const planeSize=Math.max(horizontalExtent*1.6,extent*.9,300);
        formations.filter(f=>visible(f.top_tvd_m)).forEach((f,i)=>{
          const geom=new THREE.PlaneGeometry(planeSize,planeSize);geometries.push(geom);
          const mat=new THREE.MeshBasicMaterial({color:i%2?0x164e63:colors.formation,side:THREE.DoubleSide,transparent:true,opacity:.10,depthWrite:false});materials.push(mat);
          const mesh=new THREE.Mesh(geom,mat);mesh.rotation.x=-Math.PI/2;mesh.position.y=-(f.top_tvd_m-origin.tvd);mesh.userData={kind:'formation',name:f.name};scene.add(mesh);
        });
      }

      if(layers.targets){
        for(const t of targets.filter(t=>visible(t.center_tvd_m))){
          const radius=Math.max(.5,t.radius_m),height=Math.max(1,t.tolerance_m*2);
          const geom=new THREE.CylinderGeometry(radius,radius,height,32,1,true);geometries.push(geom);
          const mat=new THREE.MeshBasicMaterial({color:colors.target,transparent:true,opacity:.18,side:THREE.DoubleSide,depthWrite:false});materials.push(mat);
          const mesh=new THREE.Mesh(geom,mat);mesh.position.copy(toWorld(t.center_north_m,t.center_east_m,t.center_tvd_m));mesh.userData={kind:'target',name:t.name};scene.add(mesh);
          const ringGeom=new THREE.RingGeometry(radius*.92,radius,40);geometries.push(ringGeom);
          const ringMat=new THREE.MeshBasicMaterial({color:colors.target,transparent:true,opacity:.85,side:THREE.DoubleSide});materials.push(ringMat);
          const ring=new THREE.Mesh(ringGeom,ringMat);ring.rotation.x=-Math.PI/2;ring.position.copy(mesh.position);scene.add(ring);
        }
      }

      const addUncertainty=(items:SpatialUncertainty[],color:number)=>{
        if(!items.length)return;
        const stride=Math.max(1,Math.ceil(items.length/22));
        items.filter((u,i)=>(i%stride===0||i===items.length-1)&&visible(u.tvd_m)).forEach(u=>{
          const geom=new THREE.SphereGeometry(1,14,10);geometries.push(geom);
          const mat=new THREE.MeshBasicMaterial({color,wireframe:true,transparent:true,opacity:.5,depthWrite:false});materials.push(mat);
          const mesh=new THREE.Mesh(geom,mat);
          mesh.position.copy(toWorld(u.north_m,u.east_m,u.tvd_m));
          mesh.scale.set(Math.max(.05,u.semi_minor_2sigma_m),Math.max(.05,u.vertical_2sigma_m),Math.max(.05,u.semi_major_2sigma_m));
          mesh.rotation.y=THREE.MathUtils.degToRad(u.azimuth_major_deg);
          mesh.userData={kind:'uncertainty',md:u.md_m};scene.add(mesh);
        });
      };
      if(layers.subjectUncertainty)addUncertainty(subjectUncertainty,colors.subjectUncertainty);
      if(layers.offsetUncertainty)addUncertainty(offsetUncertainty,colors.offsetUncertainty);

      if(layers.closestApproach&&closestApproach&&visible(closestApproach.ref_pos_nev[2])&&visible(closestApproach.offset_pos_nev[2])){
        const a=toWorld(closestApproach.ref_pos_nev[0],closestApproach.ref_pos_nev[1],closestApproach.ref_pos_nev[2]);
        const b=toWorld(closestApproach.offset_pos_nev[0],closestApproach.offset_pos_nev[1],closestApproach.offset_pos_nev[2]);
        const line=makeLine([a,b],colors.closest,1,true);line.userData={kind:'closest-approach'};scene.add(line);
        for(const pos of [a,b]){
          const geom=new THREE.SphereGeometry(markerRadius*1.35,16,12);geometries.push(geom);
          const mat=new THREE.MeshStandardMaterial({color:colors.closest,emissive:0x3f0712,emissiveIntensity:.35});materials.push(mat);
          const mesh=new THREE.Mesh(geom,mat);mesh.position.copy(pos);scene.add(mesh);
        }
      }

      if(layers.stations){
        const stride=Math.max(1,Math.ceil(subject.length/110));
        subject.filter((p,i)=>(i%stride===0||i===subject.length-1)&&visible(p.tvd_m)).forEach(p=>{
          const isSelected=selectedMD!==null&&Math.abs(p.md_m-selectedMD)<1e-6;
          const geom=new THREE.SphereGeometry(markerRadius*(isSelected?1.65:.78),12,9);geometries.push(geom);
          const mat=new THREE.MeshStandardMaterial({color:isSelected?colors.selected:colors.subject,emissive:isSelected?0x7c2d12:0x062a3b,emissiveIntensity:isSelected?.55:.22});materials.push(mat);
          const mesh=new THREE.Mesh(geom,mat);mesh.position.copy(toWorld(engineeringNorth(p),engineeringEast(p),p.tvd_m));mesh.userData={kind:'station',md:p.md_m,selectable:true};scene.add(mesh);selectable.push(mesh);
        });
      }

      if(selectedMD!==null){
        const selected=subject.reduce((best,p)=>Math.abs(p.md_m-selectedMD)<Math.abs(best.md_m-selectedMD)?p:best,subject[0]);
        if(selected&&visible(selected.tvd_m)){
          const geom=new THREE.SphereGeometry(markerRadius*1.8,18,12);geometries.push(geom);
          const mat=new THREE.MeshStandardMaterial({color:colors.selected,emissive:0x9a3412,emissiveIntensity:.65});materials.push(mat);
          const marker=new THREE.Mesh(geom,mat);marker.position.copy(toWorld(engineeringNorth(selected),engineeringEast(selected),selected.tvd_m));scene.add(marker);
        }
      }

      const distance=Math.max(180,extent*1.35);
      if(cameraPreset==='plan'){camera.position.set(0,distance*1.25,.001);camera.up.set(0,0,1);}
      else if(cameraPreset==='north-section'){camera.position.set(distance,0,0);camera.up.set(0,1,0);}
      else if(cameraPreset==='east-section'){camera.position.set(0,0,distance);camera.up.set(0,1,0);}
      else{camera.position.set(distance*.78,distance*.58,distance*.78);camera.up.set(0,1,0);}
      camera.lookAt(0,0,0);

      controls=new OrbitControls(camera,renderer.domElement);
      controls.target.set(0,0,0);controls.enableDamping=true;controls.dampingFactor=.08;controls.screenSpacePanning=true;
      controls.minDistance=Math.max(5,extent*.03);controls.maxDistance=Math.max(1000,extent*12);controls.update();

      const raycaster=new THREE.Raycaster();raycaster.params.Line.threshold=Math.max(.5,extent*.006);
      const pointer=new THREE.Vector2();
      const onPointer=(ev:PointerEvent)=>{
        if(ev.button!==0)return;
        const rect=renderer.domElement.getBoundingClientRect();
        pointer.x=((ev.clientX-rect.left)/rect.width)*2-1;
        pointer.y=-((ev.clientY-rect.top)/rect.height)*2+1;
        raycaster.setFromCamera(pointer,camera);
        const hits=raycaster.intersectObjects(selectable,false);
        const md=hits[0]?.object?.userData?.md;
        if(typeof md==='number')onSelectMD(md);
      };
      renderer.domElement.addEventListener('pointerdown',onPointer);

      resizeObserver=new ResizeObserver(()=>{
        const w=Math.max(1,container.clientWidth),h=Math.max(1,container.clientHeight);
        camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h,false);
      });
      resizeObserver.observe(container);

      const animate=()=>{
        controls.update();
        renderer.render(scene,camera);
        setRenderInfo(v=>{
          const next={objects:scene.children.length,triangles:renderer.info.render.triangles};
          return v.objects===next.objects&&v.triangles===next.triangles?v:next;
        });
        frame=requestAnimationFrame(animate);
      };
      animate();

      return ()=>{
        cancelAnimationFrame(frame);resizeObserver?.disconnect();renderer.domElement.removeEventListener('pointerdown',onPointer);
        controls?.dispose();geometries.forEach(g=>g?.dispose?.());materials.forEach(m=>m?.dispose?.());renderer?.dispose?.();container.replaceChildren();
      };
    }catch(error){
      setFailure(error instanceof Error?error.message:String(error));
      return ()=>{cancelAnimationFrame(frame);resizeObserver?.disconnect();controls?.dispose?.();renderer?.dispose?.();};
    }
  },[
    subjectPoints,offsetPoints,formations,casings,targets,subjectUncertainty,offsetUncertainty,
    closestApproach,selectedMD,onSelectMD,layers,cameraPreset,clipTvdM
  ]);

  return <div className={'geodrill-webgl-host '+className}>
    <div ref={host} className="geodrill-webgl-canvas" aria-label="Interactive GeoDrill WebGL well scene"/>
    {failure&&<div className="webgl-failure"><strong>3D scene unavailable</strong><span>{failure}</span></div>}
    {!failure&&<div className="webgl-performance" aria-hidden="true">{renderInfo.objects} objects · {renderInfo.triangles.toLocaleString()} triangles</div>}
    <div className="webgl-axis-key" aria-hidden="true"><span><i className="axis-e"/>E</span><span><i className="axis-v"/>Up</span><span><i className="axis-n"/>N</span></div>
  </div>;
}
