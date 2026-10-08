from __future__ import annotations

from uuid import UUID

from auditor.evaluations.public import EvaluationAccess
from auditor.identity.public import Permission, UploadTicket, issue_ticket
from auditor.shared.application.ports import Clock
from auditor.shared.domain.actor import Actor


class IssueUploadTicket:
    """Grants a short-lived ticket to upload one document to an evaluation the actor may upload to.

    State rules (consent, open evaluation, limits) are still checked by the upload itself.
    """

    def __init__(self, access: EvaluationAccess, secret: bytes, clock: Clock) -> None:
        self._access = access
        self._secret = secret
        self._clock = clock

    async def execute(self, actor: Actor, evaluation_id: UUID) -> UploadTicket:
        evaluation = await self._access.require(actor, evaluation_id, Permission.UPLOAD_DOCUMENTS)
        return issue_ticket(self._secret, actor.user_id, evaluation.id, self._clock.now())
