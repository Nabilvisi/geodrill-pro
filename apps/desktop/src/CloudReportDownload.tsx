import React, {useEffect, useState} from 'react';
import {ArrowDownToLine, LoaderCircle} from 'lucide-react';

// Prepare the original backend bytes before offering a native download link.
// Reserializing the parsed report in JavaScript can change numeric JSON tokens
// and therefore break its canonical Python snapshot fingerprint.
export function CloudReportDownload({path,name}:{path:string;name:string}) {
  const [href,setHref]=useState<string|null>(null);
  const [error,setError]=useState('');
  useEffect(()=>{
    let cancelled=false; let url:string|null=null;
    window.fetch(path).then(async response=>{
      if(!response.ok)throw new Error('Report export returned '+response.status);
      const blob=await response.blob();
      if(cancelled)return;
      url=URL.createObjectURL(blob);setHref(url);
    }).catch(cause=>{if(!cancelled)setError((cause as Error).message);});
    return ()=>{cancelled=true;if(url)URL.revokeObjectURL(url);};
  },[path]);
  if(error)return <p className="small-note" role="alert">{error}. Reopen the report to retry.</p>;
  return <a className="button primary" href={href??undefined} download={name}
    aria-disabled={!href} onClick={event=>{if(!href)event.preventDefault();}}>
    {href?<ArrowDownToLine size={16}/>:<LoaderCircle className="spin" size={16}/>}
    {href?'Download complete JSON':'Preparing download…'}
  </a>;
}
