from typing import List

import gitlab

from infra_agent.models.gl import (
    GitlabCommit,
    GitlabFile,
    GitlabMergeRequest,
    GitlabMergeRequestList,
)
from infra_agent.settings import settings

gl = gitlab.Gitlab(str(settings.GITLAB_URL), private_token=settings.GITLAB_TOKEN)


async def list_opened_merge_requests() -> GitlabMergeRequestList:
    """List opened merge requests for a project."""
    project = gl.projects.get(settings.GITLAB_HELMFILE_PROJECT_PATH)
    mrs = project.mergerequests.list(state="opened", all=True)
    items = [
        GitlabMergeRequest(
            id=mr.id,
            title=mr.title,
            action=None,
            description=mr.description,
            state=mr.state,
            created_at=mr.created_at,
            updated_at=mr.updated_at,
            merged_by=getattr(mr, "merged_by", None),
            merged_at=getattr(mr, "merged_at", None),
            closed_by=getattr(mr, "closed_by", None),
            closed_at=getattr(mr, "closed_at", None),
            target_branch=mr.target_branch,
            source_branch=mr.source_branch,
        )
        for mr in mrs
    ]
    return GitlabMergeRequestList(items=items)


async def get_merge_request_details(mr_id: int) -> GitlabMergeRequest:
    """Get details of a merge request."""
    project = gl.projects.get(settings.GITLAB_HELMFILE_PROJECT_PATH)
    mr = project.mergerequests.get(mr_id)
    return GitlabMergeRequest(
        id=mr.id,
        title=mr.title,
        action=None,
        description=mr.description,
        state=mr.state,
        created_at=mr.created_at,
        updated_at=mr.updated_at,
        merged_by=getattr(mr, "merged_by", None),
        merged_at=getattr(mr, "merged_at", None),
        closed_by=getattr(mr, "closed_by", None),
        closed_at=getattr(mr, "closed_at", None),
        target_branch=mr.target_branch,
        source_branch=mr.source_branch,
    )


async def update_file_and_push(branch: str, file_path: str, content: str, commit_message: str) -> GitlabCommit:
    """Update a file in a branch and push."""
    project = gl.projects.get(settings.GITLAB_HELMFILE_PROJECT_PATH)
    file = project.files.get(file_path=file_path, ref=branch)
    file.content = content
    file.save(branch=branch, commit_message=commit_message)
    commit = project.commits.list(ref_name=branch, per_page=1)[0]
    return GitlabCommit(
        id=commit.id,
        short_id=commit.short_id,
        title=commit.title,
        message=commit.message,
        author_name=commit.author_name,
        author_email=commit.author_email,
        authored_date=commit.authored_date,
        committer_name=commit.committer_name,
        committer_email=commit.committer_email,
        committed_date=commit.committed_date,
        parent_ids=commit.parent_ids,
        web_url=commit.web_url,
    )


async def create_merge_request_from_branch(
    source_branch: str, target_branch: str, title: str, description: str
) -> GitlabMergeRequest:
    """Create a merge request from a branch."""
    project = gl.projects.get(settings.GITLAB_HELMFILE_PROJECT_PATH)
    mr = project.mergerequests.create(
        {
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": title,
            "description": description,
        }
    )
    return GitlabMergeRequest(
        id=mr.id,
        title=mr.title,
        action=None,
        description=mr.description,
        state=mr.state,
        created_at=mr.created_at,
        updated_at=mr.updated_at,
        merged_by=getattr(mr, "merged_by", None),
        merged_at=getattr(mr, "merged_at", None),
        closed_by=getattr(mr, "closed_by", None),
        closed_at=getattr(mr, "closed_at", None),
        target_branch=mr.target_branch,
        source_branch=mr.source_branch,
    )


async def approve_merge_request(mr_id: int) -> bool:
    """Approve a merge request."""
    project = gl.projects.get(settings.GITLAB_HELMFILE_PROJECT_PATH)
    mr = project.mergerequests.get(mr_id)
    mr.approve()
    return True


async def get_file_contents(branch: str, file_path: str) -> GitlabFile:
    """Get file contents from repository, branch, and path."""
    project = gl.projects.get(settings.GITLAB_HELMFILE_PROJECT_PATH)
    file = project.files.get(file_path=file_path, ref=branch)
    return GitlabFile(
        file_path=file.file_path,
        file_name=file.file_name,
        size=file.size,
        encoding=file.encoding,
        content=file.decode(),
        ref=branch,
        blob_id=getattr(file, "blob_id", None),
        commit_id=getattr(file, "commit_id", None),
        last_commit_id=getattr(file, "last_commit_id", None),
        execute_filemode=getattr(file, "execute_filemode", None),
    )


async def list_files_in_repository(branch: str, path: str = "") -> List[GitlabFile]:
    """List files in repository for a given branch and path."""
    project = gl.projects.get(settings.GITLAB_HELMFILE_PROJECT_PATH)
    files = project.repository_tree(path=path, ref=branch, all=True)
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
