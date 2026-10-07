/* Transport only: calculations and eligibility remain in the original Python API. */
(() => {
  window.GEODRILL_CLOUD = true;
  const nativeFetch = window.fetch.bind(window);
  const pending = new Map(); const queued = [];
  let inFlight = false, ready = false, serial = 0;
  const instance = crypto.randomUUID();
  const send = (type, data) => parent.postMessage({isStreamlitMessage:true,type,...data}, "*");
  const base64 = bytes => {let value="";for(let i=0;i<bytes.length;i+=8192)value+=String.fromCharCode(...bytes.subarray(i,i+8192));return btoa(value);};
  const flush = () => {
    if (!ready || inFlight || !queued.length) return;
    const requests = queued.splice(0,32); inFlight=true;
    send("streamlit:setComponentValue", {value:{batch_id:instance+":"+serial,requests},dataType:"json"});
  };
  window.addEventListener("message",event => {
    if(event.source !== parent || event.data?.type !== "streamlit:render")return;
    ready=true; let received=false;
    for(const result of event.data.args.responses??[]){
      const waiter=pending.get(result.id);if(!waiter)continue;
      pending.delete(result.id);received=true;clearTimeout(waiter.timer);
      const bytes=Uint8Array.from(atob(result.body_base64),c=>c.charCodeAt(0));
      waiter.resolve(new Response([204,304].includes(result.status)?null:bytes,{status:result.status,headers:result.headers}));
    }
    if(received)inFlight=false;
    flush();
  });
  window.fetch = async (input, options={}) => {
    const url=new URL(typeof input==="string"?input:input.url,location.href);
    if(url.origin!==location.origin || !url.pathname.startsWith("/api/"))return nativeFetch(input,options);
    const req={id:instance+":"+(++serial),path:url.pathname+url.search,method:options.method??"GET"};
    const headers=new Headers(options.headers??{});req.headers={};
    for(const name of ['x-geodrill-wellbore','x-geodrill-trajectory-type']){
      const value=headers.get(name);if(value!==null)req.headers[name]=value;
    }
    if(options.body instanceof FormData){
      req.form=[];
      for(const [name,value] of options.body.entries()){
        if(value instanceof File){if(value.size>2097152)throw Error("File exceeds the 2 MiB limit.");req.form.push({name,filename:value.name,type:value.type,file_base64:base64(new Uint8Array(await value.arrayBuffer()))});}
        else req.form.push({name,value:String(value)});
      }
    }else if(options.body!==undefined)req.body=String(options.body);
    return new Promise((resolve,reject)=>{
      const timer=setTimeout(()=>{pending.delete(req.id);reject(Error("Cloud request timed out; reconnect and reopen saved evidence before retrying."));},90000);
      pending.set(req.id,{resolve,reject,timer});queued.push(req);queueMicrotask(flush);
    });
  };
  document.addEventListener("click",event=>{
    const link=event.target.closest?.("a[href]");if(!link)return;
    const url=new URL(link.href,location.href);if(url.origin!==location.origin || !url.pathname.startsWith("/api/"))return;
    event.preventDefault();
    window.fetch(url.pathname+url.search).then(async response=>{
      if(!response.ok)throw Error("Export failed: "+response.status);
      const blob=await response.blob();const a=document.createElement("a");
      a.href=URL.createObjectURL(blob);
      a.download=link.download || /filename="([^"]+)"/.exec(response.headers.get("content-disposition")??"")?.[1] || "geodrill-export";
      document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(a.href),30000);
    }).catch(error=>alert(error.message));
  },true);
  send("streamlit:componentReady",{apiVersion:1});
  send("streamlit:setFrameHeight",{height:1100});
})();
