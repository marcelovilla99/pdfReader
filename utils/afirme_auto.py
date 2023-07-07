from tabula import read_pdf
import re
import urllib.request
import os


def load_pdf_data(path):
    policyDetail_df = read_pdf(path,  encoding='ISO-8859-1', pages='all', multiple_tables=True, area=[0, 0, 160, 6000], stream=True)
    policyDetail_df = policyDetail_df[0]

    contractor_df = read_pdf(path,  encoding='ISO-8859-1', pages='all', multiple_tables=True, area=[150, 0, 400, 6000], stream=True)
    contractor_df = contractor_df[0]

    vehicle_df = read_pdf(path,  encoding='ISO-8859-1', pages='all', multiple_tables=True, area=[270, 0, 400, 6000], stream=True)
    vehicle_df = vehicle_df[0]

    premiumAmount_df = read_pdf(path,  encoding='ISO-8859-1', pages='all', multiple_tables=True, area=[270, 0, 800, 6000], stream=True)
    premiumAmount_df = premiumAmount_df[0]
    idx = premiumAmount_df[premiumAmount_df.apply(lambda row: row.astype(str).str.contains('Prima Neta:').any(), axis=1)].index[0]
    premiumAmount_df = premiumAmount_df.iloc[idx:]

    premiumAmount_df2 = read_pdf(path,  encoding='ISO-8859-1', pages=2, multiple_tables=True, area=[0, 0, 4000, 6000], stream=True)
    premiumAmount_df2 = premiumAmount_df2[0]

    return policyDetail_df, contractor_df, vehicle_df, premiumAmount_df, premiumAmount_df2


def parse_policyDetail_df(df, vehicleInsurance):
    policy_number = re.search(r'(\d+)', df.columns[3]).group(1)
    start_date = df.iloc[0, 3]
    end_date = df.iloc[1, 3]

    vehicleInsurance = {
        'policyNumber': policy_number,
        'date': {
            'start': start_date,
            'end': end_date
        }
    }
    return vehicleInsurance


def parse_contractor_df(df, vehicleInsurance):
    contractor_name = df.iloc[3, 1]
    rfc = df.iloc[1, 4]
    address1 = df.iloc[1, 1]
    address2 = df.iloc[2, 1]
    postal_code = df.iloc[3, 4]
    address = f"{address1} {address2} C.P.: {postal_code}"

    vehicleInsurance['contractor'] = {
        'name': contractor_name,
        'rfc': rfc,
        'address': address
    }

    return vehicleInsurance


def parse_vehicle_df(df, vehicleInsurance):
    make = df.iloc[0, 1]
    model = int(df.iloc[0, 3])
    description = df.iloc[3, 1]
    motor = df.iloc[5, 5]
    series = df.iloc[3, 5]
    plates = df.iloc[5, 1]
    use = df.iloc[6, 1]

    vehicleInsurance['insuredVehicles'] = []
    vehicleInsurance['insuredVehicles'].append(
        {
            'description': description,
            'series': series,
            'model': model,
            'plates': plates,
            'use': use,
            'motor': motor,
            'make': make
        }
    )

    return vehicleInsurance


def parse_premiumAmount_df(df, df2, vehicleInsurance):
    netPremium = float(df.iloc[0, 4].replace('$', '').replace(',', ''))
    finance = float(df.iloc[1, 4].replace('$', '').replace(',', ''))
    extraAmount = float(df.iloc[3, 4].replace('$', '').replace(',', ''))
    extraCharge = float(df.iloc[4, 4].replace('$', '').replace(',', ''))
    tax = float(df2.iloc[3, 1].replace('$', '').replace(',', ''))
    total = float(df2.iloc[4, 1].replace('$', '').replace(',', ''))

    vehicleInsurance['premiumAmount'] = {
        'netPremium': netPremium,
        'finance': finance,
        'extraAmount': extraAmount,
        'extraCharge': extraCharge,
        'tax': tax,
        'total': total
    }

    return vehicleInsurance


def extract_afirme_auto_data(url):
    pdf_path = "/tmp/temp1.pdf"
    urllib.request.urlretrieve(url, pdf_path)
    vehicleInsurance = {'insuredVehicles': []}
    policyDetail_df, contractor_df, vehicle_df, premiumAmount_df, premiumAmount_df2 = load_pdf_data(pdf_path)
    vehicleInsurance = parse_policyDetail_df(policyDetail_df, vehicleInsurance)
    vehicleInsurance = parse_contractor_df(contractor_df, vehicleInsurance)
    vehicleInsurance = parse_vehicle_df(vehicle_df, vehicleInsurance)
    vehicleInsurance = parse_premiumAmount_df(premiumAmount_df, premiumAmount_df2, vehicleInsurance)
    os.remove(pdf_path)
    return vehicleInsurance


