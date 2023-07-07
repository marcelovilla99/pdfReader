from tabula import read_pdf
import re
import urllib.request
import os


def load_pdf_data(path):
    policy_df = read_pdf(path,  encoding='ISO-8859-1', pages='all', multiple_tables=True, area=[120, 0, 300, 600], stream=True)
    policy_df = policy_df[0]

    vehicle_df = read_pdf(path,  encoding='ISO-8859-1', pages='all', multiple_tables=True, area=[340, 0, 1000, 1000], stream=True)
    vehicle_df = vehicle_df[0]

    coverages_df = read_pdf(path,  encoding='ISO-8859-1', pages='all', multiple_tables=True, area=[440, 0, 10000, 10000], stream=True)
    coverages_df = coverages_df[0]

    index = coverages_df[coverages_df['Coberturas amparadas Suma asegurada'].str.contains('Prima neta', na=False)].index[0]
    premiumAmount_df = coverages_df.iloc[index:]

    return policy_df, vehicle_df, coverages_df, premiumAmount_df


def parse_policy_df(df, vehicleInsurance):
    df_clean = df.iloc[:, 0].str.split(':', expand=True)
    start_date = df.loc[0][1].strip().split(' ')[0] + ' 12:00 horas'
    end_date = df.loc[0][4].strip().split(' al ')[-1] + ' 12:00 horas'

    client_code = df_clean.loc[1][3].strip()
    name = df_clean.loc[3][1].strip()
    rfc = df.loc[7][4].strip().split(': ')[-1]

    address_part_1 = df.loc[5][0].strip().split('Domicilio: ')[-1]
    address_part_2 = df.loc[6][0].strip()
    address_part_3 = df.loc[7][0].strip()
    address_part_4 = ", " + df.loc[5][4].strip()
    address = address_part_1 + address_part_2 + address_part_3 + address_part_4

    first_cell_content = df.iloc[0, 0]  # Accessing first cell of the dataframe
    policyNumber = " ".join(first_cell_content.split(" ")[1:3])

    packageCoverageName = ""
    for idx, row in df.iterrows():
        row_as_str = row.to_string()
        if 'Paquete:' in row_as_str:
            packageCoverageName = row_as_str.split('Paquete:')[1].strip().split()[0]
            break

    vehicleInsurance['packageCoverage'] = {
        "name": "",
        "coverages": []
    }

    vehicleInsurance['packageCoverage']['name'] = packageCoverageName

    vehicleInsurance['contractor'] = {
        'name': name,
        'clientCode': client_code,
        'rfc': rfc,
        'address': address
    }

    vehicleInsurance['date'] = {
        'start': start_date,
        'end': end_date,
    }

    vehicleInsurance['policyNumber'] = policyNumber

    return vehicleInsurance


def parse_vehicle_df(df, vehicleInsurance):
    description = df.iloc[0][0].split(': ')[-1]
    series = df.iloc[1][0].split(': ')[-1]
    model = int(df.iloc[1][0].split(': ')[1].split(' ')[0])
    plates = df.iloc[3][0].split(': ')[-1]
    use = df.iloc[4][0].split(': ')[1].split(' ')[0]
    motor = df.iloc[2][0].split()[-1].split(':')[-1]
    make = df.iloc[2][0].split('Marca: ')[1].split('Capacidad')[0].strip()

    if "Placas" in plates:
        plates = ""

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


def parse_coverages_df(df, vehicleInsurance):
    end_index = df[df['Coberturas amparadas Suma asegurada'] == 'Prima neta'].index[0]
    df_clean = df.loc[:end_index - 1]

    coverage_list = []
    for index, row in df_clean.iterrows():
        coverage_dict = {}
        coverage = str(row['Coberturas amparadas Suma asegurada'])
        deductible_data = str(row['Deducible Prima'])

        if "NO APLICA" in deductible_data:
            deductible = 'NO APLICA'
        else:
            match = re.search(r'(\d+\.\d+)\s%', deductible_data)
            if match:
                deductible = float(match.group(1)) / 100
            else:
                deductible = None

        if "VALOR COMERCIAL" in coverage:
            description, insuredAmount = coverage.split("VALOR COMERCIAL")
            insuredAmount = "VALOR COMERCIAL"
        elif "AMPARADA" in coverage:
            description, insuredAmount = coverage.split("AMPARADA")
            insuredAmount = "AMPARADA"
        else:
            match = re.search(r'(\d+[,\d+]*\.\d+|\d+[,\d+]*|\d+)$', coverage)
            if match:
                description = coverage[:match.start()].strip()
                insuredAmount = float(match.group(0).replace(',', ''))
            else:
                description = coverage
                insuredAmount = None

        if deductible:
            coverage_dict['deductible'] = deductible
            coverage_dict['description'] = description
            coverage_dict['insuredAmount'] = insuredAmount
            coverage_list.append(coverage_dict)

    vehicleInsurance['packageCoverage']['coverages'] = coverage_list

    return vehicleInsurance


def parse_premiumAmount_df(df, vehicleInsurance):
    vehicleInsurance['premiumAmount'] = {}
    for index, row in df.iterrows():
        desc = row[0]

        try:
            amount = float(row['Deducible Prima'].replace(',', ''))
        except ValueError:
            continue

        if 'Prima neta' in desc:
            vehicleInsurance['premiumAmount']['netPremium'] = amount
        elif 'Otros descuentos' in desc:
            vehicleInsurance['premiumAmount']['discount'] = amount
        elif 'Financiamiento por pago fraccionado' in desc:
            vehicleInsurance['premiumAmount']['finance'] = amount
        elif 'Gastos de expedición' in desc:
            vehicleInsurance['premiumAmount']['extra'] = amount
        elif 'I.V.A.' in desc:
            vehicleInsurance['premiumAmount']['tax'] = amount
        elif 'Prima total' in desc:
            vehicleInsurance['premiumAmount']['total'] = amount

    return vehicleInsurance


def extract_chubb_auto_data(url):
    pdf_path = "/tmp/temp2.pdf"
    urllib.request.urlretrieve(url, pdf_path)
    vehicleInsurance = {'insuredVehicles': []}
    policy_df, vehicle_df, coverages_df, premiumAmount_df = load_pdf_data(pdf_path)
    vehicleInsurance = parse_policy_df(policy_df, vehicleInsurance)
    vehicleInsurance = parse_vehicle_df(vehicle_df, vehicleInsurance)
    vehicleInsurance = parse_coverages_df(coverages_df, vehicleInsurance)
    vehicleInsurance = parse_premiumAmount_df(premiumAmount_df, vehicleInsurance)
    os.remove(pdf_path)
    return vehicleInsurance

