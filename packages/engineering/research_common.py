"""Shared typed research inputs and bounded numerical tools for Modules 12–17."""
import math
from typing import Literal
from pydantic import Field
from .models import Contract

class StudyInput(Contract):
    input_dataset_id: str | None = Field(default=None,min_length=1,max_length=80)
    study_name: str = Field(min_length=3,max_length=100)
    geometry_revision_id: str
    depth_datum: str
    evidence_state: Literal["unknown","supplied","synthetic"]="unknown"
    source_note: str = Field(min_length=3,max_length=500)

def base(module,scope,limitations):
    return {"model_version":module,"scope":scope,"approval_issued":False,"equipment_authority":"none",
            "status":"research_scenario","reasons":[],"limitations":limitations,"profile":[],"history":[]}

def solve(matrix,rhs):
    n=len(rhs);a=[list(row)+[value] for row,value in zip(matrix,rhs)]
    for k in range(n):
        pivot=max(range(k,n),key=lambda i:abs(a[i][k]));a[k],a[pivot]=a[pivot],a[k]
        if abs(a[k][k])<1e-16:raise ValueError("Singular matrix.")
        scale=a[k][k];a[k]=[x/scale for x in a[k]]
        for i in range(n):
            if i!=k:
                scale=a[i][k];a[i]=[x-scale*y for x,y in zip(a[i],a[k])]
    return [row[-1] for row in a]

def eigen_symmetric(matrix):
    n=len(matrix);a=[list(r) for r in matrix];vectors=[[float(i==j) for j in range(n)] for i in range(n)]
    for iteration in range(100):
        p,q=max(((i,j) for i in range(n) for j in range(i+1,n)),key=lambda ij:abs(a[ij[0]][ij[1]]))
        if abs(a[p][q])<1e-14*max(1.,max(abs(a[i][i]) for i in range(n))):break
        angle=.5*math.atan2(2*a[p][q],a[q][q]-a[p][p]);c=math.cos(angle);s=math.sin(angle)
        app,aqq,apq=a[p][p],a[q][q],a[p][q]
        for j in range(n):
            if j not in (p,q):
                x,y=a[j][p],a[j][q];a[j][p]=a[p][j]=c*x-s*y;a[j][q]=a[q][j]=s*x+c*y
            x,y=vectors[j][p],vectors[j][q];vectors[j][p]=c*x-s*y;vectors[j][q]=s*x+c*y
        a[p][p]=c*c*app-2*s*c*apq+s*s*aqq
        a[q][q]=s*s*app+2*s*c*apq+c*c*aqq;a[p][q]=a[q][p]=0.
    else:raise ValueError("Modal eigensolver did not converge.")
    return sorted((a[i][i],[vectors[j][i] for j in range(n)]) for i in range(n))

def rms(values):
    return math.sqrt(sum(x*x for x in values)/len(values)) if values else None
