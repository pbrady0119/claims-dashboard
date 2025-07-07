import pandas as pd
import random
import uuid
from datetime import datetime, timedelta

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env
project_root = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=project_root / ".env")
output_path = project_root / os.getenv("CLAIMS_DATA_PATH")

n_rows = 100_000
num_patients = 50000

# Patients
patient_ids = [f"PT{i+1:05d}" for i in range(num_patients)]
high_utilizers = patient_ids[:int(num_patients * 0.3)]
regular_patients = patient_ids[int(num_patients * 0.3):]
weighted_patient_pool = (
    random.choices(high_utilizers, k=70000) +
    random.choices(regular_patients, k=30000)
)
random.shuffle(weighted_patient_pool)

# Value Pools
value_pools = {
    "procedure_codes": ['99213', '99214', '99215', '99385', '99386', '99387', '93000', '93010',
                        '80050', '80053', '81001', '81002', '90471', '90472', '36415', '87635',
                        '99406', '29580', '11720'],
    "insurance_plans": ['Blue Cross', 'Aetna', 'UnitedHealthcare', 'Medicare', 'Medicaid', 'Cigna'],
    "denial_reasons": [
        'Coverage not active',
        'Service not covered',
        'Missing prior authorization',
        'Duplicate claim',
        'Incomplete documentation',
        'Exceeded plan limits'
    ],
    "denial_weights": [0.1, 0.15, 0.35, 0.2, 0.15, 0.05],  # realistic skew
    "genders": ['Male', 'Female', 'Unknown'],
    "service_locations": ['Hospital', 'Clinic', 'Telehealth'],
    "providers": [f"PROV{i:03d}" for i in range(1, 21)],
    "provider_weights": [0.1]*2 + [0.05]*3 + [0.04]*5 + [0.03]*10  # Top 2 providers dominate
}

claims = []

for i in range(n_rows):
    claim_id = str(uuid.uuid4())
    patient_id = weighted_patient_pool[i]
    is_outlier = False

    # Patient info
    age = random.randint(18, 99)
    gender = random.choice(value_pools["genders"])

    # Date skewed toward recent
    days_ago = int(random.triangular(0, 730, 0))
    procedure_date = datetime.today() - timedelta(days=days_ago)
    submission_delay = random.randint(0, 30)
    submission_date = procedure_date + timedelta(days=submission_delay)
    procedure_date_str = procedure_date.strftime('%Y-%m-%d')
    submission_date_str = submission_date.strftime('%Y-%m-%d')

    # Insurance
    insurance_plan = random.choice(value_pools["insurance_plans"])
    insurance_multiplier = {
        "Medicaid": 0.6, "Medicare": 1.4, "Cigna": 0.8,
        "Aetna": 0.9, "Blue Cross": 1.0, "UnitedHealthcare": 0.7
    }[insurance_plan]

    # Seasonal Diagnosis
    month = procedure_date.month
    if month in [12, 1, 2]:
        diagnosis_code = random.choices(
            ['J02.9', 'R05', 'B34.9', 'J45.909', 'Z23', 'R07.9',
             'N39.0', 'Z00.00', 'F41.1', 'E11.9', 'I10', 'E78.5',
             'M54.5', 'Z79.899', 'F32.9', 'R10.9', 'Z13.6', 'Z01.419',
             'H52.4', 'S93.4', 'K21.9'],
            weights=[0.15, 0.08, 0.1, 0.1, 0.1, 0.07,
                     0.05, 0.05, 0.04, 0.04, 0.03, 0.03,
                     0.02, 0.02, 0.01, 0.01, 0.01, 0.01,
                     0.005, 0.005, 0.005]
        )[0]
    elif month in [6, 7, 8]:
        diagnosis_code = random.choices(
            ['Z00.00', 'S93.4', 'M54.5', 'R51', 'Z01.419', 'F41.1',
             'I10', 'E11.9', 'Z79.899', 'E78.5', 'Z13.6', 'R10.9',
             'F32.9', 'N39.0', 'Z23', 'H52.4', 'R07.9', 'K21.9',
             'B34.9', 'J02.9', 'J45.909'],
            weights=[0.15, 0.12, 0.1, 0.1, 0.08, 0.07,
                     0.05, 0.05, 0.05, 0.04, 0.03, 0.03,
                     0.02, 0.02, 0.02, 0.01, 0.01, 0.01,
                     0.005, 0.005, 0.005]
        )[0]
    else:
        diagnosis_code = random.choices(
            ['E11.9', 'I10', 'M54.5', 'F41.1', 'K21.9', 'N39.0',
             'Z23', 'Z00.00', 'E78.5', 'Z79.899', 'R07.9', 'B34.9',
             'R05', 'J02.9', 'J45.909', 'F32.9', 'Z13.6', 'H52.4',
             'S93.4', 'R10.9', 'Z01.419'],
            weights=[0.1, 0.1, 0.1, 0.08, 0.07, 0.07,
                     0.06, 0.06, 0.05, 0.05, 0.04, 0.03,
                     0.02, 0.02, 0.02, 0.01, 0.01, 0.01,
                     0.005, 0.005, 0.005]
        )[0]

    procedure_code = random.choice(value_pools["procedure_codes"])
    provider_id = random.choices(value_pools["providers"], weights=value_pools["provider_weights"])[0]
    service_location = random.choice(value_pools["service_locations"])

    # Turnaround time
    if random.random() < 0.005:
        turnaround_days = 0
        is_outlier = True
    else:
        turnaround_days = random.randint(5, 30)

    # Billing by location
    if service_location == "Hospital":
        billed_amount = round(random.uniform(5000, 100000), 2)
    elif service_location == "Clinic":
        billed_amount = round(random.uniform(500, 15000), 2)
    else:
        billed_amount = round(random.uniform(50, 1000), 2)

    # Outlier tag (rarely override above range)
    if random.random() < 0.015:
        billed_amount = round(random.uniform(100000, 200000), 2)
        is_outlier = True

    # Status logic
    pending_chance = random.random()
    if pending_chance < 0.05:
        claim_status = "Pending"
        is_denied = False
        denial_reason = None
        paid_amount = 0.0
    elif pending_chance < 0.15:
        claim_status = "Denied"
        is_denied = True
        denial_reason = random.choices(value_pools["denial_reasons"], weights=value_pools["denial_weights"])[0]
        paid_amount = 0.0
    else:
        if random.random() < 0.02:
            claim_status = "Denied"
            is_denied = True
            denial_reason = "Audited denial – outlier detected"
            paid_amount = 0.0
            is_outlier = True
        else:
            claim_status = "Paid"
            is_denied = False
            denial_reason = None
            paid_amount = round(billed_amount * random.uniform(0.5, 0.9) * insurance_multiplier, 2)

    claims.append({
        "claim_id": claim_id,
        "patient_id": patient_id,
        "age": age,
        "gender": gender,
        "procedure_code": procedure_code,
        "diagnosis_code": diagnosis_code,
        "procedure_date": procedure_date_str,
        "submission_date": submission_date_str,
        "turnaround_days": turnaround_days,
        "insurance_plan": insurance_plan,
        "claim_status": claim_status,
        "is_denied": is_denied,
        "is_outlier": is_outlier,
        "denial_reason": denial_reason,
        "billed_amount": billed_amount,
        "paid_amount": paid_amount,
        "service_location": service_location,
        "provider_id": provider_id
    })

df = pd.DataFrame(claims)
df.to_csv(output_path, index=False)
print(f"✅ CSV with {n_rows:,} claims written to {output_path}")
