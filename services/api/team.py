"""Team-mode HTTP routes: login, users, and the programme review workflow.

Only mounted when GEODRILL_MODE=team. The caller (main.py middleware) authenticates the
Bearer token and places the user on ``request.state.user`` before any of these run.
"""
from typing import Any
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from . import access, auth, programmes
from .storage import Store


class LoginIn(BaseModel):
    username: str = Field(max_length=64)
    password: str = Field(max_length=256)


class UserIn(BaseModel):
    username: str
    display_name: str = Field(max_length=120)
    role: str
    password: str = Field(max_length=256)


class ActiveIn(BaseModel):
    active: bool


class ProgrammeIn(BaseModel):
    title: str = Field(max_length=200)
    content: dict[str, Any]
    evidence_bindings: list[dict[str, Any]] | None = None


class VersionIn(BaseModel):
    content: dict[str, Any]
    evidence_bindings: list[dict[str, Any]] | None = None


class ActionIn(BaseModel):
    note: str = Field(default="", max_length=2000)


class MemberIn(BaseModel):
    user_id: str = Field(max_length=64)


def bearer(request: Request) -> str | None:
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    return token.strip() if scheme.lower() == "bearer" and token.strip() else None


def build_router(store: Store) -> APIRouter:
    router = APIRouter()

    def me(request: Request) -> dict:
        user = getattr(request.state, "user", None)
        if not user:
            raise HTTPException(401, "Sign in required")
        return user

    def admin(request: Request) -> dict:
        user = me(request)
        if user["role"] != "admin":
            raise HTTPException(403, "Administrator role required")
        return user

    @router.post("/api/team/login")
    def login(value: LoginIn):
        try:
            token, user = auth.login(store, value.username, value.password)
        except auth.AuthError as error:
            raise HTTPException(401, str(error))
        return {"token": token, "token_type": "bearer", "expires_in_hours": auth.SESSION_HOURS, "user": user}

    @router.post("/api/team/logout")
    def logout(request: Request):
        me(request)
        auth.logout(store, bearer(request))
        return {"status": "signed out"}

    @router.get("/api/team/me")
    def whoami(request: Request):
        return me(request)

    @router.get("/api/team/users")
    def users(request: Request):
        admin(request)
        return auth.list_users(store)

    @router.post("/api/team/users", status_code=201)
    def add_user(value: UserIn, request: Request):
        actor = admin(request)
        return auth.create_user(store, value.username, value.display_name, value.role, value.password, actor=f"user:{actor['username']}")

    @router.post("/api/team/users/{user_id}/active")
    def set_active(user_id: str, value: ActiveIn, request: Request):
        actor = admin(request)
        if user_id == actor["id"] and not value.active:
            raise HTTPException(422, "You cannot deactivate your own account")
        return auth.set_active(store, user_id, value.active, f"user:{actor['username']}")

    @router.post("/api/projects/{project_id}/programmes", status_code=201)
    def create_programme(project_id: str, value: ProgrammeIn, request: Request):
        user = me(request)
        access.require_member(store, user, project_id)
        bindings = value.evidence_bindings if value.evidence_bindings is not None else value.content.get("evidence_bindings")
        return programmes.create_programme(store, project_id, value.title, value.content, user, evidence_bindings=bindings)

    @router.get("/api/projects/{project_id}/programmes")
    def list_programmes(project_id: str, request: Request):
        access.require_member(store, me(request), project_id)
        return programmes.list_programmes(store, project_id)

    @router.get("/api/team/programmes/{programme_id}")
    def get_programme(programme_id: str, request: Request):
        access.require_member(store, me(request), access.project_for_programme(store, programme_id))
        return programmes.get_programme(store, programme_id)

    @router.post("/api/team/programmes/{programme_id}/versions", status_code=201)
    def new_version(programme_id: str, value: VersionIn, request: Request):
        user = me(request)
        access.require_member(store, user, access.project_for_programme(store, programme_id))
        bindings = value.evidence_bindings if value.evidence_bindings is not None else value.content.get("evidence_bindings")
        return programmes.new_version(store, programme_id, value.content, user, evidence_bindings=bindings)

    @router.post("/api/team/versions/{version_id}/actions/{action}")
    def act(version_id: str, action: str, value: ActionIn, request: Request):
        user = me(request)
        access.require_member(store, user, access.project_for_version(store, version_id))
        return programmes.act(store, version_id, action, user, value.note)

    @router.get("/api/team/versions/{version_id}/verify")
    def verify(version_id: str, request: Request):
        access.require_member(store, me(request), access.project_for_version(store, version_id))
        return programmes.verify_version(store, version_id)

    @router.get("/api/projects/{project_id}/members")
    def members(project_id: str, request: Request):
        access.require_member(store, me(request), project_id)
        return access.list_members(store, project_id)

    @router.post("/api/projects/{project_id}/members", status_code=201)
    def add_member(project_id: str, value: MemberIn, request: Request):
        actor = admin(request)
        access.add_member(store, project_id, value.user_id, actor)
        return access.list_members(store, project_id)

    @router.delete("/api/projects/{project_id}/members/{user_id}")
    def remove_member(project_id: str, user_id: str, request: Request):
        actor = admin(request)
        access.remove_member(store, project_id, user_id, actor)
        return access.list_members(store, project_id)

    return router

