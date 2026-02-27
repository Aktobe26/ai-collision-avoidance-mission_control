import requests


def fetch_tle_group(group_name):

    url = f"https://celestrak.org/NORAD/elements/gp.php?GROUP={group_name}&FORMAT=tle"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        lines = response.text.strip().splitlines()

        satellites = []

        for i in range(0, len(lines), 3):
            if i + 2 < len(lines):
                name = lines[i].strip()
                line1 = lines[i + 1].strip()
                line2 = lines[i + 2].strip()

                satellites.append((name, line1, line2))

        return satellites

    except Exception as e:
        print("TLE fetch error:", e)
        return []
