import os

files = {
    'beneficiary_2015': r'd:\CTS\Datasets\original\All Beneficiary Years\beneficiary_2015.csv',
    'beneficiary_2016': r'd:\CTS\Datasets\original\All Beneficiary Years\beneficiary_2016.csv',
    'beneficiary_2017': r'd:\CTS\Datasets\original\All Beneficiary Years\beneficiary_2017.csv',
    'beneficiary_2018': r'd:\CTS\Datasets\original\All Beneficiary Years\beneficiary_2018.csv',
    'beneficiary_2019': r'd:\CTS\Datasets\original\All Beneficiary Years\beneficiary_2019.csv',
    'beneficiary_2020': r'd:\CTS\Datasets\original\All Beneficiary Years\beneficiary_2020.csv',
    'beneficiary_2021': r'd:\CTS\Datasets\original\All Beneficiary Years\beneficiary_2021.csv',
    'beneficiary_2022': r'd:\CTS\Datasets\original\All Beneficiary Years\beneficiary_2022.csv',
    'beneficiary_2023': r'd:\CTS\Datasets\original\All Beneficiary Years\beneficiary_2023.csv',
    'beneficiary_2024': r'd:\CTS\Datasets\original\All Beneficiary Years\beneficiary_2024.csv',
    'beneficiary_2025': r'd:\CTS\Datasets\original\All Beneficiary Years\beneficiary_2025.csv',
    'inpatient': r'd:\CTS\Datasets\original\inpatient.csv',
    'outpatient': r'd:\CTS\Datasets\original\Outpatient\outpatient.csv',
    'carrier': r'd:\CTS\Datasets\original\Carrier\carrier.csv',
    'HRRP': r'd:\CTS\Datasets\original\FY_2026_Hospital_Readmissions_Reduction_Program_Hospital.csv',
    'DAC': r'd:\CTS\Datasets\original\theme_doctors-clinicians_current\DAC_NationalDownloadableFile.csv',
    'Facility_Affiliation': r'd:\CTS\Datasets\original\theme_doctors-clinicians_current\Facility_Affiliation.csv',
    'Utilization': r'd:\CTS\Datasets\original\theme_doctors-clinicians_current\Utilization_3.csv',
    'ec_public_reporting': r'd:\CTS\Datasets\original\theme_doctors-clinicians_current\ec_public_reporting.csv',
    'ec_score_file': r'd:\CTS\Datasets\original\theme_doctors-clinicians_current\ec_score_file.csv',
    'grp_public_reporting': r'd:\CTS\Datasets\original\theme_doctors-clinicians_current\grp_public_reporting.csv',
}

for name, path in files.items():
    size_mb = os.path.getsize(path) / (1024*1024)
    count = 0
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        for _ in f:
            count += 1
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        header = f.readline().strip()
    sep = '|' if '|' in header else ','
    num_cols = len(header.split(sep))
    print(f'{name}: {count-1:,} data rows | {num_cols} columns | {size_mb:.1f} MB | sep="{sep}"')
