import sys
import os


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from fastapi import Request, Depends, HTTPException, status


from services.auth import auth_service
from entity.models import Role, User


class RoleAccess:
    """
    Class for role-based access control.

    Args:
        allowed_roles (list[Role]): List of roles allowed to access the resource.
    """

    def __init__(self, allowed_roles: list[Role]):
        self.allowed_roles = allowed_roles

    async def __call__(
        self, request: Request, user: User = Depends(auth_service.get_current_user)
    ) -> None:
        """
        Check if the user has permission to access the resource based on their role.

        Args:
            request (Request): The request object.
            user (User): The current user.

        Raises:
            HTTPException: If the user does not have permission (HTTP 403 Forbidden).

        Returns:
            None
        """
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="FORBIDDEN"
            )
