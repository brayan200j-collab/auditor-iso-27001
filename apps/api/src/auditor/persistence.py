"""Imports every ORM model so `Base.metadata` is complete (Alembic, tests). Composition level."""

from __future__ import annotations

from auditor.analysis.infrastructure import models as analysis_models
from auditor.audit.infrastructure import models as audit_models
from auditor.checklist.infrastructure import models as checklist_models
from auditor.companies.infrastructure import models as companies_models
from auditor.documents.infrastructure import models as documents_models
from auditor.evaluations.infrastructure import models as evaluations_models
from auditor.feedback.infrastructure import models as feedback_models
from auditor.identity.infrastructure import models as identity_models
from auditor.reports.infrastructure import models as reports_models
from auditor.review.infrastructure import models as review_models
from auditor.shared.infrastructure import jobs_model
from auditor.shared.infrastructure.database import Base

MODEL_MODULES = (
    analysis_models,
    audit_models,
    checklist_models,
    companies_models,
    documents_models,
    evaluations_models,
    feedback_models,
    identity_models,
    reports_models,
    review_models,
    jobs_model,
)

metadata = Base.metadata
