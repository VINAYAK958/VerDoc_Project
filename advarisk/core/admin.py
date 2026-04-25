from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from django.utils import timezone
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages

from .models import (
    CustomUser, LoanOperation, OperationHistory,
    SROState, SRODistrict, SROSubDistrict, SROOffice,
)
from .sro_data import SRO_MAP


# ── Custom User Creation / Change forms (no password exposure) ────────────────

class AdminUserCreationForm(UserCreationForm):
    """Full add-user form for admin — includes all role-specific fields."""
    class Meta(UserCreationForm.Meta):
        model  = CustomUser
        fields = [
            'first_name', 'last_name', 'username', 'email',
            'role', 'phone_number',
            'aadhar_number', 'pan_number',
            'state', 'district', 'sub_district', 'sro_no',
            'is_active',
        ]


class AdminUserChangeForm(UserChangeForm):
    """Change form — password field is completely removed."""
    password = None  # hide the hashed-password summary row

    class Meta(UserChangeForm.Meta):
        model  = CustomUser
        fields = [
            'first_name', 'last_name', 'username', 'email',
            'role', 'phone_number',
            'aadhar_number', 'pan_number',
            'state', 'district', 'sub_district', 'sro_no',
            'is_active', 'is_staff', 'last_active',
            'groups', 'user_permissions',
        ]


# ── SRO Location Hierarchy ────────────────────────────────────────────────────

@admin.register(SROState)
class SROStateAdmin(admin.ModelAdmin):
    list_display  = ['name', 'district_count']
    search_fields = ['name']

    @admin.display(description='Districts')
    def district_count(self, obj):
        return obj.districts.count()


@admin.register(SRODistrict)
class SRODistrictAdmin(admin.ModelAdmin):
    list_display  = ['name', 'state', 'sub_district_count']
    list_filter   = ['state']
    search_fields = ['name', 'state__name']
    raw_id_fields = []
    autocomplete_fields = ['state']

    @admin.display(description='Sub-Districts')
    def sub_district_count(self, obj):
        return obj.sub_districts.count()


@admin.register(SROSubDistrict)
class SROSubDistrictAdmin(admin.ModelAdmin):
    list_display  = ['name', 'district', 'state_name', 'office_count']
    list_filter   = ['district__state']
    search_fields = ['name', 'district__name', 'district__state__name']
    autocomplete_fields = ['district']

    @admin.display(description='State')
    def state_name(self, obj):
        return obj.district.state.name

    @admin.display(description='Offices')
    def office_count(self, obj):
        return obj.offices.count()


@admin.register(SROOffice)
class SROOfficeAdmin(admin.ModelAdmin):
    list_display  = ['sro_code', 'sro_name', 'sub_district_name', 'district_name', 'state_name', 'agent_count']
    list_filter   = ['sub_district__district__state']
    search_fields = ['sro_code', 'sro_name', 'sub_district__name']
    autocomplete_fields = ['sub_district']

    @admin.display(description='Sub-District')
    def sub_district_name(self, obj):
        return obj.sub_district.name

    @admin.display(description='District')
    def district_name(self, obj):
        return obj.sub_district.district.name

    @admin.display(description='State')
    def state_name(self, obj):
        return obj.sub_district.district.state.name

    @admin.display(description='Agents')
    def agent_count(self, obj):
        return CustomUser.objects.filter(sro_no=obj.sro_code, role='AGENT').count()


# ── CustomUser Admin ──────────────────────────────────────────────────────────

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    form     = AdminUserChangeForm
    add_form = AdminUserCreationForm

    list_display  = [
        'display_name', 'email', 'phone_number', 'role_badge',
        'aadhar_masked', 'pan_number',
        'sro_no', 'online_status', 'is_active',
    ]
    list_filter   = ['role', 'state', 'is_active']
    search_fields = ['first_name', 'last_name', 'email', 'phone_number',
                     'aadhar_number', 'pan_number', 'username']
    ordering      = ['-date_joined']

    # ── Fieldsets for CHANGE form ────────────────────────────────────────────
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'username', 'email'),
        }),
        ('Role & Contact', {
            'fields': ('role', 'phone_number'),
        }),
        ('Identity Documents', {
            'description': 'Both fields are unique across all users.',
            'fields': ('aadhar_number', 'pan_number'),
        }),
        ('SRO Assignment (Agents only)', {
            'classes': ('collapse',),
            'fields': ('state', 'district', 'sub_district', 'sro_no'),
        }),
        ('Access & Permissions', {
            'classes': ('collapse',),
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Activity', {
            'classes': ('collapse',),
            'fields': ('last_active', 'last_login', 'date_joined'),
        }),
    )
    readonly_fields = ('last_active', 'last_login', 'date_joined')

    # ── Fieldsets for ADD form ────────────────────────────────────────────────
    add_fieldsets = (
        ('Account Details', {
            'fields': (
                'first_name', 'last_name', 'username', 'email',
                'role', 'phone_number',
                'aadhar_number', 'pan_number',
                'state', 'district', 'sub_district', 'sro_no',
                'password1', 'password2', 'is_active',
            ),
        }),
    )

    # ── Custom display columns ────────────────────────────────────────────────

    @admin.display(description='Name / Email', ordering='first_name')
    def display_name(self, obj):
        name = obj.get_full_name() or obj.username
        return format_html(
            '<strong>{}</strong><br><small style="color:#94a3b8;">{}</small>',
            name, obj.email,
        )

    @admin.display(description='Role')
    def role_badge(self, obj):
        colours = {'CLIENT': '#3b82f6', 'AGENT': '#f59e0b'}
        c = colours.get(obj.role, '#64748b')
        return format_html(
            '<span style="background:{0}22;color:{0};border:1px solid {0}55;'
            'border-radius:99px;padding:2px 10px;font-size:0.75rem;font-weight:700;">'
            '{1}</span>', c, obj.role,
        )

    @admin.display(description='Aadhaar')
    def aadhar_masked(self, obj):
        a = obj.aadhar_number
        if not a or len(a) < 4:
            return '—'
        return format_html('<code>XXXX XXXX {}</code>', a[-4:])

    @admin.display(description='Online / Last Seen')
    def online_status(self, obj):
        if obj.is_online:
            when = obj.last_active.strftime('%H:%M') if obj.last_active else ''
            return format_html(
                '<span style="color:#10b981;font-weight:700;">● Online</span>'
                '<br><small style="color:#94a3b8;">{}</small>', when,
            )
        if obj.last_active:
            delta   = timezone.now() - obj.last_active
            minutes = int(delta.total_seconds() // 60)
            if minutes < 60:
                label = f'{minutes}m ago'
            elif minutes < 1440:
                label = f'{minutes // 60}h ago'
            else:
                label = f'{minutes // 1440}d ago'
            when = obj.last_active.strftime('%d %b %Y, %H:%M')
            return format_html(
                '<span style="color:#94a3b8;">○ Offline</span>'
                '<br><small style="color:#64748b;">{} ({})</small>',
                label, when,
            )
        return format_html('<span style="color:#475569;font-size:0.8rem;">Never logged in</span>')

    def get_form(self, request, obj=None, **kwargs):
        """Prevent admins from seeing or editing passwords."""
        form = super().get_form(request, obj, **kwargs)
        if 'password' in form.base_fields:
            del form.base_fields['password']
        return form


# ── LoanOperation Admin ───────────────────────────────────────────────────────

@admin.register(LoanOperation)
class LoanOperationAdmin(admin.ModelAdmin):
    list_display  = [
        'id', 'client_info', 'operation_type', 'amount_fmt',
        'status_badge', 'agent_info', 'sro_no',
        'docs_progress', 'created_at',
    ]
    list_filter   = ['status', 'operation_type', 'state', 'sro_no']
    search_fields = ['client__email', 'client__first_name', 'sro_no', 'bhu_aadhar']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['mark_approved', 'mark_rejected']

    @admin.display(description='Client')
    def client_info(self, obj):
        name = obj.client.get_full_name() or obj.client.email
        return format_html('<strong>{}</strong>', name)

    @admin.display(description='Amount', ordering='amount')
    def amount_fmt(self, obj):
        if obj.amount is None:
            return '—'
        formatted_amount = "{:,}".format(int(obj.amount))
        return format_html('<span style="font-family:monospace;">₹&nbsp;{}</span>',
                           formatted_amount)

    @admin.display(description='Status')
    def status_badge(self, obj):
        colours = {
            'PENDING':     ('#f59e0b', '#f59e0b22'),
            'IN_PROGRESS': ('#3b82f6', '#3b82f622'),
            'COMPLETED':   ('#10b981', '#10b98122'),
        }
        fg, bg = colours.get(obj.status, ('#94a3b8', '#94a3b822'))
        return format_html(
            '<span style="background:{};color:{};border-radius:99px;'
            'padding:2px 10px;font-size:0.78rem;font-weight:700;">{}</span>',
            bg, fg, obj.get_status_display(),
        )

    @admin.display(description='Agent')
    def agent_info(self, obj):
        if obj.agent:
            return format_html('<span style="color:#f59e0b;">{}</span>',
                               obj.agent.get_full_name() or obj.agent.email)
        return format_html('<span style="color:#475569;font-style:italic;">Unassigned</span>')

    @admin.display(description='Documents')
    def docs_progress(self, obj):
        approved = obj.approved_docs_count
        total    = 8
        pct      = int(approved / total * 100)
        colour   = '#10b981' if approved == total else ('#f59e0b' if approved > 0 else '#475569')
        bar      = (
            f'<div style="background:#1e293b;border-radius:4px;height:6px;width:80px;display:inline-block;vertical-align:middle;">'
            f'<div style="background:{colour};width:{pct}%;height:100%;border-radius:4px;"></div></div>'
        )
        return format_html(
            '{} <span style="color:{};font-weight:600;font-size:0.8rem;">&nbsp;{}/{}</span>',
            bar, colour, approved, total,
        )

    @admin.action(description='Mark selected operations as Completed/Approved')
    def mark_approved(self, request, queryset):
        updated = queryset.update(status='COMPLETED')
        self.message_user(request, f'{updated} operation(s) marked as Completed.', messages.SUCCESS)

    @admin.action(description='Mark selected operations as Rejected')
    def mark_rejected(self, request, queryset):
        # Move back to PENDING so agent can retry
        updated = queryset.update(status='PENDING')
        self.message_user(request, f'{updated} operation(s) reset to Pending.', messages.WARNING)


# ── OperationHistory Admin ────────────────────────────────────────────────────

@admin.register(OperationHistory)
class OperationHistoryAdmin(admin.ModelAdmin):
    list_display  = ['loan_operation', 'actor', 'action_short', 'timestamp']
    list_filter   = ['timestamp']
    search_fields = ['action', 'actor__email', 'actor__first_name']
    readonly_fields = ['loan_operation', 'actor', 'action', 'snapshot', 'timestamp']

    @admin.display(description='Action')
    def action_short(self, obj):
        return obj.action[:80]

    def has_add_permission(self, request):
        return False  # history is append-only

    def has_change_permission(self, request, obj=None):
        return False  # read-only audit ledger
