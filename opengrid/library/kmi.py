import requests
import bs4
import datetime as dt
import pandas as pd


def get_kmi_current_month():
    """
    Gets the current month table from http://www.meteo.be/meteo/view/nl/123763-Huidige+maand.html
    and parse it into a Pandas DataFrame

    Returns
    -------
    Pandas DataFrame
    """
    # start out by getting the html from the website
    html = fetch_website()
    return parse(html)


def fetch_website(url="http://www.meteo.be/meteo/view/nl/123763-Huidige+maand.html"):
    """
    Fetch the website containing the data from http://www.meteo.be/meteo/view/nl/123763-Huidige+maand.html

    Returns
    -------
    str
    """

    r = requests.get(url)

    if r.status_code == 200:
        return r.text
    else:
        raise Exception("Seems like you got code {}".format(r.status_code))


def parse(html):
    """
    Parse the html from http://www.meteo.be/meteo/view/nl/123763-Huidige+maand.html to a Pandas DataFrame

    Parameters
    ----------
    html : str

    Returns
    -------
    Pandas DataFrame
    """
    soup = bs4.BeautifulSoup(html, "html.parser")
    day_values = soup.findAll("tbody")[1]  # the table we want is the second table called 'tbody'
    table_rows = day_values.findAll("tr")

    # parse column names. Take the titles, but remove periods, linebreaks and other artefacts
    titles = table_rows[0].findAll("th")
    column_names = ["_".join(title.text.replace(".", "").split()).lower() for title in titles]

    # parse rows
    # The table has a stupid date format, so it is quite hard to infer the correct date.
    # We start from the back, because the last row should be from yesterday
    # We then work our way back from the date we know into the past
    rows = []
    last_date = dt.date.today()
    for row in reversed(table_rows[2:]):
        values = []
        for title, td in zip(column_names, row.findAll("td")):
            if title == 'datum':
                day = int(td.text.split(" ")[0])  # get day as int from text
                while day != last_date.day:
                    last_date = last_date - dt.timedelta(days=1)
                values.append(last_date)
            elif title == 'zon_duur':
                try:
                    hour, minute = td.text.split(":")
                    time = dt.time(hour=int(hour), minute=int(minute))
                except ValueError:
                    time = pd.NaT
                values.append(time)
            else:
                try:
                    val = float(td.text.replace(",", "."))
                except ValueError:
                    val = float('NaN')
                values.append(val)
        rows.append(values)

    # create DataFrame
    df = pd.DataFrame(rows, columns=column_names).set_index('datum')
    df.index = pd.DatetimeIndex(df.index)
    df = df.sort_index().tz_localize('Europe/Brussels')

    return df