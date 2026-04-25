from django.urls import path
from . import views

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────────────────────────
    path('signup/',                views.signup,               name='signup'),
    path('signup/client/',         views.signup_client,        name='signup_client'),
    path('signup/agent/',          views.signup_agent,         name='signup_agent'),
    path('signup/verify/',         views.verify_signup_otp,    name='verify_signup_otp'),

    # Password reset (OTP-based)
    path('password-reset/',        views.smart_password_reset, name='smart_password_reset'),
    path('password-reset/otp/',    views.otp_verify,           name='otp_verify'),
    path('password-reset/set/',    views.otp_set_password,     name='otp_set_password'),

    # ── Dashboard ─────────────────────────────────────────────────────────────
    path('',                       views.dashboard_redirect,   name='dashboard'),

    # ── Client ────────────────────────────────────────────────────────────────
    path('dashboard/',             views.ClientDashboardView.as_view(), name='client_dashboard'),
    path('raise/',                 views.RaiseLoanView.as_view(),        name='raise_loan'),
    path('payoff/',                views.PayoffLoanView.as_view(),       name='payoff_loan'),

    # ── Agent ─────────────────────────────────────────────────────────────────
    path('agent/',                            views.AgentDashboardView.as_view(),  name='agent_dashboard'),
    path('agent/task/<int:pk>/accept/',       views.accept_task,                   name='accept_task'),
    path('agent/task/<int:pk>/undo-accept/',  views.undo_accept_task,              name='undo_accept_task'),
    path('agent/task/<int:pk>/complete/',     views.complete_task,                 name='complete_task'),
    path('agent/task/<int:pk>/verify/',       views.verify_documents,              name='verify_documents'),
    path('agent/task/<int:pk>/undo-verify/',  views.undo_verify_documents,         name='undo_verify_documents'),

    # ── History / Audit ───────────────────────────────────────────────────────
    path('history/<int:pk>/',      views.OperationHistoryView.as_view(),  name='operation_history'),

    # ── SRO JSON APIs ─────────────────────────────────────────────────────────
    path('api/states/',            views.api_get_states,        name='api_states'),
    path('api/districts/',         views.api_get_districts,     name='api_districts'),
    path('api/sub-districts/',     views.api_get_sub_districts, name='api_sub_districts'),
    path('api/sro-no/',            views.api_get_sro_no,        name='api_sro_no'),

    # ── Live availability checks ──────────────────────────────────────────────
    path('api/check-email/',       views.api_check_email,       name='api_check_email'),
    path('api/check-phone/',       views.api_check_phone,       name='api_check_phone'),
    path('api/check-aadhar/',      views.api_check_aadhar,      name='api_check_aadhar'),
    path('api/check-pan/',         views.api_check_pan,         name='api_check_pan'),
]
