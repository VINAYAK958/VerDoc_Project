import re
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, LoanOperation, DOC_STATUS_CHOICES


# ─────────────────────────── Validators ──────────────────────────────────────

def validate_aadhar(value, exclude_pk=None):
    """Validate 12-digit Aadhaar and check uniqueness."""
    cleaned = re.sub(r'[\s\-]', '', value)
    if not re.match(r'^\d{12}$', cleaned):
        raise forms.ValidationError(
            'Aadhaar must be exactly 12 digits (format: XXXX XXXX XXXX).'
        )
    qs = CustomUser.objects.filter(aadhar_number=cleaned)
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    if qs.exists():
        raise forms.ValidationError('This Aadhaar number is already registered.')
    return cleaned


def validate_pan(value, exclude_pk=None):
    """Validate 10-char PAN (loose format) and check uniqueness."""
    val = value.strip().upper()
    # Loose: 5 letters, 4 digits, 1 letter (the official format is a subset)
    if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', val):
        raise forms.ValidationError(
            'Invalid PAN. Expected format: ABCDE1234F '
            '(5 letters, 4 digits, 1 letter — 10 characters total).'
        )
    qs = CustomUser.objects.filter(pan_number=val)
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    if qs.exists():
        raise forms.ValidationError('This PAN number is already registered.')
    return val


def validate_phone(value):
    """Exactly 10 digits, no spaces or dashes."""
    cleaned = re.sub(r'[\s\-]', '', value)
    if not re.match(r'^\d{10}$', cleaned):
        raise forms.ValidationError('Mobile number must be exactly 10 digits.')
    return cleaned


# ─────────────────── Live-check API helper fields ─────────────────────────────
# These are rendered with data-check-url so JS can AJAX-validate on blur.

def _text(placeholder, extra_cls='', **attrs):
    a = {'placeholder': placeholder, 'class': f'live-check {extra_cls}'.strip(), **attrs}
    return forms.TextInput(attrs=a)


# ────────────────────────── Client Signup Form ────────────────────────────────

class ClientSignupForm(UserCreationForm):
    aadhar_number = forms.CharField(
        max_length=14,
        label='Aadhaar Number',
        help_text='12-digit Aadhaar (XXXX XXXX XXXX) — must be unique',
        widget=forms.TextInput(attrs={
            'id': 'id_aadhar_number',
            'placeholder': 'XXXX XXXX XXXX',
            'maxlength': '14',
            'inputmode': 'numeric',
            'data-check': 'aadhar',
        }),
    )
    pan_number = forms.CharField(
        max_length=10,
        label='PAN Number',
        help_text='10-character PAN (e.g. ABCDE1234F) — must be unique',
        widget=forms.TextInput(attrs={
            'id': 'id_pan_number',
            'placeholder': 'ABCDE1234F',
            'maxlength': '10',
            'style': 'text-transform:uppercase;',
            'data-check': 'pan',
        }),
    )

    class Meta:
        model  = CustomUser
        fields = ['first_name', 'username', 'email', 'aadhar_number', 'pan_number']
        labels = {
            'first_name': 'Full Name',
            'username':   'Username',
            'email':      'Bank Email Address',
        }
        widgets = {
            'email': forms.EmailInput(attrs={
                'placeholder': 'yourname@bank.com',
                'data-check': 'email',
            }),
        }

    def clean_first_name(self):
        val = self.cleaned_data.get('first_name', '').strip()
        if not val:
            raise forms.ValidationError('Full Name is required.')
        return val

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if not email:
            raise forms.ValidationError('Email address is required.')
        qs = CustomUser.objects.filter(email=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('This email is already registered.')
        return email

    def clean_aadhar_number(self):
        pk = self.instance.pk if self.instance else None
        return validate_aadhar(self.cleaned_data.get('aadhar_number', ''), exclude_pk=pk)

    def clean_pan_number(self):
        pk = self.instance.pk if self.instance else None
        return validate_pan(self.cleaned_data.get('pan_number', ''), exclude_pk=pk)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'CLIENT'
        if commit:
            user.save()
        return user


# ────────────────────────── Agent Signup Form ─────────────────────────────────

class AgentSignupForm(UserCreationForm):
    phone_number = forms.CharField(
        max_length=10,
        label='Mobile Number',
        help_text='10-digit mobile number (used to log in)',
        widget=forms.TextInput(attrs={
            'placeholder': '9876543210',
            'maxlength': '10',
            'inputmode': 'numeric',
            'data-check': 'phone',
        }),
    )
    aadhar_number = forms.CharField(
        max_length=14,
        label='Aadhaar Number',
        help_text='12-digit Aadhaar (XXXX XXXX XXXX) — must be unique',
        widget=forms.TextInput(attrs={
            'id': 'id_aadhar_number',
            'placeholder': 'XXXX XXXX XXXX',
            'maxlength': '14',
            'inputmode': 'numeric',
            'data-check': 'aadhar',
        }),
    )
    pan_number = forms.CharField(
        max_length=10,
        label='PAN Number',
        help_text='10-character PAN (e.g. ABCDE1234F) — must be unique',
        widget=forms.TextInput(attrs={
            'id': 'id_pan_number',
            'placeholder': 'ABCDE1234F',
            'maxlength': '10',
            'style': 'text-transform:uppercase;',
            'data-check': 'pan',
        }),
    )

    class Meta:
        model  = CustomUser
        fields = [
            'first_name', 'username', 'email', 'phone_number',
            'aadhar_number', 'pan_number',
            'state', 'district', 'sub_district', 'sro_no',
        ]
        labels = {
            'first_name':   'Full Name',
            'username':     'Username',
            'email':        'Email Address',
            'state':        'State',
            'district':     'District',
            'sub_district': 'Sub-District',
            'sro_no':       'SRO Number',
        }
        widgets = {
            'state':        forms.Select(attrs={'id': 'sro-state'}),
            'district':     forms.Select(attrs={'id': 'sro-district'}),
            'sub_district': forms.Select(attrs={'id': 'sro-sub-district'}),
            'sro_no':       forms.Select(attrs={'id': 'sro-node'}),
            'email': forms.EmailInput(attrs={
                'placeholder': 'agent@email.com',
                'data-check': 'email',
            }),
        }

    def clean_first_name(self):
        val = self.cleaned_data.get('first_name', '').strip()
        if not val:
            raise forms.ValidationError('Full Name is required.')
        return val

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if not email:
            raise forms.ValidationError('Email address is required.')
        qs = CustomUser.objects.filter(email=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('This email is already registered.')
        return email

    def clean_phone_number(self):
        cleaned = validate_phone(self.cleaned_data.get('phone_number', ''))
        qs = CustomUser.objects.filter(phone_number=cleaned)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('This mobile number is already registered.')
        return cleaned

    def clean_aadhar_number(self):
        pk = self.instance.pk if self.instance else None
        return validate_aadhar(self.cleaned_data.get('aadhar_number', ''), exclude_pk=pk)

    def clean_pan_number(self):
        pk = self.instance.pk if self.instance else None
        return validate_pan(self.cleaned_data.get('pan_number', ''), exclude_pk=pk)

    def clean_sro_no(self):
        val = self.cleaned_data.get('sro_no') or ''
        val = str(val).strip()
        if not val:
            raise forms.ValidationError('Please select an SRO from the dropdown.')
        return val

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'AGENT'
        if commit:
            user.save()
        return user


# ─────────────────────────── Loan Operation Form ─────────────────────────────

class LoanOperationForm(forms.ModelForm):
    """
    Loan operation form.
    NOTE: 'amount' is submitted via a HIDDEN input (id_amount) populated by JS.
    The form field uses HiddenInput so it doesn't render a visible widget.
    'amount_display' is NOT a form field — it's a plain HTML input in the template.
    """

    bhu_aadhar = forms.CharField(
        max_length=14,
        required=False,
        label='Bhu Aadhar (ULPIN)',
        help_text='14-char alphanumeric ULPIN — [State 2][District 2][SubDistrict 2][Village 4][Plot 4]',
        widget=forms.TextInput(attrs={
            'id': 'id_bhu_aadhar',
            'placeholder': 'e.g. RJ01020001A001',
            'maxlength': '14',
            'autocomplete': 'off',
        }),
    )

    class Meta:
        model  = LoanOperation
        fields = [
            'amount', 'bhu_aadhar',
            'state', 'district', 'sub_district', 'sro_no',
            'doc_lease_deed', 'doc_title_deed', 'doc_encumbrance',
            'doc_attornment', 'doc_mother_deed', 'doc_building_plan',
            'doc_occupancy', 'doc_tax_receipts',
        ]
        widgets = {
            'state':        forms.Select(attrs={'id': 'sro-state'}),
            'district':     forms.Select(attrs={'id': 'sro-district'}),
            'sub_district': forms.Select(attrs={'id': 'sro-sub-district'}),
            'sro_no':       forms.Select(attrs={'id': 'sro-node'}),
            # amount is hidden — the display input + JS populates it
            'amount':       forms.HiddenInput(attrs={'id': 'id_amount', 'name': 'amount'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['amount'].required = False

    def clean_bhu_aadhar(self):
        value = (self.cleaned_data.get('bhu_aadhar') or '').strip().upper()
        if value and not re.fullmatch(r'[A-Z0-9]{14}', value):
            raise forms.ValidationError('Bhu Aadhar must be exactly 14 alphanumeric characters.')
        return value

    def clean_amount(self):
        # Amount validation is done in the view using request.POST directly.
        # Accept whatever is posted here (or None/blank).
        return self.cleaned_data.get('amount')


# ─────────────────── Live-check API form fields ───────────────────────────────

class LiveCheckForm(forms.Form):
    """Used by AJAX endpoints to check field availability."""
    value = forms.CharField(max_length=200)
    field = forms.ChoiceField(choices=[
        ('email', 'email'), ('phone', 'phone'),
        ('aadhar', 'aadhar'), ('pan', 'pan'),
    ])


# ─────────────────────── Document Verification Form ──────────────────────────

class DocumentVerificationForm(forms.ModelForm):
    """Used by agents to tick/cross each submitted document."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only some documents may be uploaded, so we don't require all statuses in the POST
        for field in self.fields:
            self.fields[field].required = False

    class Meta:
        model  = LoanOperation
        fields = [
            'doc_lease_deed_status', 'doc_title_deed_status',
            'doc_encumbrance_status', 'doc_attornment_status',
            'doc_mother_deed_status', 'doc_building_plan_status',
            'doc_occupancy_status', 'doc_tax_receipts_status',
        ]
        widgets = {f: forms.RadioSelect(choices=DOC_STATUS_CHOICES) for f in fields}


# ─────────────────────────── Task Completion Form ────────────────────────────

class TaskCompletionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['verification_proof'].required = False

    class Meta:
        model  = LoanOperation
        fields = ['verification_proof', 'notes']
        labels = {
            'verification_proof': 'Upload SRO Verification Proof',
            'notes': 'Notes',
        }
        help_texts = {
            'notes': 'Any additional notes about the SRO verification process.',
        }


# ──────────────────────────── Password Reset Form ────────────────────────────

class PasswordResetForm(forms.Form):
    identifier = forms.CharField(
        label='Email or Mobile Number',
        help_text='Clients: enter your bank email. Agents: enter your mobile number or email.',
        widget=forms.TextInput(attrs={
            'id': 'id_identifier',
            'placeholder': 'email@example.com or 9876543210',
            'autocomplete': 'off',
        }),
    )
