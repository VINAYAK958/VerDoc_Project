"""
SRO_MAP structure:
SRO_MAP[state][district][sub_district] = [list of sro_no strings]
"""

SRO_MAP = {
    "Maharashtra": {
        "Pune": {
            "Khed": ["SRO-Khed-1", "SRO-Khed-2"],
        },
        "Mumbai Suburban": {
            "Andheri": ["SRO-Andheri-East", "SRO-Andheri-West"],
            "Borivali": ["SRO-Borivali-1", "SRO-Borivali-2"],
        },
    },
    "Delhi": {
        "South Delhi": {
            "Vasant Kunj": ["SRO-VA", "SRO-VB"],
            "Mehrauli":    ["SRO-Mehrauli"],
        },
        "New Delhi": {
            "Connaught Place": ["SRO-CP"],
            "Chanakyapuri":    ["SRO-Chanakyapuri"],
        },
    },
    "Karnataka": {
        "Bengaluru Urban": {
            "Basavanagudi": ["SRO-Basavanagudi"],
            "Jayanagar":    ["SRO-Jayanagar"],
            "Shivajinagar": ["SRO-Shivajinagar"],
            "Rajajinagar":  ["SRO-Rajajinagar"],
        },
        "Mysuru": {
            "Mysuru": ["SRO-Mysuru-East", "SRO-Mysuru-West"],
        },
    },
    "Rajasthan": {
        "Jaipur": {
            "Sanganer": ["SRO-Sanganer-1", "SRO-Sanganer-2"],
            "Amer":     ["SRO-Amer"],
        },
        "Jodhpur": {
            "Jodhpur": ["SRO-Jodhpur-East", "SRO-Jodhpur-West"],
        },
    },
    "Uttar Pradesh": {
        "Lucknow": {
            "Sadar":           ["SRO-Sadar-1", "SRO-Sadar-2"],
            "Bakshi Ka Talab": ["SRO-BakshiKaaTalab"],
        },
        "Gautam Buddha Nagar": {
            "Greater Noida": ["SRO-GreNo-1"],
        },
    },
    "Haryana": {
        "Gurugram": {
            "Sohna": ["SRO-Sohna"],
        },
        "Faridabad": {
            "Faridabad": ["SRO-Faridabad-Central", "SRO-Old-Faridabad"],
        },
    },
    "Punjab": {
        "Ludhiana": {
            "Ludhiana West": ["SRO-Ludhiana-West"],
            "Khanna":        ["SRO-Khanna"],
        },
        "Amritsar": {
            "Amritsar": ["SRO-Amritsar-1", "SRO-Amritsar-2"],
        },
    },
}
