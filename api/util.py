import ipdb

db = ipdb.City("ipipfree.ipdb")

def get_ip_city(ip):
    ipinfo = db.find_map(ip, "CN")
    country = ipinfo["country_name"]
    region_name = ipinfo["region_name"]
    city = ipinfo["city_name"]
    return country, region_name, city


