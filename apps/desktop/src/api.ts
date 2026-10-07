export async function api<T>(path:string, options:RequestInit={}):Promise<T> {
  const response=await fetch('/api'+path,{...options,headers:{'X-Geodrill-Client':'workstation',...(!(options.body instanceof FormData)?{'Content-Type':'application/json'}:{}),...options.headers}});
  if(!response.ok){const body=await response.json().catch(()=>({detail:'Service unavailable'}));throw new Error(typeof body.detail==='string'?body.detail:JSON.stringify(body.detail));}
  return response.json();
}

export type EngineeringScope={wellboreId?:string;trajectoryRole?:string};
export const scopeQuery=({wellboreId,trajectoryRole}:EngineeringScope)=>wellboreId?'&wellbore_id='+encodeURIComponent(wellboreId)+'&trajectory_type='+encodeURIComponent(trajectoryRole??'planned'):'';
export function engineeringApi(scope:EngineeringScope){
  return <T,>(path:string,options:RequestInit={}):Promise<T>=>api<T>(path,{...options,headers:{...(scope.wellboreId?{'X-Geodrill-Wellbore':scope.wellboreId,'X-Geodrill-Trajectory-Type':scope.trajectoryRole??'planned'}:{}),...options.headers}});
}
