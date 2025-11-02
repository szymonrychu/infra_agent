from typing import List, Optional

from pydantic import BaseModel


class GitlabMergeRequest(BaseModel):
    id: int
    title: str
    action: str | None
    description: Optional[str] = None
    state: str
    created_at: str
    updated_at: str
    merged_by: Optional[str] = None
    merged_at: Optional[str] = None
    closed_by: Optional[str] = None
    closed_at: Optional[str] = None
    target_branch: str
    source_branch: str


class GitlabMergeRequestList(BaseModel):
    """List of Gitlab merge requests"""

    items: List[GitlabMergeRequest]


class GitlabWebhookPayload(BaseModel):
    object_kind: str
    user: dict
    project: dict
    object_attributes: GitlabMergeRequest


class GitlabCommit(BaseModel):
    id: str
    short_id: Optional[str] = None
    title: Optional[str] = None
    message: Optional[str] = None
    author_name: Optional[str] = None
    author_email: Optional[str] = None
    authored_date: Optional[str] = None
    committer_name: Optional[str] = None
    committer_email: Optional[str] = None
    committed_date: Optional[str] = None
    parent_ids: Optional[List[str]] = None
    web_url: Optional[str] = None


class GitlabRepository(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    web_url: Optional[str] = None
    url: Optional[str] = None
    visibility: Optional[str] = None
    default_branch: Optional[str] = None
    created_at: Optional[str] = None
    last_activity_at: Optional[str] = None


class GitlabFile(BaseModel):
    file_path: str
    file_name: str
    size: Optional[int] = None
    encoding: Optional[str] = None
    content: Optional[str] = None
    ref: Optional[str] = None
    blob_id: Optional[str] = None
    commit_id: Optional[str] = None
    last_commit_id: Optional[str] = None
    execute_filemode: Optional[bool] = None
