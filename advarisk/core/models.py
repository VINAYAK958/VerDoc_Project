from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


ROLE_CHOICES = [
    ('CLIENT', 'Client'),
    ('AGENT',  'Agent'),
]

STATUS_CHOICES = [
    ('PENDING',     'Pending'),
    ('IN_PROGRESS', 'In Progress'),
    ('COMPLETED',   'Completed'),
]

OPERATION_TYPE_CHOICES = [
    ('RAISE',  'Raise Loan'),
    ('PAYOFF', 'Pay Off Loan'),
]

DOC_STATUS_CHOICES = [
    ('PENDING',   'Pending'),
    ('APPROVED',  'Approved'),
    ('REJECTED',  'Rejected'),
]


# ── Admin-managed SRO location hierarchy ─────────────────────────────────────

class SROState(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='State Name')

    class Meta:
        ordering = ['name']
        verbose_name = 'State'
        verbose_name_plural = 'States'

    def __str__(self):
        return self.name


class SRODistrict(models.Model):
    state = models.ForeignKey(SROState, on_delete=models.CASCADE, related_name='districts')
    name  = models.CharField(max_length=100, verbose_name='District Name')

    class Meta:
        ordering = ['name']
        unique_together = [('state', 'name')]
        verbose_name = 'District'
        verbose_name_plural = 'Districts'

    def __str__(self):
        return f'{self.name} ({self.state})'


class SROSubDistrict(models.Model):
    district = models.ForeignKey(SRODistrict, on_delete=models.CASCADE, related_name='sub_districts')
    name     = models.CharField(max_length=100, verbose_name='Sub-District Name')

    class Meta:
        ordering = ['name']
        unique_together = [('district', 'name')]
        verbose_name = 'Sub-District'
        verbose_name_plural = 'Sub-Districts'

    def __str__(self):
        return f'{self.name} ({self.district.name}, {self.district.state.name})'


class SROOffice(models.Model):
    sub_district = models.ForeignKey(SROSubDistrict, on_delete=models.CASCADE, related_name='offices')
    sro_code     = models.CharField(max_length=50, unique=True, verbose_name='SRO Code')
    sro_name     = models.CharField(max_length=200, blank=True, verbose_name='SRO Name')

    class Meta:
        ordering = ['sro_code']
        verbose_name = 'SRO Office'
        verbose_name_plural = 'SRO Offices'

    def __str__(self):
        return f'{self.sro_code} — {self.sub_district}'


# ── Users ─────────────────────────────────────────────────────────────────────

class CustomUser(AbstractUser):
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='CLIENT')

    # Phone — required for agents, optional for clients
    phone_number = models.CharField(
        max_length=10, unique=True, null=True, blank=True,
        help_text='10-digit mobile number (mandatory for Agents)',
    )

    # Email — unique across all users; used by clients to log in
    email = models.EmailField(unique=True)

    # Identity documents — unique and mandatory for both roles
    aadhar_number = models.CharField(
        max_length=12, blank=True, default='', unique=False,
        verbose_name='Aadhaar Number',
        help_text='12-digit Aadhaar number (format: XXXX XXXX XXXX)',
    )
    pan_number = models.CharField(
        max_length=10, blank=True, default='', unique=False,
        verbose_name='PAN Number',
        help_text='10-character PAN (e.g. ABCDE1234F)',
    )

    # Location / SRO fields (used by Agents only)
    state        = models.CharField(max_length=100, blank=True, null=True)
    district     = models.CharField(max_length=100, blank=True, null=True)
    sub_district = models.CharField(max_length=100, blank=True, null=True)
    sro_no       = models.CharField(max_length=50, blank=True, null=True, verbose_name='SRO Number')

    # Online/offline tracking
    last_active = models.DateTimeField(null=True, blank=True, verbose_name='Last Active')

    @property
    def is_client(self):
        return self.role == 'CLIENT'

    @property
    def is_agent(self):
        return self.role == 'AGENT'

    @property
    def is_online(self):
        """True if the user has been active within the last 5 minutes."""
        if not self.last_active:
            return False
        return (timezone.now() - self.last_active).total_seconds() < 300

    def __str__(self):
        name = self.get_full_name() or self.email or self.username
        return f'{name} ({self.role})'


# ── Loan Operations ───────────────────────────────────────────────────────────

class LoanOperation(models.Model):
    client = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE,
        related_name='client_operations',
        limit_choices_to={'role': 'CLIENT'},
    )
    agent = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='agent_operations',
        limit_choices_to={'role': 'AGENT'},
    )
    operation_type = models.CharField(max_length=10, choices=OPERATION_TYPE_CHOICES)
    amount         = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    notes          = models.TextField(blank=True, null=True, help_text='Updates from agent')

    # SRO target fields
    state          = models.CharField(max_length=100, blank=True, null=True, verbose_name='Target State')
    district       = models.CharField(max_length=100, blank=True, null=True, verbose_name='Target District')
    sub_district   = models.CharField(max_length=100, blank=True, null=True, verbose_name='Target Sub-District')
    sro_no         = models.CharField(max_length=50, blank=True, null=True, verbose_name='Target SRO Number')

    # Bhu Aadhar / ULPIN
    bhu_aadhar = models.CharField(
        max_length=14, blank=True, null=True,
        verbose_name='Bhu Aadhar (ULPIN)',
        help_text='14-character alphanumeric Unique Land Parcel Identification Number.',
    )

    # Document uploads (8 institutional documents)
    doc_lease_deed    = models.FileField(upload_to='bank_docs/', blank=True, null=True,
        help_text='Registered Lease Deed/Agreement')
    doc_title_deed    = models.FileField(upload_to='bank_docs/', blank=True, null=True,
        help_text='Original Title Deeds (Sale Deed/Conveyance Deed)')
    doc_encumbrance   = models.FileField(upload_to='bank_docs/', blank=True, null=True,
        help_text='Encumbrance Certificate (EC) — 13–30 year period')
    doc_attornment    = models.FileField(upload_to='bank_docs/', blank=True, null=True,
        help_text="Letter of Attornment")
    doc_mother_deed   = models.FileField(upload_to='bank_docs/', blank=True, null=True,
        help_text='Chain of Documents (Mother Deed)')
    doc_building_plan = models.FileField(upload_to='bank_docs/', blank=True, null=True,
        help_text='Approved Building Plan / Sanction Plan')
    doc_occupancy     = models.FileField(upload_to='bank_docs/', blank=True, null=True,
        help_text='Occupancy Certificate / Completion Certificate')
    doc_tax_receipts  = models.FileField(upload_to='bank_docs/', blank=True, null=True,
        help_text='Latest Property Tax Receipts')

    # Per-document verification status (set by agent)
    doc_lease_deed_status    = models.CharField(max_length=10, choices=DOC_STATUS_CHOICES, default='PENDING')
    doc_title_deed_status    = models.CharField(max_length=10, choices=DOC_STATUS_CHOICES, default='PENDING')
    doc_encumbrance_status   = models.CharField(max_length=10, choices=DOC_STATUS_CHOICES, default='PENDING')
    doc_attornment_status    = models.CharField(max_length=10, choices=DOC_STATUS_CHOICES, default='PENDING')
    doc_mother_deed_status   = models.CharField(max_length=10, choices=DOC_STATUS_CHOICES, default='PENDING')
    doc_building_plan_status = models.CharField(max_length=10, choices=DOC_STATUS_CHOICES, default='PENDING')
    doc_occupancy_status     = models.CharField(max_length=10, choices=DOC_STATUS_CHOICES, default='PENDING')
    doc_tax_receipts_status  = models.CharField(max_length=10, choices=DOC_STATUS_CHOICES, default='PENDING')

    # Agent proof upload
    verification_proof = models.FileField(
        upload_to='verification_proofs/', blank=True, null=True,
        help_text='SRO stamped document or receipt',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.get_operation_type_display()} — {self.client} — {self.get_status_display()}'

    @property
    def doc_status_summary(self):
        """Returns a list of (short_label, status) tuples for all 8 documents."""
        return [
            ('Lease Deed',    self.doc_lease_deed_status),
            ('Title Deed',    self.doc_title_deed_status),
            ('EC',            self.doc_encumbrance_status),
            ('Attornment',    self.doc_attornment_status),
            ('Mother Deed',   self.doc_mother_deed_status),
            ('Building Plan', self.doc_building_plan_status),
            ('Occupancy',     self.doc_occupancy_status),
            ('Tax Receipts',  self.doc_tax_receipts_status),
        ]

    @property
    def approved_docs_count(self):
        return sum(1 for _, s in self.doc_status_summary if s == 'APPROVED')

    @property
    def rejected_docs_count(self):
        return sum(1 for _, s in self.doc_status_summary if s == 'REJECTED')

    @property
    def pending_docs_count(self):
        return sum(1 for _, s in self.doc_status_summary if s == 'PENDING')

    @property
    def processed_docs_count(self):
        return self.approved_docs_count + self.rejected_docs_count

    @property
    def is_fully_approved(self):
        return self.approved_docs_count == 8
    @property
    def doc_details(self):
        """Returns a list of (label, status, file) tuples for all 8 documents."""
        return [
            ('Registered Lease Deed/Agreement',    str(self.doc_lease_deed_status),    self.doc_lease_deed),
            ('Original Title Deeds',               str(self.doc_title_deed_status),    self.doc_title_deed),
            ('Encumbrance Certificate (EC)',       str(self.doc_encumbrance_status),   self.doc_encumbrance),
            ('Letter of Attornment',               str(self.doc_attornment_status),    self.doc_attornment),
            ('Chain of Documents (Mother Deed)',   str(self.doc_mother_deed_status),   self.doc_mother_deed),
            ('Approved Building Plan',             str(self.doc_building_plan_status), self.doc_building_plan),
            ('Occupancy / Completion Certificate', str(self.doc_occupancy_status),     self.doc_occupancy),
            ('Property Tax Receipts',              str(self.doc_tax_receipts_status),  self.doc_tax_receipts),
        ]

    @property
    def uploaded_doc_details(self):
        """Returns only those (label, status, file) tuples where a file is actually uploaded."""
        return [d for d in self.doc_details if d[2]]


# ── Audit history ─────────────────────────────────────────────────────────────

class OperationHistory(models.Model):
    loan_operation = models.ForeignKey(LoanOperation, on_delete=models.CASCADE, related_name='history')
    actor          = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    action         = models.TextField()
    # snapshot stores a JSON blob of what changed (for undo)
    snapshot       = models.JSONField(null=True, blank=True)
    timestamp      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.actor} — {self.action[:60]}'


class OTPVerification(models.Model):
    user       = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='otps')
    otp_code   = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used    = models.BooleanField(default=False)

    @classmethod
    def generate_code(cls):
        import random
        return str(random.randint(100000, 999999))

    def __str__(self):
        return f'OTP for {self.user}: {self.otp_code}'
