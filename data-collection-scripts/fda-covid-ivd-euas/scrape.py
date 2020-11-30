import requests
import csv
import sys

from bs4 import BeautifulSoup

def scrape():
    url = "https://www.fda.gov/emergency-preparedness-and-response/mcm-legal-regulatory-and-policy-framework/emergency-use-authorization#covidinvitrodev"
    sys.stderr.write("getting data from: %s\n" % url)

    page = requests.get(url)

    if page.status_code != 200:
        raise ValueError("failed to get the webpage, expected a 200, got %d" % page.status_code)

    soup = BeautifulSoup(page.text, 'html.parser')

    table = soup.find('table')
    if table == None:
        raise ValueError("failed to get the table from the page, maybe the url is wrong...")

    rows = table.find_all('tr')[1:]

    table_headers = [
      'Date EUA First Issued',
      'Most recent authorization or revision',
      'Entity',
      'Diagnostic (Most Recent Letter of Authorization)',
      'Prduct attributes',
      'Authorized Setting',
      'Authorization Labeling',
      'Amendments and Other Documents',
      'Federal Register Notice for EUA',
      'Other Brand Name(s)'
    ]

    f = csv.writer(sys.stdout)
    f.writerow(table_headers)

    for row in rows:
        cell = []
        for td in row.find_all('td'):
            cell_text = td.text
            if td.a:
                cell_text = get_links(td)
            cell.append(cell_text)

        f.writerow(cell)

    sys.stderr.write("success !!\n")

def get_links(td):
    cell_text = ""
    hrefs = td.find_all('a')
    for h in hrefs:
        href = h.get('href')
        if not href.startswith("https"):
            cell_text = cell_text + "\nhttps://www.fda.gov" + href
        else:
            cell_text = cell_text + "\n" + href
    return cell_text

scrape()
