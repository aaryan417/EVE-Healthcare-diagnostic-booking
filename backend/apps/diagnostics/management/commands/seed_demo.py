import os
import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import User
from apps.diagnostics.models import (
    DiagnosticCentre,
    DiagnosticTest,
    CentreTest,
    AppointmentSlot,
    CentreMembership,
)


class Command(BaseCommand):
    help = 'Seeds sample diagnostic centres, pathology tests, imaging services, prices, and appointment slots for demonstration in a safe, idempotent manner.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting demo data seeding...'))

        # Fetch demo credentials from environment variables with safe defaults
        superuser_email = os.environ.get('DEMO_SUPERUSER_EMAIL', 'admin@evehealthcare.com')
        superuser_password = os.environ.get('DEMO_SUPERUSER_PASSWORD', 'AdminPass123!')
        superuser_name = os.environ.get('DEMO_SUPERUSER_NAME', 'Demo Platform Admin')

        centre_admin_a_email = os.environ.get('DEMO_CENTRE_ADMIN_EMAIL', 'centreadmin_a@clinic.com')
        centre_admin_a_password = os.environ.get('DEMO_CENTRE_ADMIN_PASSWORD', 'AdminPass123!')
        centre_admin_a_name = os.environ.get('DEMO_CENTRE_ADMIN_NAME', 'Centre Admin A')

        centre_admin_b_email = os.environ.get('DEMO_CENTRE_ADMIN_B_EMAIL', 'centreadmin_b@clinic.com')
        centre_admin_b_password = os.environ.get('DEMO_CENTRE_ADMIN_B_PASSWORD', 'AdminPass123!')
        centre_admin_b_name = os.environ.get('DEMO_CENTRE_ADMIN_B_NAME', 'Centre Admin B')

        patient_email = os.environ.get('DEMO_PATIENT_EMAIL', 'patient@example.com')
        patient_password = os.environ.get('DEMO_PATIENT_PASSWORD', 'PatientPass123!')
        patient_name = os.environ.get('DEMO_PATIENT_NAME', 'Aaryan Verma')

        # 1. Create/Update Demo Platform Admin / Superuser
        admin_user, created_admin = User.objects.get_or_create(
            email=superuser_email,
            defaults={
                'name': superuser_name,
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            }
        )
        admin_user.set_password(superuser_password)
        admin_user.name = superuser_name
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.is_active = True
        admin_user.save()
        action = 'Created' if created_admin else 'Updated'
        self.stdout.write(f'[{action}] Platform Admin: {admin_user.email}')

        # 2. Create/Update Demo Centre Admins
        centre_admin_a, created_ca_a = User.objects.get_or_create(
            email=centre_admin_a_email,
            defaults={
                'name': centre_admin_a_name,
                'is_staff': False,
                'is_superuser': False,
                'is_active': True,
            }
        )
        centre_admin_a.set_password(centre_admin_a_password)
        centre_admin_a.name = centre_admin_a_name
        centre_admin_a.is_active = True
        centre_admin_a.save()
        action = 'Created' if created_ca_a else 'Updated'
        self.stdout.write(f'[{action}] Centre Admin A: {centre_admin_a.email}')

        centre_admin_b, created_ca_b = User.objects.get_or_create(
            email=centre_admin_b_email,
            defaults={
                'name': centre_admin_b_name,
                'is_staff': False,
                'is_superuser': False,
                'is_active': True,
            }
        )
        centre_admin_b.set_password(centre_admin_b_password)
        centre_admin_b.name = centre_admin_b_name
        centre_admin_b.is_active = True
        centre_admin_b.save()
        action = 'Created' if created_ca_b else 'Updated'
        self.stdout.write(f'[{action}] Centre Admin B: {centre_admin_b.email}')

        # 3. Create/Update Demo Patient User
        patient_user, created_patient = User.objects.get_or_create(
            email=patient_email,
            defaults={
                'name': patient_name,
                'is_staff': False,
                'is_superuser': False,
                'is_active': True,
            }
        )
        patient_user.set_password(patient_password)
        patient_user.name = patient_name
        patient_user.is_active = True
        patient_user.save()
        action = 'Created' if created_patient else 'Updated'
        self.stdout.write(f'[{action}] Patient: {patient_user.email}')

        # 4. Seed Diagnostic Centres
        centres_data = [
            {
                'name': 'Apollo Diagnostics — Indiranagar',
                'address': '100 Feet Road, 12th Main',
                'city': 'Bengaluru',
                'state': 'Karnataka',
                'pincode': '560038',
            },
            {
                'name': 'Metropolis Healthcare — Koramangala',
                'address': '80 Feet Road, 4th Block',
                'city': 'Bengaluru',
                'state': 'Karnataka',
                'pincode': '560034',
            },
            {
                'name': 'Suburban Diagnostics — Bandra West',
                'address': 'Linking Road, Near National Park',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'pincode': '400050',
            },
        ]

        centres = []
        for cdata in centres_data:
            centre, created = DiagnosticCentre.objects.get_or_create(
                name=cdata['name'],
                defaults=cdata
            )
            centres.append(centre)
            action = 'Created' if created else 'Existing'
            self.stdout.write(f'[{action}] Centre: {centre.name}')

        # 5. Create Centre Memberships
        m_a, created_m_a = CentreMembership.objects.get_or_create(
            user=centre_admin_a,
            centre=centres[0],
            defaults={'role': CentreMembership.Role.ADMIN}
        )
        m_b, created_m_b = CentreMembership.objects.get_or_create(
            user=centre_admin_b,
            centre=centres[1],
            defaults={'role': CentreMembership.Role.ADMIN}
        )

        # 6. Seed Diagnostic Tests (7 Pathology + 5 Imaging Services)
        tests_data = [
            # Pathology / Laboratory Tests (Existing 7)
            {
                'name': 'Complete Blood Count (CBC)',
                'description': 'Measures red blood cells, white blood cells, hemoglobin, hematocrit, and platelets.',
            },
            {
                'name': 'Lipid Profile',
                'description': 'Evaluates total cholesterol, HDL, LDL, and triglycerides for cardiovascular health.',
            },
            {
                'name': 'Thyroid Profile (T3, T4, TSH)',
                'description': 'Comprehensive screening for hyperthyroidism and hypothyroidism function.',
            },
            {
                'name': 'HbA1c (Glycated Hemoglobin)',
                'description': 'Assesses average blood sugar levels over the past 2 to 3 months.',
            },
            {
                'name': 'Liver Function Test (LFT)',
                'description': 'Evaluates liver enzyme levels, total bilirubin, albumin, and proteins.',
            },
            {
                'name': 'Kidney Function Test (KFT)',
                'description': 'Checks blood urea nitrogen (BUN), serum creatinine, and electrolytes.',
            },
            {
                'name': 'Vitamin D3 & B12 Panel',
                'description': 'Screens for key micronutrient deficiencies supporting bone and neurological health.',
            },
            # Imaging / Radiology Services (New 5)
            {
                'name': 'MRI Brain',
                'description': 'High-resolution magnetic resonance imaging scan of the brain and cerebral vasculature.',
            },
            {
                'name': 'CT Scan Chest',
                'description': 'Cross-sectional computed tomography scan evaluating lungs, mediastinum, and chest structure.',
            },
            {
                'name': 'Ultrasound Abdomen',
                'description': 'Non-invasive sonogram evaluating liver, gallbladder, pancreas, kidneys, and spleen.',
            },
            {
                'name': 'X-Ray Chest',
                'description': 'Digital diagnostic radiograph screening lungs, heart, ribs, and thoracic cavity.',
            },
            {
                'name': 'PET-CT Scan',
                'description': 'Positron emission tomography combined with CT for advanced metabolic and oncological imaging.',
            },
        ]

        tests = []
        for tdata in tests_data:
            test, created = DiagnosticTest.objects.get_or_create(
                name=tdata['name'],
                defaults=tdata
            )
            tests.append(test)
            action = 'Created' if created else 'Existing'
            self.stdout.write(f'[{action}] Test: {test.name}')

        # 7. Seed Centre-Specific Pricing (CentreTest)
        prices = [
            # Existing Pathology Offerings (16 offerings)
            (0, 0, Decimal('450.00')),
            (0, 1, Decimal('850.00')),
            (0, 2, Decimal('950.00')),
            (0, 3, Decimal('550.00')),
            (0, 4, Decimal('1100.00')),
            (0, 5, Decimal('1050.00')),
            (0, 6, Decimal('1800.00')),
            (1, 0, Decimal('500.00')),
            (1, 1, Decimal('900.00')),
            (1, 2, Decimal('900.00')),
            (1, 3, Decimal('600.00')),
            (1, 4, Decimal('1200.00')),
            (2, 0, Decimal('550.00')),
            (2, 1, Decimal('950.00')),
            (2, 2, Decimal('1000.00')),
            (2, 3, Decimal('650.00')),

            # New Imaging Offerings (15 offerings across 3 centres)
            # MRI Brain (test idx 7)
            (0, 7, Decimal('4200.00')),
            (1, 7, Decimal('4500.00')),
            (2, 7, Decimal('4800.00')),
            # CT Scan Chest (test idx 8)
            (0, 8, Decimal('2800.00')),
            (1, 8, Decimal('3000.00')),
            (2, 8, Decimal('3200.00')),
            # Ultrasound Abdomen (test idx 9)
            (0, 9, Decimal('1200.00')),
            (1, 9, Decimal('1400.00')),
            (2, 9, Decimal('1500.00')),
            # X-Ray Chest (test idx 10)
            (0, 10, Decimal('400.00')),
            (1, 10, Decimal('450.00')),
            (2, 10, Decimal('500.00')),
            # PET-CT Scan (test idx 11)
            (0, 11, Decimal('12500.00')),
            (1, 11, Decimal('13000.00')),
            (2, 11, Decimal('14000.00')),
        ]

        centre_tests = []
        for centre_idx, test_idx, price in prices:
            ct, created = CentreTest.objects.get_or_create(
                centre=centres[centre_idx],
                test=tests[test_idx],
                defaults={'price': price}
            )
            centre_tests.append(ct)

        self.stdout.write(self.style.SUCCESS(f'Seeded {len(centre_tests)} centre test offerings with prices.'))

        # 8. Seed Future Appointment Slots for Next 7 Days (Idempotent)
        today = timezone.now().date()
        time_slots = [
            (datetime.time(8, 0), datetime.time(8, 30)),
            (datetime.time(8, 30), datetime.time(9, 0)),
            (datetime.time(9, 0), datetime.time(9, 30)),
            (datetime.time(9, 30), datetime.time(10, 0)),
            (datetime.time(10, 0), datetime.time(10, 30)),
            (datetime.time(10, 30), datetime.time(11, 0)),
            (datetime.time(11, 0), datetime.time(11, 30)),
            (datetime.time(14, 0), datetime.time(14, 30)),
            (datetime.time(14, 30), datetime.time(15, 0)),
            (datetime.time(15, 0), datetime.time(15, 30)),
        ]

        slot_created_count = 0
        slot_existing_count = 0
        for day_offset in range(1, 8):
            slot_date = today + datetime.timedelta(days=day_offset)
            for ct in centre_tests:
                for start_t, end_t in time_slots:
                    slot, created = AppointmentSlot.objects.get_or_create(
                        centre_test=ct,
                        date=slot_date,
                        start_time=start_t,
                        end_time=end_t,
                        defaults={'capacity': 5}
                    )
                    if created:
                        slot_created_count += 1
                    else:
                        slot_existing_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Appointment slots status across next 7 days: {slot_created_count} created, {slot_existing_count} already existed.'
        ))
        self.stdout.write(self.style.SUCCESS('Demo data seeding complete successfully!'))
