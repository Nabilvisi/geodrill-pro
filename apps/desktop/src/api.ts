export async function api<T>(path:string, options:RequestInit={}):Promise<T> {
  const response=await fetch('/api'+path,{...options,headers:{'X-Geodrill-Client':'workstation',...(!(options.body instanceof FormData)?{'Content-Type':'application/json'}:{}),...options.headers}});
  if(!response.ok){const body=await response.json().catch(()=>({detail:'Service unavailable'}));throw new Error(typeof body.detail==='string'?body.detail:JSON.stringify(body.detail));}
  return response.json();
}
