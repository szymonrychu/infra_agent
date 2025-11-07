from typing import List, Optional

import gitlab
from pydantic import Field

from infra_agent.models.generic import InfraAgentBaseModel, PromptToolError
from infra_agent.models.gl import GitlabFile
from infra_agent.settings import settings

gl = gitlab.Gitlab(str(settings.GITLAB_URL), private_token=settings.GITLAB_TOKEN)


async def list_files_in_repository(branch: str, path: str = "") -> List[GitlabFile]:
    """List files in repository for a given branch and path."""
    project = gl.projects.get(settings.GITLAB_HELMFILE_PROJECT_PATH)
    files = project.repository_tree(path=path, ref=branch, all=True, recursive=True)
    result = []
    for f in files:
        result.append(
            GitlabFile(
                file_path=f.get("path", ""),
                file_name=f.get("name", ""),
                size=f.get("size", None),
                encoding=None,
                content=None,
                ref=branch,
                blob_id=f.get("id", None),
                commit_id=None,
                last_commit_id=None,
                execute_filemode=f.get("mode", None) == "100755",
            )
        )
    return result


class GitlabMergeRequest(InfraAgentBaseModel):
    id: int | None = None
    title: str
    state: str = "opened"
    description: str
    target_branch: str
    source_branch: str
    merge_request_files: dict[str, str] = Field(default={}, exclude=True)

    async def add_files(self, file_path: str, file_contents: str):
        self.merge_request_files[file_path] = file_contents

    async def commit_and_push(self, commit_message: str):
        project = gl.projects.get(settings.GITLAB_HELMFILE_PROJECT_PATH)
        existing_files = [f.file_path for f in await list_files_in_repository(self.source_branch)]
        commit_actions = []
        for file_path, file_contents in self.merge_request_files.items():
            commit_actions.append(
                {
                    "action": "update" if file_path in existing_files else "create",
                    "file_path": file_path,
                    "content": file_contents,
                }
            )
        try:
            project.commits.create(
                {
                    "commit_message": commit_message,
                    "author_email": "ai",
                    "author_name": "ai",
                    "actions": commit_actions,
                    "branch": self.target_branch,
                    "start_branch": self.source_branch,
                }
            )
        except Exception as e:
            raise PromptToolError(
                message=f"Problem creating commit! {e}",
                tool_name="create_merge_request",
                inputs={
                    "commit_message": commit_message,
                },
            )

        try:
            project.mergerequests.create(
                {
                    "source_branch": self.target_branch,
                    "target_branch": self.source_branch,
                    "title": self.title,
                    "description": self.description,
                    "labels": "ai,automerge",
                }
            )
        except Exception as e:
            raise PromptToolError(
                message=f"Problem creating merge request from commit! {e}",
                tool_name="create_merge_request",
                inputs={
                    "commit_message": commit_message,
                },
            )


class GitlabMergeRequestList(InfraAgentBaseModel):
    """List of Gitlab merge requests"""

    items: List[GitlabMergeRequest]


class GitlabWebhookPayload(InfraAgentBaseModel):
    object_kind: str
    user: dict
    project: dict
    object_attributes: GitlabMergeRequest


class GitlabCommit(InfraAgentBaseModel):
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


class GitlabRepository(InfraAgentBaseModel):
    id: int
    name: str
    description: Optional[str] = None
    web_url: Optional[str] = None
    url: Optional[str] = None
    visibility: Optional[str] = None
    default_branch: Optional[str] = None
    created_at: Optional[str] = None
    last_activity_at: Optional[str] = None


class GitlabFile(InfraAgentBaseModel):
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
