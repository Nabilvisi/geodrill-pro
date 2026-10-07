"""Persisted wellbore survey/trajectory workflows; equations remain in kernels."""
import json
from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from starlette.concurrency import run_in_threadpool
from packages.domain.wellbore_revisions import (TrajectoryRole, SurveySave, AuthoredSurveySave, AdoptSurvey, TrajectorySave, UncertaintySave, ProximitySave)
from services.application.wellbore_revisions import WellboreRevisionService
from services.api.storage import RevisionConflict

router=APIRouter(prefix='/api/v1/wellbores/{wellbore_id}',tags=['Wellbore revisions'])


def service(request):
    return WellboreRevisionService(request.app.state.store)


def mutation(request, fn):
    try:
        with request.app.state.mutation_lock:
            return fn()
    except RevisionConflict as error:
        raise HTTPException(409,str(error)) from error


@router.get('/directional-context')
def context(request:Request,wellbore_id:str,trajectory_type:TrajectoryRole='planned'):
    return service(request).context(wellbore_id,trajectory_type)


@router.get('/surveys')
def surveys(request:Request,wellbore_id:str,trajectory_type:TrajectoryRole|None=None):
    return service(request).records(wellbore_id,'survey',trajectory_type)


@router.get('/trajectories')
def trajectories(request:Request,wellbore_id:str,trajectory_type:TrajectoryRole|None=None):
    return service(request).records(wellbore_id,'trajectory',trajectory_type)


@router.get('/revisions/{revision_id}')
def revision(request:Request,wellbore_id:str,revision_id:str):
    svc=service(request);value=svc.get(wellbore_id,revision_id)
    return {'revision':value,'freshness':svc.freshness(value)}


@router.post('/surveys',status_code=201)
async def authored(request:Request,wellbore_id:str,body:AuthoredSurveySave):
    if body.evidence_state not in {'authored_design','synthetic'}:
        raise HTTPException(422,'Use an original source import for observations; authored stations are design or synthetic evidence.')
    raw=await request.body()
    return await run_in_threadpool(mutation,request,lambda:service(request).import_survey(wellbore_id,body,'authored-survey.json',raw,authored=True))


@router.post('/surveys/import',status_code=201)
async def imported(request:Request,wellbore_id:str,metadata:str=Form(...),file:UploadFile=File(...)):
    raw=await file.read(2*1024*1024+1);await file.close()
    if len(raw)>2*1024*1024:raise HTTPException(413,'Survey exceeds 2 MiB.')
    filename=(file.filename or '').replace('\\','/').split('/')[-1][:160]
    if not filename.lower().endswith('.csv'):raise HTTPException(422,'Survey imports require a CSV file with explicit units.')
    body=SurveySave.model_validate(json.loads(metadata))
    return await run_in_threadpool(mutation,request,lambda:service(request).import_survey(wellbore_id,body,filename,raw))


@router.post('/surveys/from-dataset',status_code=201)
def adopted(request:Request,wellbore_id:str,body:AdoptSurvey):
    return mutation(request,lambda:service(request).save_survey(wellbore_id,body,body.dataset_id))


@router.post('/trajectories',status_code=201)
def calculated(request:Request,wellbore_id:str,body:TrajectorySave):
    return mutation(request,lambda:service(request).save_trajectory(wellbore_id,body))


@router.post('/uncertainty',status_code=201)
def uncertainty(request:Request,wellbore_id:str,body:UncertaintySave):
    return mutation(request,lambda:service(request).save_uncertainty(wellbore_id,body))


@router.post('/anticollision/calculate',status_code=201)
def proximity(request:Request,wellbore_id:str,body:ProximitySave):
    return mutation(request,lambda:service(request).save_proximity(wellbore_id,body))
