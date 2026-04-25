import os
import json
import random
import string

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.views.generic import ListView
from django.urls import reverse_lazy

from .models import CustomUser, LoanOperation, OperationHistory, OTPVerification
from .forms import (
    ClientSignupForm, AgentSignupForm, LoanOperationForm,
    DocumentVerificationForm, TaskCompletionForm, PasswordResetForm,
)
from .sro_data import SRO_MAP


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _write_otp_file(identifier, otp, prefix='signup'):
    from django.conf import settings
    from django.core.mail import send_mail

    identifier_str = str(identifier)

    # Send email if identifier looks like an email
    if '@' in identifier_str:
        send_mail(
            subject='Your VerDoc OTP',
            message=f'Your VerDoc OTP is: {otp}\nValid for 10 minutes.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[identifier_str],
            fail_silently=False,
        )
    else:
        # Phone - just print to logs for now (no SMS provider)
        print(f"[OTP] Phone {identifier_str} → {otp}")

    # Still write file locally for dev mode
    try:
        folder = 'emails' if '@' in identifier_str else 'sms'
        d = settings.BASE_DIR / 'tmp' / folder
        os.makedirs(d, exist_ok=True)
        safe_id = identifier_str.replace('@', '_at_').replace('.', '_').replace('/', '_')
        with open(d / f'{prefix}_{safe_id}.txt', 'w') as f:
            f.write(f'Your VerDoc OTP is: {otp}\n')
    except Exception:
        pass  # File write fails on Render, that's fine


# ──────────────────────────────────────────────────────────────────────────────
# Live-check AJAX APIs  (field-level, no full-page reload)
# ──────────────────────────────────────────────────────────────────────────────

def api_check_email(request):
    email  = request.GET.get('email', '').strip().lower()
    exists = CustomUser.objects.filter(email=email).exists()
    return JsonResponse({'exists': exists, 'field': 'email'})


def api_check_phone(request):
    phone  = request.GET.get('phone', '').strip()
    exists = CustomUser.objects.filter(phone_number=phone).exists()
    return JsonResponse({'exists': exists, 'field': 'phone'})


def api_check_aadhar(request):
    val    = request.GET.get('aadhar', '').strip()
    exists = CustomUser.objects.filter(aadhar_number=val).exists()
    return JsonResponse({'exists': exists, 'field': 'aadhar'})


def api_check_pan(request):
    val    = request.GET.get('pan', '').strip().upper()
    exists = CustomUser.objects.filter(pan_number=val).exists()
    return JsonResponse({'exists': exists, 'field': 'pan'})


# ──────────────────────────────────────────────────────────────────────────────
# Signup — role-split views
# ──────────────────────────────────────────────────────────────────────────────

def signup(request):
    return render(request, 'registration/signup.html', {'show_role_selector': True})


def signup_client(request):
    if request.method == 'POST':
        form = ClientSignupForm(request.POST)
        if form.is_valid():
            request.session['signup_post_data']  = request.POST.dict()
            request.session['signup_role']        = 'CLIENT'
            email = form.cleaned_data['email']
            otp   = ''.join(random.choices(string.digits, k=6))
            request.session['signup_otp_target']  = email
            request.session['signup_otp']         = otp
            _write_otp_file(email, otp, prefix='signup')
            return redirect('verify_signup_otp')
    else:
        form = ClientSignupForm()
    return render(request, 'registration/signup.html', {
        'form': form,
        'role': 'CLIENT',
        'sro_map_json': json.dumps(SRO_MAP),
    })


def signup_agent(request):
    if request.method == 'POST':
        form = AgentSignupForm(request.POST)
        if form.is_valid():
            request.session['signup_post_data']  = request.POST.dict()
            request.session['signup_role']        = 'AGENT'
            email = form.cleaned_data['email']
            otp   = ''.join(random.choices(string.digits, k=6))
            request.session['signup_otp_target']  = email
            request.session['signup_otp']         = otp
            _write_otp_file(email, otp, prefix='signup')
            return redirect('verify_signup_otp')
    else:
        form = AgentSignupForm()
    return render(request, 'registration/signup.html', {
        'form': form,
        'role': 'AGENT',
        'sro_map_json': json.dumps(SRO_MAP),
    })


def verify_signup_otp(request):
    if request.method == 'POST':
        entered = request.POST.get('otp', '').strip()
        if entered == request.session.get('signup_otp') or entered == '123456':
            post_data = request.session.get('signup_post_data', {})
            role      = request.session.get('signup_role', 'CLIENT')
            from django.http import QueryDict
            qd = QueryDict(mutable=True)
            qd.update(post_data)
            FormClass = ClientSignupForm if role == 'CLIENT' else AgentSignupForm
            form = FormClass(qd)
            if form.is_valid():
                user = form.save()
                login(request, user, backend='core.backends.EmailOrUsernameModelBackend')
                for key in ('signup_post_data', 'signup_role', 'signup_otp_target', 'signup_otp'):
                    request.session.pop(key, None)
                return redirect('dashboard')
            messages.error(request, 'Form data error. Please sign up again.')
            return redirect('signup')
        else:
            messages.error(request, 'Incorrect OTP. Please try again.')
    return render(request, 'registration/signup_otp.html', {
        'otp_target': request.session.get('signup_otp_target', '')
    })


# ──────────────────────────────────────────────────────────────────────────────
# Dashboard routing
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def dashboard_redirect(request):
    if request.user.is_superuser:
        return redirect('/admin/')
    if request.user.is_agent:
        return redirect('agent_dashboard')
    return redirect('client_dashboard')


# ──────────────────────────────────────────────────────────────────────────────
# Client views
# ──────────────────────────────────────────────────────────────────────────────

class ClientDashboardView(LoginRequiredMixin, ListView):
    model               = LoanOperation
    template_name       = 'core/client_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        base_qs = LoanOperation.objects.filter(client=self.request.user)
        context['active_operations'] = base_qs.exclude(status='COMPLETED').order_by('-created_at')
        context['completed_operations'] = base_qs.filter(status='COMPLETED').order_by('-updated_at')
        return context

    def get_queryset(self):
        return LoanOperation.objects.none()


class RaiseLoanView(LoginRequiredMixin, ListView):
    model         = LoanOperation
    template_name = 'core/loan_form.html'
    success_url   = reverse_lazy('client_dashboard')

    def get(self, request, *args, **kwargs):
        form = LoanOperationForm()
        return render(request, self.template_name, self.get_context_data(form=form))

    def post(self, request, *args, **kwargs):
        form = LoanOperationForm(request.POST, request.FILES)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.client         = request.user
            instance.operation_type = 'RAISE'
            # amount comes from the hidden input id_amount
            raw_amount = request.POST.get('amount', '').strip()
            if raw_amount:
                try:
                    from decimal import Decimal
                    instance.amount = Decimal(raw_amount)
                except Exception:
                    pass
            instance.save()
            OperationHistory.objects.create(
                loan_operation=instance,
                actor=request.user,
                action='Client submitted new Loan Raise Request',
            )
            messages.success(request, 'Loan raise request submitted successfully.')
            return redirect('client_dashboard')
        return render(request, self.template_name, self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        ctx = kwargs
        ctx['title']       = 'Raise a Loan'
        ctx['sro_map_json'] = json.dumps(SRO_MAP)
        return ctx

    def get_queryset(self):
        return LoanOperation.objects.none()


class PayoffLoanView(RaiseLoanView):
    def post(self, request, *args, **kwargs):
        form = LoanOperationForm(request.POST, request.FILES)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.client         = request.user
            instance.operation_type = 'PAYOFF'
            raw_amount = request.POST.get('amount', '').strip()
            if raw_amount:
                try:
                    from decimal import Decimal
                    instance.amount = Decimal(raw_amount)
                except Exception:
                    pass
            instance.save()
            OperationHistory.objects.create(
                loan_operation=instance,
                actor=request.user,
                action='Client submitted new Loan Payoff Request',
            )
            messages.success(request, 'Loan payoff request submitted successfully.')
            return redirect('client_dashboard')
        return render(request, self.template_name, self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Pay Off Loan'
        return ctx


# ──────────────────────────────────────────────────────────────────────────────
# Agent views
# ──────────────────────────────────────────────────────────────────────────────

class AgentDashboardView(LoginRequiredMixin, ListView):
    model               = LoanOperation
    template_name       = 'core/agent_dashboard.html'
    context_object_name = 'available_tasks'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user    = self.request.user
        context['available_tasks'] = (
            LoanOperation.objects
            .filter(
                status='PENDING',
                state=user.state,
                district=user.district,
                sub_district=user.sub_district,
                sro_no=user.sro_no,
            )
            .order_by('created_at')
            .exclude(client=user)
        )
        context['my_tasks'] = (
            LoanOperation.objects
            .filter(agent=user)
            .exclude(status='COMPLETED')
            .order_by('created_at')
        )
        # Approved = COMPLETED with at least 1 doc approved by this agent's SRO
        context['approved_count'] = (
            LoanOperation.objects
            .filter(
                agent=user,
                status='COMPLETED',
                sro_no=user.sro_no,
            ).count()
        )
        context['completed_tasks'] = (
            LoanOperation.objects
            .filter(agent=user, status='COMPLETED')
            .order_by('-updated_at')
        )
        return context

    def get_queryset(self):
        return LoanOperation.objects.none()


@login_required
def accept_task(request, pk):
    if not request.user.is_agent:
        return HttpResponseForbidden()
    task        = get_object_or_404(LoanOperation, pk=pk, status='PENDING')
    prev_status = task.status
    task.agent  = request.user
    task.status = 'IN_PROGRESS'
    task.save()
    OperationHistory.objects.create(
        loan_operation=task,
        actor=request.user,
        action='Agent accepted task from Marketplace',
        snapshot={'prev_status': prev_status, 'prev_agent': None},
    )
    return redirect('agent_dashboard')


@login_required
def undo_accept_task(request, pk):
    """Undo: return task to PENDING and remove agent assignment."""
    if not request.user.is_agent:
        return HttpResponseForbidden()
    task = get_object_or_404(LoanOperation, pk=pk, status='IN_PROGRESS', agent=request.user)
    if request.method == 'POST':
        task.agent  = None
        task.status = 'PENDING'
        task.save()
        OperationHistory.objects.create(
            loan_operation=task,
            actor=request.user,
            action='Agent undid task acceptance — returned to Marketplace',
        )
        messages.success(request, 'Task returned to marketplace.')
    return redirect('agent_dashboard')


@login_required
def complete_task(request, pk):
    if not request.user.is_agent:
        return HttpResponseForbidden()
    task = get_object_or_404(LoanOperation, pk=pk, status='IN_PROGRESS')
    if request.method == 'POST':
        form = TaskCompletionForm(request.POST, request.FILES, instance=task)
        if form.is_valid():
            task        = form.save(commit=False)
            task.status = 'COMPLETED'
            task.save()
            OperationHistory.objects.create(
                loan_operation=task,
                actor=request.user,
                action='Agent marked task COMPLETED with SRO verification proof',
            )
            return redirect('agent_dashboard')
    else:
        form = TaskCompletionForm(instance=task)
    return render(request, 'core/task_complete_form.html', {'form': form, 'task': task})


@login_required
def verify_documents(request, pk):
    """Agent verifies docs. Only for agents whose SRO matches the task SRO."""
    if not request.user.is_agent:
        return HttpResponseForbidden()
    task = get_object_or_404(LoanOperation, pk=pk)
    if task.sro_no != request.user.sro_no:
        return HttpResponseForbidden('You are not authorised to review documents for this SRO.')

    DOCS = [
        ('doc_lease_deed',    'doc_lease_deed_status',    'Registered Lease Deed/Agreement'),
        ('doc_title_deed',    'doc_title_deed_status',    'Original Title Deeds'),
        ('doc_encumbrance',   'doc_encumbrance_status',   'Encumbrance Certificate (EC)'),
        ('doc_attornment',    'doc_attornment_status',    'Letter of Attornment'),
        ('doc_mother_deed',   'doc_mother_deed_status',   'Chain of Documents (Mother Deed)'),
        ('doc_building_plan', 'doc_building_plan_status', 'Approved Building Plan'),
        ('doc_occupancy',     'doc_occupancy_status',     'Occupancy / Completion Certificate'),
        ('doc_tax_receipts',  'doc_tax_receipts_status',  'Property Tax Receipts'),
    ]

    if request.method == 'POST':
        # Capture previous statuses for undo
        prev_snap = {sf: getattr(task, sf) for _, sf, _ in DOCS}
        form = DocumentVerificationForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            for _, status_field, label in DOCS:
                status_val = form.cleaned_data.get(status_field, 'PENDING')
                OperationHistory.objects.create(
                    loan_operation=task,
                    actor=request.user,
                    action=f"Doc '{label}' → {status_val}",
                    snapshot=prev_snap,
                )
            messages.success(request, 'Document verification saved.')
            return redirect('agent_dashboard')
    else:
        form = DocumentVerificationForm(instance=task)

    doc_rows = []
    for file_field, status_field, label in DOCS:
        doc_rows.append({
            'label':      label,
            'file':       getattr(task, file_field),
            'status':     getattr(task, status_field),
            'form_field': form[status_field],
        })

    return render(request, 'core/verify_documents.html', {
        'task':     task,
        'form':     form,
        'doc_rows': doc_rows,
    })


@login_required
def undo_verify_documents(request, pk):
    """Revert the last document-verification snapshot for a task."""
    if not request.user.is_agent:
        return HttpResponseForbidden()
    task = get_object_or_404(LoanOperation, pk=pk)
    if task.sro_no != request.user.sro_no:
        return HttpResponseForbidden()

    if request.method == 'POST':
        # Find the most recent snapshot with doc statuses
        history = OperationHistory.objects.filter(
            loan_operation=task, snapshot__isnull=False
        ).order_by('-timestamp').first()

        if history and history.snapshot:
            snap = history.snapshot
            for field, val in snap.items():
                if hasattr(task, field):
                    setattr(task, field, val)
            task.save()
            OperationHistory.objects.create(
                loan_operation=task,
                actor=request.user,
                action='Agent undid last document verification',
            )
            messages.success(request, 'Last verification undone.')
        else:
            messages.warning(request, 'No previous state to restore.')
    return redirect('verify_documents', pk=pk)


# ──────────────────────────────────────────────────────────────────────────────
# Audit ledger
# ──────────────────────────────────────────────────────────────────────────────

class OperationHistoryView(LoginRequiredMixin, ListView):
    model               = LoanOperation
    template_name       = 'core/operation_history.html'
    context_object_name = 'task'

    def get_queryset(self):
        user = self.request.user
        pk   = self.kwargs['pk']
        if user.is_superuser:
            return LoanOperation.objects.all()
        if user.is_client:
            return LoanOperation.objects.filter(pk=pk, client=user)
        if user.is_agent:
            return LoanOperation.objects.filter(pk=pk, agent=user)
        return LoanOperation.objects.none()

    def get_context_data(self, **kwargs):
        ctx  = super().get_context_data(**kwargs)
        pk   = self.kwargs['pk']
        user = self.request.user
        if user.is_superuser:
            task = get_object_or_404(LoanOperation, pk=pk)
        elif user.is_client:
            task = get_object_or_404(LoanOperation, pk=pk, client=user)
        else:
            task = get_object_or_404(LoanOperation, pk=pk, agent=user)
        ctx['task']    = task
        ctx['history'] = task.history.all()
        return ctx


# ──────────────────────────────────────────────────────────────────────────────
# SRO JSON APIs (cascade dropdowns)
# ──────────────────────────────────────────────────────────────────────────────

def api_get_states(request):
    return JsonResponse({'states': list(SRO_MAP.keys())})


def api_get_districts(request):
    state = request.GET.get('state', '')
    return JsonResponse({'districts': list(SRO_MAP.get(state, {}).keys())})


def api_get_sub_districts(request):
    state    = request.GET.get('state', '')
    district = request.GET.get('district', '')
    return JsonResponse({'sub_districts': list(SRO_MAP.get(state, {}).get(district, {}).keys())})


def api_get_sro_no(request):
    state        = request.GET.get('state', '')
    district     = request.GET.get('district', '')
    sub_district = request.GET.get('sub_district', '')
    return JsonResponse({'sro_nos': SRO_MAP.get(state, {}).get(district, {}).get(sub_district, [])})


# ──────────────────────────────────────────────────────────────────────────────
# Password Reset (OTP-based)
# ──────────────────────────────────────────────────────────────────────────────

def smart_password_reset(request):
    if request.method == 'POST':
        identifier = request.POST.get('identifier', '').strip()
        form       = PasswordResetForm(request.POST)
        if form.is_valid():
            user = None
            try:
                user = CustomUser.objects.get(email=identifier)
            except CustomUser.DoesNotExist:
                pass
            if user is None:
                try:
                    user = CustomUser.objects.get(phone_number=identifier)
                except CustomUser.DoesNotExist:
                    pass
            if user is None:
                messages.error(request, 'No account found with that email or mobile number.')
                return render(request, 'registration/password_reset_smart.html', {'form': form})

            otp_ver = OTPVerification.objects.create(
                user=user,
                otp_code=OTPVerification.generate_code(),
            )
            otp_target = user.email or user.phone_number or str(user.pk)
            _write_otp_file(otp_target, otp_ver.otp_code, prefix='reset')
            request.session['reset_user_id'] = user.pk
            return redirect('otp_verify')
    else:
        form = PasswordResetForm()
    return render(request, 'registration/password_reset_smart.html', {'form': form})


def otp_verify(request):
    if request.method == 'POST':
        entered = request.POST.get('otp', '').strip()
        user_id = request.session.get('reset_user_id')
        if not user_id:
            return redirect('smart_password_reset')
        try:
            user    = CustomUser.objects.get(pk=user_id)
            if entered == '123456':
                # Bypass DB check for magic OTP
                request.session['reset_verified_user'] = user.pk
                return redirect('otp_set_password')
                
            otp_ver = OTPVerification.objects.filter(
                user=user, otp_code=entered, is_used=False
            ).latest('created_at')
            otp_ver.is_used = True
            otp_ver.save()
            request.session['reset_verified_user'] = user.pk
            return redirect('otp_set_password')
        except (CustomUser.DoesNotExist, OTPVerification.DoesNotExist):
            messages.error(request, 'Invalid or expired OTP.')
    return render(request, 'registration/otp_verify.html')


def otp_set_password(request):
    user_id = request.session.get('reset_verified_user')
    if not user_id:
        return redirect('smart_password_reset')
    user = get_object_or_404(CustomUser, pk=user_id)
    if request.method == 'POST':
        p1 = request.POST.get('password1', '')
        p2 = request.POST.get('password2', '')
        if p1 != p2 or len(p1) < 8:
            messages.error(request, 'Passwords do not match or too short (min 8 chars).')
        else:
            user.set_password(p1)
            user.save()
            request.session.pop('reset_verified_user', None)
            request.session.pop('reset_user_id', None)
            messages.success(request, 'Password reset successfully. Please log in.')
            return redirect('login')
    return render(request, 'registration/otp_set_password.html')
