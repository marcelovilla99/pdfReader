from tabula import read_pdf
import urllib.request
import os
import numpy as np
import re


def load_pdf_data(path):
    print("contractor df....")
    contractor_df = read_pdf(path,  encoding='ISO-8859-1', pages='all', multiple_tables=True, area=[0, 0, 200, 600], stream=True)
    contractor_df = contractor_df[0]

    print("vehicle df....")
    vehicle_df = read_pdf(path,  encoding='ISO-8859-1', pages='all', multiple_tables=True, area=[220, 0, 350, 6000], stream=True)
    vehicle_df = vehicle_df[0]

    print("coverages df....")
    coverages_df = read_pdf(path,  encoding='ISO-8859-1', pages='all', multiple_tables=True, area=[350, 0, 550, 6000], stream=True)
    coverages_df = coverages_df[0]\

    print("valid dates df....")
    valid_df = read_pdf(path,  encoding='ISO-8859-1', pages='all', multiple_tables=True, area=[50, 300, 200, 800], stream=True)
    valid_df = valid_df[0]

    return contractor_df, vehicle_df, coverages_df, valid_df


def parse_contractor_df(df, vehicleInsurance):
    policy_number = df.iloc[1, 2].split('No.')[-1]
    policy_number = re.sub("\D", "", policy_number)

    address_part1 = df.iloc[7, 1].strip()
    address_part2 = df.iloc[8, 1].strip()
    address = address_part1 + ' ' + address_part2

    vehicleInsurance['packageCoverage'] = {
        'name': "",
        'coverages': []
    }

    vehicleInsurance['packageCoverage']['name'] = df.iloc[0, 2]

    vehicleInsurance['contractor'] = {
        'clientCode': df['Unnamed: 0'][2],
        'name': df['Unnamed: 1'][2],
        'rfc':  df['Unnamed: 0'][5],
        'address': address,
        'reference': df['Unnamed: 1'][7],
    }

    vehicleInsurance['policyNumber'] = policy_number

    return vehicleInsurance


def parse_vehicle_df(df, vehicleInsurance):
    description = f"{df.iloc[0, 0]} {df.iloc[1, 0]}"
    series = df.iloc[0, 1]
    model = int(df.iloc[3, 0].split(' ')[0])
    plates = df.iloc[3, 0].split(' ')[1]
    motor = df.iloc[3, 1]
    use = df.iloc[4, 0].split(' ')[1]
    circulatesIn = ' '.join(df.iloc[6, 0].split(' ')[2:])

    vehicleInsurance['insuredVehicles'].append(
        {
            'description': description,
            'series': series,
            'model':  model,
            'plates': plates,
            'motor': motor,
            'use': use,
            'circulatesIn': circulatesIn,
        }
    )

    vehicleInsurance['premiumAmount'] = {
        'netPremium': float(df.columns[3].replace('$', '').replace(',', '')),
        'extra': float(df.iloc[1, 3].replace('$', '').replace(',', '')),
        'right': float(df.iloc[2, 3].replace('$', '').replace(',', '')),
        'tax': float(df.iloc[3, 3].replace('$', '').replace(',', '')),
        'total': float(df.iloc[4, 3].replace('$', '').replace(',', ''))
    }

    return vehicleInsurance


def parse_coverages_df(df, vehicleInsurance):
    condition = df.iloc[:, 0] == 'Total Coberturas y Servicios'
    index = np.where(condition)[0][0]
    df = df.iloc[:index, :]

    coverages = []

    for i, row in df.iterrows():
        parts = row[0].split(' $ ')

        if len(parts) > 1:
            insured_amount = int(parts[1].replace(',', ''))
            description = parts[0]
        else:
            insured_amount = "AMPARADA"
            description = ' '.join(parts[0].split(' ')[:-1])

        deductible = row[1]
        if deductible is not None and deductible == deductible:
            if deductible.endswith(' %'):
                deductible = float(deductible.replace(' %', '')) / 100
            elif deductible == "No aplica":
                deductible = "No aplica"
        else:
            deductible = "NaN"

        coverage = {
            'description': description,
            'insuredAmount': insured_amount,
            'deductible': deductible,
        }

        coverages.append(coverage)

    vehicleInsurance['packageCoverage']['coverages'] = coverages

    return vehicleInsurance


def parse_dates(df, vehicleInsurance):
    column = df.iloc[:, 1]
    start_date = column[3]
    end_date = column[4]

    vehicleInsurance["dates"] = {
        'start': start_date,
        'end': end_date,
    }

    return vehicleInsurance


def extract_gnp_auto_data(url):
    pdf_path = "/tmp/temp3.pdf"
    urllib.request.urlretrieve(url, pdf_path)
    vehicleInsurance = {'insuredVehicles': []}
    contractor_df, vehicle_df, coverages_df, valid_df = load_pdf_data(pdf_path)
    vehicleInsurance = parse_contractor_df(contractor_df, vehicleInsurance)
    vehicleInsurance = parse_vehicle_df(vehicle_df, vehicleInsurance)
    vehicleInsurance = parse_coverages_df(coverages_df, vehicleInsurance)
    vehicleInsurance = parse_dates(valid_df, vehicleInsurance)
    os.remove(pdf_path)
    return vehicleInsurance

