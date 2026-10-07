import {useEffect,useState} from 'react';
import {api} from './api';

/** Freshness is an overlay. Historical calculation status and bytes stay fixed. */
export function CalculationFreshness({projectId,calculationId}:{projectId:string;calculationId?:string}){
  const [state,setState]=useState<{stale:boolean;reasons:string[]}|null>(null);
  useEffect(()=>{let active=true;setState(null);if(calculationId)api<Record<string,{stale:boolean;reasons:string[]}>>('/projects/'+projectId+'/calculation-dependencies').then(s=>{if(active)setState(s[calculationId]??null);}).catch(()=>{if(active)setState({stale:true,reasons:['Dependency state unavailable; reload before treating this record as current.']});});return()=>{active=false;};},[projectId,calculationId]);
  return state?.stale?<div className="alert warning" role="status"><strong>STALE calculation dependencies.</strong> {state.reasons.join(' ')} Historical result status remains preserved.</div>:null;
}
