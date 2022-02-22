# below are functions to save marketing UTM params to cookie to retrieve them
# on the oauth callback for the tracking functions
def get_utm_params(params: dict) -> dict:
    filtered_params = {
        "utm_department": params.get("utm_department", None),
        "utm_campaign": params.get("utm_campaign", None),
        "utm_medium": params.get("utm_medium", None),
        "utm_source": params.get("utm_source", None),
        "utm_content": params.get("utm_content", None),
        "utm_term": params.get("utm_term", None),
    }
    # remove None values from the dict
    return {k: v for k, v in filtered_params.items() if v is not None}
