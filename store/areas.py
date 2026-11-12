"""Districts where we install, for the local area pages at /cctv-installation/<district>/.

Keep this in step with serviceability.INSTALLATION_DISTRICTS: only list places we really install in.
"""
from collections import OrderedDict

AREAS = OrderedDict([
    ("kozhikode", {
        "name": "Kozhikode",
        "intro": ("Our office is on the Payyoli–Perambra Road, so Kozhikode district is home ground for us. "
                  "We plan, supply and install CCTV cameras, video door phones, smart locks and biometric "
                  "systems for homes, shops and offices across the district."),
        "towns": ["Kozhikode city", "Perambra", "Vadakara", "Koyilandy", "Payyoli", "Kuttiady", "Nadapuram",
                  "Balussery", "Thamarassery", "Mukkam", "Feroke", "Ramanattukara", "Kunnamangalam"],
    }),
    ("kannur", {
        "name": "Kannur",
        "intro": ("We install CCTV and security systems across Kannur district, from Kannur town and Thalassery "
                  "to Payyanur and Iritty. Every job starts with a free site survey, so camera positions, "
                  "cabling and recording storage are planned for your building before anything is fitted."),
        "towns": ["Kannur town", "Thalassery", "Payyanur", "Taliparamba", "Mattannur", "Iritty", "Kuthuparamba",
                  "Panoor", "Sreekandapuram", "Anthoor", "Peravoor"],
    }),
    ("malappuram", {
        "name": "Malappuram",
        "intro": ("From Malappuram town to Manjeri, Tirur and Perinthalmanna, we plan and install CCTV, video "
                  "door phones, smart locks and biometric attendance systems for homes and businesses across "
                  "Malappuram district."),
        "towns": ["Malappuram town", "Manjeri", "Perinthalmanna", "Tirur", "Ponnani", "Kottakkal", "Kondotty",
                  "Nilambur", "Tanur", "Valanchery", "Parappanangadi", "Areekode"],
    }),
])

# Categories shown under "What we install" (only those with products on sale appear).
INSTALL_CATEGORY_SLUGS = ["cctv-installation", "homegate-automation", "smart-locks", "biometric-devices",
                          "access-control", "alarm-systems"]
