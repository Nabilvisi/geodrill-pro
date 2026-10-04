"""Bounded native-depth exploratory clustering; no facies classification."""
import math
import random
from collections import Counter
from typing import Literal
from pydantic import Field, model_validator
from .models import Contract


class LogFeature(Contract):
    curve: str = Field(min_length=1, max_length=80)
    unit: str = Field(min_length=1, max_length=40)
    transform: Literal["identity", "log10"] = "identity"
    minimum: float = Field(ge=-1e12, le=1e12)
    maximum: float = Field(ge=-1e12, le=1e12)
    range_basis: str = Field(min_length=3, max_length=300)

    @model_validator(mode="after")
    def range(self):
        if self.maximum <= self.minimum:
            raise ValueError("Feature maximum must exceed minimum.")
        if self.transform == "log10" and self.minimum <= 0:
            raise ValueError("Log10 features require a strictly positive declared range.")
        return self


class ClusteringInput(Contract):
    dataset_id: str = Field(min_length=1, max_length=80)
    geometry_revision_id: str = Field(min_length=1, max_length=80)
    depth_datum: str = Field(min_length=1, max_length=100)
    maximum_native_gap_m: float = Field(ge=.0001, le=1000)
    study_name: str = Field(min_length=3, max_length=100)
    features: list[LogFeature] = Field(min_length=1, max_length=8)
    clusters: int = Field(ge=2, le=8)
    seed: int = Field(ge=0, le=2147483647)
    fit_top_md_m: float = Field(ge=0, le=30000)
    fit_bottom_md_m: float = Field(gt=0, le=30000)
    depth_alignment_note: str = Field(min_length=3, max_length=400)
    correction_status: Literal["corrected", "raw", "unknown"]
    correction_note: str = Field(min_length=3, max_length=400)
    acquisition_quality_note: str = Field(min_length=3, max_length=400)
    max_iterations: int = Field(default=100, ge=1, le=200)

    @model_validator(mode="after")
    def distinct(self):
        if len({f.curve for f in self.features}) != len(self.features):
            raise ValueError("Selected curves must be unique.")
        if self.fit_bottom_md_m <= self.fit_top_md_m:
            raise ValueError("Training bottom must exceed top MD.")
        return self


def squared(a, b):
    return math.fsum((x-y)**2 for x,y in zip(a,b))


def lloyd(points, k, seed, max_iterations):
    """k-means++ sampling then Lloyd iteration, exact label convergence."""
    rng=random.Random(seed)
    centers=[list(points[rng.randrange(len(points))])]
    for _ in range(1,k):
        weights=[min(squared(p,c) for c in centers) for p in points]
        total=math.fsum(weights)
        if total <= 0:
            return None
        target=rng.random()*total
        cumulative=0.
        selected=len(points)-1
        for index,weight in enumerate(weights):
            cumulative += weight
            if weight > 0 and cumulative > target:
                selected=index
                break
        centers.append(list(points[selected]))
    previous=None
    for iteration in range(1,max_iterations+1):
        labels=[min(range(k),key=lambda j:squared(p,centers[j])) for p in points]
        groups=[[p for p,label in zip(points,labels) if label==j] for j in range(k)]
        if any(not g for g in groups):
            return None  # No silent removal or invented empty-cluster center.
        centers=[[math.fsum(p[d] for p in group)/len(group) for d in range(len(points[0]))] for group in groups]
        if labels == previous:
            break
        previous=labels
    # Verify that the reported centers and assignments agree.
    final=[min(range(k),key=lambda j:squared(p,centers[j])) for p in points]
    converged=final==labels
    inertia=math.fsum(squared(p,centers[label]) for p,label in zip(points,final))
    return {"centers":centers,"labels":final,"inertia":inertia,"iterations":iteration,"converged":converged,"seed":seed}


def adjusted_rand(a,b):
    choose=lambda n:n*(n-1)/2
    pairs=choose(len(a))
    if not pairs:
        return 1.
    cell=math.fsum(choose(n) for n in Counter(zip(a,b)).values())
    left=math.fsum(choose(n) for n in Counter(a).values())
    right=math.fsum(choose(n) for n in Counter(b).values())
    expected=left*right/pairs
    maximum=(left+right)/2
    return 1. if abs(maximum-expected)<1e-14 else (cell-expected)/(maximum-expected)


def cluster_logs(value:ClusteringInput, rows, curves, total_md):
    if len(rows)>2500:
        raise ValueError("Exploratory clustering is bounded to 2,500 native-depth records; no automatic downsampling.")
    if value.fit_bottom_md_m > total_md:
        raise ValueError("Training interval extends beyond the saved survey.")
    units={c["mnemonic"]:c["unit"] for c in curves[1:]}
    features=sorted(value.features,key=lambda f:f.curve)
    for f in features:
        if f.curve not in units or units[f.curve]!=f.unit:
            raise ValueError(f"Curve {f.curve} and exact source unit {f.unit} must match LAS metadata.")
    ordered=sorted(enumerate(rows),key=lambda item:item[1]["depth_m"])
    output=[]
    vectors={}
    for source_index,row in ordered:
        md=row["depth_m"]
        reasons=[]
        if md>total_md:
            reasons.append("Outside saved survey depth coverage")
        vector=[]
        for f in features:
            x=row.get(f.curve)
            if x is None:
                reasons.append("Missing "+f.curve)
            elif not math.isfinite(x) or not f.minimum<=x<=f.maximum:
                reasons.append("Outside declared range: "+f.curve)
            else:
                vector.append(math.log10(x) if f.transform=="log10" else x)
        result={"source_index":source_index,"depth_m":md,"cluster":None,"distance":None,"status":"withheld" if reasons else "eligible","reason":"; ".join(reasons)}
        output.append(result)
        if not reasons:
            vectors[source_index]=vector
    train=[r for r in output if r["source_index"] in vectors and value.fit_top_md_m<=r["depth_m"]<=value.fit_bottom_md_m]
    warnings=["Clusters describe log response, not confirmed lithology. Distances are not geological probabilities.",
              "Native sample depths are preserved; no interpolation, tool-response correction or depth shifting is performed.",
              "Labels are sorted by feature-center coordinates for this run; IDs do not transfer geological meaning across runs.",
              "Range checks use supplied envelopes; they are not a validated domain-shift detector.",
              "Initialization agreement does not measure facies accuracy or stability to measurement noise."]
    if value.correction_status!="corrected":
        warnings.append("Environmental/tool corrections are "+value.correction_status+"; results require specialist review.")
    base={"model":"native-log-kmeans","version":"0.1.0","status":"insufficient_data","facies_confirmation":False,
          "rows":output,"centers":[],"scaling":[],"intervals":[],"warnings":warnings,"training_count":len(train),
          "excluded_count":sum(r["status"]=="withheld" for r in output),"seed":value.seed,"initializations":[],
          "distance_definition":"Euclidean distance after transform and training-population standardization"}
    if len(train)<2*value.clusters:
        return {**base,"reason":"At least two complete in-range training observations per requested cluster are required."}
    points=[vectors[r["source_index"]] for r in train]
    means=[math.fsum(p[d] for p in points)/len(points) for d in range(len(features))]
    scales=[math.sqrt(math.fsum((p[d]-means[d])**2 for p in points)/len(points)) for d in range(len(features))]
    if any(s<=1e-12 for s in scales):
        return {**base,"reason":"A selected training feature has zero or numerically negligible variance; revise the feature selection explicitly."}
    normalize=lambda p:[(x-m)/s for x,m,s in zip(p,means,scales)]
    z=[normalize(p) for p in points]
    if len({tuple(p) for p in z})<value.clusters:
        return {**base,"reason":"Fewer distinct complete training vectors than requested clusters."}
    runs=[lloyd(z,value.clusters,value.seed+i,value.max_iterations) for i in range(3)]
    valid=[r for r in runs if r is not None and r["converged"]]
    base["initializations"]=[{"seed":value.seed+i,"status":"empty_cluster" if r is None else "converged" if r["converged"] else "not_converged",
                              "inertia":None if r is None else r["inertia"],"iterations":None if r is None else r["iterations"]} for i,r in enumerate(runs)]
    if not valid:
        return {**base,"status":"withheld","reason":"No initialization reached a nonempty, assignment-consistent solution."}
    best=min(valid,key=lambda r:(r["inertia"],r["seed"]))
    rank=sorted(range(value.clusters),key=lambda j:tuple(best["centers"][j]))
    centers=[best["centers"][j] for j in rank]
    for i,c in enumerate(centers):
        responses={f.curve:(10**(x*s+m) if f.transform=="log10" else x*s+m) for f,x,m,s in zip(features,c,means,scales)}
        base["centers"].append({"cluster":i+1,"standardized":c,"response_centers":responses,
                                "training_count":best["labels"].count(rank[i])})
    for r in output:
        if r["source_index"] in vectors:
            p=normalize(vectors[r["source_index"]])
            label=min(range(value.clusters),key=lambda j:squared(p,centers[j]))
            r.update(cluster=label+1,distance=math.sqrt(squared(p,centers[label])),status="exploratory",
                     reason="Within supplied feature envelope; facies interpretation unconfirmed.")
    # Intervals are bounded by native samples; gaps/withheld rows end a run.
    interval=None
    for r in output:
        if r["cluster"] is None:
            interval=None
        elif interval is None or interval["cluster"]!=r["cluster"] or r["depth_m"]-interval["last_sample_md_m"]>value.maximum_native_gap_m:
            interval={"cluster":r["cluster"],"first_sample_md_m":r["depth_m"],"last_sample_md_m":r["depth_m"],"sample_count":1}
            base["intervals"].append(interval)
        else:
            interval["last_sample_md_m"]=r["depth_m"]
            interval["sample_count"]+=1
    return {**base,"status":"exploratory","reason":"Unsupervised grouping with supplied acquisition and applicability evidence.",
            "selected_seed":best["seed"],"inertia":best["inertia"],
            "initialization_agreement_min_ari":min(adjusted_rand(best["labels"],r["labels"]) for r in valid),
            "scaling":[{"curve":f.curve,"unit":f.unit,"transform":f.transform,"training_mean":m,"training_population_std":s}
                       for f,m,s in zip(features,means,scales)]}
