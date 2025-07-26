import ipdb
import requests

db = ipdb.City("ipipfree.ipdb")

def get_city_from_ip(ip):
    ipinfo = db.find_map(ip, "CN")
    country = ipinfo["country_name"]
    region_name = ipinfo["region_name"]
    city = ipinfo["city_name"]
    if city == "":
        _ , _ , city = get_city_from_ip_online(ip)
    return country, region_name, city


def get_city_from_ip_online(ip):
    url = f"https://ipapi.co/{ip}/json/"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data["country_name"], data["region"], data["city"]
    else:
        return None, None, None
