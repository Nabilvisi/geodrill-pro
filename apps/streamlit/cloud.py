"""Session-isolated transport for the existing audited workstation in Streamlit."""
from __future__ import annotations
import base64,copy,hashlib,json,tempfile
from pathlib import Path
from urllib.parse import urlsplit,unquote
from fastapi.testclient import TestClient
from services.api.main import create_app

MAX_BODY=2*1024*1024
MAX_BATCH=32

class Workspace:
    def __init__(self,seed=True):
        self._temporary=tempfile.TemporaryDirectory(prefix="geodrill-cloud-")
        self.root=Path(self._temporary.name)
        self.app=create_app(self.root)
        self.client=TestClient(self.app)
        self.client.headers["X-Geodrill-Client"]="workstation"
        self.client.get("/api/session").raise_for_status()
        self.responses={}
        self.request_hashes={}
        self.latest=[]
        self.report_downloads={}
        if seed:self.seed()

    def call(self,method,path,**kw):
        r=self.client.request(method,path,**kw);r.raise_for_status();return r.json()

    def seed(self):
        self.call("POST","/api/demo")
        p=self.call("POST","/api/projects",json={"name":"Cloud verification · Synthetic","well_name":"Generated research well","datum":"RKB synthetic","bit_diameter_m":.216,"origin":"synthetic"})
        b="/api/projects/"+p["id"]
        ds=self.call("POST",b+"/imports",data={"kind":"survey"},files={"file":("synthetic-vertical.csv",b"md[m],inclination[deg],azimuth[deg]\n0,0,0\n500,0,0\n1000,0,0\n","text/csv")})
        g={"survey_dataset_id":ds["id"],"datum":p["datum"],"coordinate_reference":"Synthetic local frame","wellhead_north_m":0.,"wellhead_east_m":0.,"wellhead_elevation_m":0.,"survey_quality_note":"Generated vertical stations","tool_to_bit_offset_m":0.,"formations":[],"hole_sections":[{"name":"Synthetic hole","top_md_m":0.,"bottom_md_m":1000.,"diameter_m":.3,"source":"Generated hole assumption"}],"casings":[{"name":"Synthetic planned casing","top_md_m":0.,"bottom_md_m":1000.,"outside_diameter_m":.244,"inside_diameter_m":.216,"minimum_wall_m":.014,"wall_loss_allowance_m":0.,"state":"planned","grade":"Synthetic nominal material","source":"Generated geometry","yield_strength_pa":690e6,"body_rating_source":"Generated property, no material certificate"}]}
        rev=self.call("POST",b+"/geometry",json={"geometry":g,"base_revision_id":None,"change_note":"Generated cloud demonstration geometry"})
        for model in ["dynamics","bit-condition","wear-fatigue","anomaly","gas-phase","supervision"]:
            value=self.call("GET",b+"/research/"+model+"/template/"+rev["id"])
            value["study_name"]="Synthetic cloud "+model+" study"
            imported=self.call("POST",b+"/research/"+model+"/imports",files={"file":(model+"-synthetic.json",json.dumps(value).encode(),"application/json")})
            self.call("POST",b+"/calculations/"+model,json=imported["inputs_si"])

    @staticmethod
    def _encode(identifier,response):
        return {"id":identifier,"status":response.status_code,
                "headers":{k:v for k,v in response.headers.items() if k.lower() in {"content-type","content-disposition"}},
                "body_base64":base64.b64encode(response.content).decode()}

    def execute(self,request):
        if not isinstance(request,dict):raise ValueError("Request must be an object.")
        identifier=request.get("id")
        if not isinstance(identifier,str) or not identifier or len(identifier)>120:raise ValueError("Invalid request identity.")
        fingerprint=hashlib.sha256(json.dumps(request,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
        if identifier in self.responses:
            if self.request_hashes[identifier]!=fingerprint:raise ValueError("Request identity was reused with changed content.")
            return copy.deepcopy(self.responses[identifier])
        path=request.get("path","")
        if not isinstance(path,str) or len(path)>3000:raise ValueError("Invalid API path.")
        u=urlsplit(path)
        if u.scheme or u.netloc or u.fragment or not u.path.startswith("/api/") or "\\" in path or ".." in unquote(u.path).split("/"):raise ValueError("Only this workspace's relative API routes are allowed.")
        method=request.get("method","GET").upper()
        if method not in {"GET","POST","PUT","PATCH","DELETE"}:raise ValueError("Unsupported method.")
        kw={}
        body=request.get("body")
        if body is not None:
            if not isinstance(body,str) or len(body.encode())>MAX_BODY:raise ValueError("Request body exceeds the 2 MiB limit.")
            kw["content"]=body.encode();kw["headers"]={"Content-Type":"application/json"}
        form=request.get("form")
        if form is not None:
            if body is not None or not isinstance(form,list) or len(form)>20:raise ValueError("Invalid multipart request.")
            data={};files=[];size=0
            for part in form:
                if not isinstance(part,dict) or not isinstance(part.get("name"),str) or len(part["name"])>100:raise ValueError("Invalid form field.")
                if "file_base64" in part:
                    encoded=part["file_base64"]
                    if not isinstance(encoded,str) or len(encoded)>MAX_BODY*4//3+4:raise ValueError("File exceeds the 2 MiB limit.")
                    raw=base64.b64decode(encoded,validate=True);size+=len(raw)
                    filename=str(part.get("filename","input"))[:160]
                    files.append((part["name"],(filename,raw,str(part.get("type","application/octet-stream"))[:100])))
                else:
                    value=part.get("value")
                    if not isinstance(value,str):raise ValueError("Invalid form value.")
                    size+=len(value.encode());data[part["name"]]=value
            if size>MAX_BODY+65536:raise ValueError("Multipart input exceeds the 2 MiB limit.")
            kw.update(data=data,files=files)
        response=self.client.request(method,path,**kw)
        # Keep the original immutable export bytes for Streamlit's native HTTP
        # download control as well as the embedded workstation's blob link.
        disposition=response.headers.get("content-disposition","")
        if (method=="GET" and response.status_code==200 and u.path.endswith("/download")
                and disposition.startswith('attachment; filename="geodrill-report-')
                and disposition.endswith('.json"')):
            filename=disposition.split('"')[1]
            self.report_downloads[filename]=response.content
            while len(self.report_downloads)>3:
                self.report_downloads.pop(next(iter(self.report_downloads)))
        result=self._encode(identifier,response)
        self.responses[identifier]=result
        self.request_hashes[identifier]=fingerprint
        if len(self.responses)>2048:
            oldest=next(iter(self.responses));self.responses.pop(oldest);self.request_hashes.pop(oldest)
        return copy.deepcopy(result)

    def batch(self,value):
        if not isinstance(value,dict) or not isinstance(value.get("requests"),list) or len(value["requests"])>MAX_BATCH:raise ValueError("Invalid request batch.")
        results=[]
        for req in value["requests"]:
            try:results.append(self.execute(req))
            except (ValueError,TypeError,AttributeError) as error:
                identifier=req.get("id","invalid") if isinstance(req,dict) else "invalid"
                results.append({"id":identifier,"status":422,"headers":{"content-type":"application/json"},"body_base64":base64.b64encode(json.dumps({"detail":str(error)}).encode()).decode()})
        self.latest=results
        return results

    def close(self):
        self.client.close();self._temporary.cleanup()
