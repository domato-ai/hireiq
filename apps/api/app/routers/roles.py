from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import CurrentUser, get_current_user
from app.middleware.entitlements import require_role_quota
from app.models.role import Role
from app.models.workspace import Workspace
from app.services.storage import StorageService

router = APIRouter(prefix="/workspaces/{workspace_id}/roles", tags=["roles"])

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class RoleCreate(BaseModel):
    title: str
    description: str | None = None


class RoleUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None


class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    title: str
    description: str | None
    requirements_json: dict[str, Any] | None
    status: str
    jd_blob_url: str | None
    created_at: Any


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _resolve_workspace(
    workspace_id: uuid.UUID,
    user: CurrentUser,
    db: AsyncSession,
) -> Workspace:
    result = await db.execute(
        select(Workspace).where(
            Workspace.id == workspace_id,
            Workspace.owner_id == user.id,
        )
    )
    ws = result.scalar_one_or_none()
    if ws is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found.")
    return ws


async def _get_role_or_404(role_id: uuid.UUID, workspace_id: uuid.UUID, db: AsyncSession) -> Role:
    result = await db.execute(
        select(Role).where(Role.id == role_id, Role.workspace_id == workspace_id)
    )
    role = result.scalar_one_or_none()
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")
    return role


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=list[RoleOut], summary="List roles in a workspace")
async def list_roles(
    workspace_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    await _resolve_workspace(workspace_id, current_user, db)
    result = await db.execute(
        select(Role)
        .where(Role.workspace_id == workspace_id)
        .order_by(Role.created_at.desc())
    )
    return result.scalars().all()


@router.post(
    "",
    response_model=RoleOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a role",
    dependencies=[Depends(require_role_quota)],
)
async def create_role(
    workspace_id: uuid.UUID,
    payload: RoleCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    await _resolve_workspace(workspace_id, current_user, db)
    role = Role(
        workspace_id=workspace_id,
        title=payload.title,
        description=payload.description,
    )
    db.add(role)
    await db.flush()
    await db.refresh(role)
    return role


@router.get("/{role_id}", response_model=RoleOut, summary="Get a role by ID")
async def get_role(
    workspace_id: uuid.UUID,
    role_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    await _resolve_workspace(workspace_id, current_user, db)
    return await _get_role_or_404(role_id, workspace_id, db)


@router.patch("/{role_id}", response_model=RoleOut, summary="Update a role")
async def update_role(
    workspace_id: uuid.UUID,
    role_id: uuid.UUID,
    payload: RoleUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    await _resolve_workspace(workspace_id, current_user, db)
    role = await _get_role_or_404(role_id, workspace_id, db)

    if payload.title is not None:
        role.title = payload.title
    if payload.description is not None:
        role.description = payload.description
    if payload.status is not None:
        role.status = payload.status

    await db.flush()
    await db.refresh(role)
    return role


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a role", response_model=None)
async def delete_role(
    workspace_id: uuid.UUID,
    role_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    await _resolve_workspace(workspace_id, current_user, db)
    role = await _get_role_or_404(role_id, workspace_id, db)
    await db.delete(role)


@router.post(
    "/{role_id}/jd",
    response_model=RoleOut,
    summary="Upload a Job Description file and attach it to the role",
)
async def upload_jd(
    workspace_id: uuid.UUID,
    role_id: uuid.UUID,
    file: Annotated[UploadFile, File(description="PDF or DOCX job description")],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    storage: Annotated[StorageService, Depends(StorageService.from_settings)],
) -> Any:
    """
    Accepts a PDF or DOCX job description file, uploads it to Azure Blob
    Storage, and stores the URL on the role record.

    TODO: Trigger background parsing of the JD to populate requirements_json.
    """
    await _resolve_workspace(workspace_id, current_user, db)
    role = await _get_role_or_404(role_id, workspace_id, db)

    allowed_types = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF and DOCX files are accepted for job descriptions.",
        )

    blob_name = f"{workspace_id}/{role_id}/jd/{file.filename}"
    content = await file.read()
    blob_url = await storage.upload(
        container="jd",
        blob_name=blob_name,
        data=content,
        content_type=file.content_type or "application/octet-stream",
    )

    role.jd_blob_url = blob_url
    await db.flush()
    await db.refresh(role)
    return role
