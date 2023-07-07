from utils.gnp_auto import extract_gnp_auto_data
from utils.chubb_auto import extract_chubb_auto_data
from utils.afirme_auto import extract_afirme_auto_data


function_map = {
    "GNP": {
        "auto": extract_gnp_auto_data
    },
    "CHUBB": {
        "auto": extract_chubb_auto_data
    },
    "AFIRME": {
        "auto": extract_afirme_auto_data
    }
}


def getResponse(request):
    func = function_map.get(request["issuer"], {}).get(request["policyType"], None)

    if func is not None:
        # If the function is found, call it and save its output
        output = func(request['url'])
        return output
    else:
        # If the function is not found, return an error message
        return "Function not found for the given insuranceCompany and insuranceType"

