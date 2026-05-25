from backend.models.schemas import ApplicantMessageResponse
from backend.services.case_service import CaseService


class NotificationService:
    def __init__(self) -> None:
        self.case_service = CaseService()

    def store_message(self, case_id: str, message: ApplicantMessageResponse) -> ApplicantMessageResponse:
        case = self.case_service.get_case(case_id)
        if not case:
            return message
        case.applicant_message_history.append(message.model_dump())
        self.case_service.save_case(case)
        self.case_service.add_notification(case_id, message.model_dump())
        return message
