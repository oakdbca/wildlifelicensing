from django.urls import re_path

from wildlifelicensing.apps.applications.views.conditions import (
    AssignAssessorView,
    CreateConditionView,
    EnterConditionsAssessorView,
    EnterConditionsView,
    SearchConditionsView,
    SetAssessmentConditionState,
)
from wildlifelicensing.apps.applications.views.entry import (
    AmendLicenceView,
    ApplicationCompleteView,
    CheckIdentificationRequiredView,
    CheckSeniorCardView,
    CreateSelectCustomer,
    CreateSelectProfileView,
    DeleteApplicationSessionView,
    DiscardApplicationView,
    EditApplicationView,
    EnterDetailsView,
    NewApplicationView,
    PreviewView,
    RenewLicenceView,
    SelectLicenceTypeView,
)
from wildlifelicensing.apps.applications.views.issue import (
    IssueLicenceView,
    PreviewLicenceView,
    ReissueLicenceView,
)
from wildlifelicensing.apps.applications.views.process import (
    AmendmentRequestView,
    AssignOfficerView,
    IDRequestView,
    ProcessView,
    RemindAssessmentView,
    ReturnsRequestView,
    SendForAssessmentView,
    SetCharacterCheckStatusView,
    SetIDCheckStatusView,
    SetReturnsCheckStatusView,
    SetReviewStatusView,
)
from wildlifelicensing.apps.applications.views.view import (
    AddApplicationLogEntryView,
    ApplicationLogListView,
    ApplicationUserActionListView,
    ViewPDFView,
    ViewReadonlyAssessorView,
    ViewReadonlyOfficerView,
    ViewReadonlyView,
)

urlpatterns = [
    # application entry / licence renewal/amendment
    re_path(
        "^delete-application-session/$",
        DeleteApplicationSessionView.as_view(),
        name="delete_application_session",
    ),
    re_path("^new-application/$", NewApplicationView.as_view(), name="new_application"),
    re_path(
        "^select-licence-type$",
        SelectLicenceTypeView.as_view(),
        name="select_licence_type",
    ),
    re_path(
        "^select-licence-type/([0-9]+)$",
        SelectLicenceTypeView.as_view(),
        name="select_licence_type",
    ),
    re_path(
        "^create-select-customer/$",
        CreateSelectCustomer.as_view(),
        name="create_select_customer",
    ),
    re_path(
        "^edit-application/([0-9]+)/$",
        EditApplicationView.as_view(),
        name="edit_application",
    ),
    re_path(
        "^discard-application/([0-9]+)/$",
        DiscardApplicationView.as_view(),
        name="discard_application",
    ),
    re_path(
        "^check-identification/$",
        CheckIdentificationRequiredView.as_view(),
        name="check_identification",
    ),
    re_path(
        "^check-senior-card/$", CheckSeniorCardView.as_view(), name="check_senior_card"
    ),
    re_path(
        "^profile/$", CreateSelectProfileView.as_view(), name="create_select_profile"
    ),
    re_path("^enter-details/$", EnterDetailsView.as_view(), name="enter_details"),
    re_path("^preview/$", PreviewView.as_view(), name="preview"),
    re_path("^complete/$$", ApplicationCompleteView.as_view(), name="complete"),
    re_path(
        "^renew-licence/([0-9]+)/$", RenewLicenceView.as_view(), name="renew_licence"
    ),
    re_path(
        "^amend-licence/([0-9]+)/$", AmendLicenceView.as_view(), name="amend_licence"
    ),
    # process
    re_path(r"^process/([0-9]+)/$", ProcessView.as_view(), name="process"),
    re_path("^assign-officer/$", AssignOfficerView.as_view(), name="assign_officer"),
    re_path(
        "^set-id-check-status/$",
        SetIDCheckStatusView.as_view(),
        name="set_id_check_status",
    ),
    re_path("^id-request/$", IDRequestView.as_view(), name="id_request"),
    re_path("^returns-request/$", ReturnsRequestView.as_view(), name="returns_request"),
    re_path(
        "^set-returns-check-status/$",
        SetReturnsCheckStatusView.as_view(),
        name="set_returns_check_status",
    ),
    re_path(
        "^set-character-check-status/$",
        SetCharacterCheckStatusView.as_view(),
        name="set_character_check_status",
    ),
    re_path(
        "^set-review-status/$", SetReviewStatusView.as_view(), name="set_review_status"
    ),
    re_path(
        "^amendment-request/$", AmendmentRequestView.as_view(), name="amendment_request"
    ),
    re_path(
        "^send-for-assessment/$",
        SendForAssessmentView.as_view(),
        name="send_for_assessment",
    ),
    re_path(
        "^remind-assessment/$", RemindAssessmentView.as_view(), name="remind_assessment"
    ),
    # communication log
    re_path(
        "^add-log-entry/([0-9]+)/$",
        AddApplicationLogEntryView.as_view(),
        name="add_log_entry",
    ),
    re_path("^log-list/([0-9]+)/$", ApplicationLogListView.as_view(), name="log_list"),
    # action log
    re_path(
        "^action-list/([0-9]+)/$",
        ApplicationUserActionListView.as_view(),
        name="action_list",
    ),
    # conditions
    re_path(
        "^enter-conditions/([0-9]+)/$",
        EnterConditionsView.as_view(),
        name="enter_conditions",
    ),
    re_path(
        "^enter-conditions/([0-9]+)/assessment/([0-9]+)/?$",
        EnterConditionsAssessorView.as_view(),
        name="enter_conditions_assessor",
    ),
    re_path(
        "^search-conditions/$", SearchConditionsView.as_view(), name="search_conditions"
    ),
    re_path(
        "^create-condition/([0-9]+)/$",
        CreateConditionView.as_view(),
        name="create_condition",
    ),
    re_path(
        "^enter-conditions/([0-9]+)/assign-officer/$",
        AssignOfficerView.as_view(),
        name="assign_officer",
    ),
    re_path(
        "^set-assessment-condition-state/$",
        SetAssessmentConditionState.as_view(),
        name="set_assessment_condition_state",
    ),
    re_path("^assign-assessor/$", AssignAssessorView.as_view(), name="assign_assessor"),
    # issue
    re_path(
        "^issue-licence/([0-9]+)/$", IssueLicenceView.as_view(), name="issue_licence"
    ),
    re_path(
        "^reissue-licence/([0-9]+)/$",
        ReissueLicenceView.as_view(),
        name="reissue_licence",
    ),
    re_path(
        "^preview-licence/([0-9]+)/$",
        PreviewLicenceView.as_view(),
        name="preview_licence",
    ),
    # view
    re_path(
        "^view-application/([0-9]+)/$",
        ViewReadonlyView.as_view(),
        name="view_application",
    ),
    re_path(
        "^view-application-pdf/([0-9]+)/$",
        ViewPDFView.as_view(),
        name="view_application_pdf",
    ),
    re_path(
        "^view-application-officer/([0-9]+)/$",
        ViewReadonlyOfficerView.as_view(),
        name="view_application_officer",
    ),
    re_path(
        "^view-assessment/([0-9]+)/assessment/([0-9]+)/$",
        ViewReadonlyAssessorView.as_view(),
        name="view_assessment",
    ),
]
