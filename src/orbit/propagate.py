from sgp4.api import Satrec, jday
from datetime import datetime, timedelta, timezone

tle_line1 = "1 25544U 98067A   24033.54843750  .00012345  00000+0  10270-3 0  9991"
tle_line2 = "2 25544  51.6432  21.5293 0005071  72.7823  45.1234 15.49712345678901"

sat = Satrec.twoline2rv(tle_line1, tle_line2)

now = datetime.now(timezone.utc)

print("Прогноз координат (км):")

for i in range(0, 60, 10):
    t = now + timedelta(minutes=i)
    jd, fr = jday(
        t.year, t.month, t.day,
        t.hour, t.minute, t.second
    )
    e, r, v = sat.sgp4(jd, fr)
    if e == 0:
        print(f"{i:02d} мин → r={r}")
    else:
        print(f"{i:02d} мин → ошибка расчёта")
