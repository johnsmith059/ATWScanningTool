from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd

def get_track_name(html):
    soup = BeautifulSoup(html, 'html.parser')
    heading_div = soup.find('div', class_='panel-heading', style="background: #360065")
    if heading_div:
        h3 = heading_div.find('h3')
        if h3:
            return h3.text.strip()
    return "Unknown Track"

def parse_support_track_page(html, base_url):
    soup = BeautifulSoup(html, 'html.parser')
    track_name = get_track_name(html)
    table = soup.find('table', id='ErrorHistory')
    if not table:
        return []

    headers = [th.get_text(strip=True).lower() for th in table.find_all('th')]
    try:
        errors_idx = headers.index('errors')
        details_idx = headers.index('result details')
        tool_name_idx = headers.index('tool name')
    except ValueError:
        return []

    rows_data = []
    for row in table.find_all('tr')[1:]:
        cols = row.find_all('td')
        if not cols or len(cols) < max(errors_idx, details_idx, tool_name_idx) + 1:
            continue

        try:
            errors = int(cols[errors_idx].get_text(strip=True))
        except ValueError:
            errors = 0

        if errors > 0:
            tool_name = cols[tool_name_idx].get_text(strip=True)
            link_tag = cols[details_idx].find('a')
            link = urljoin(base_url, link_tag['href']) if link_tag and link_tag.has_attr('href') else None

            rows_data.append({
                'Track': track_name,
                'Tool Name': tool_name,
                'Errors': errors,
                'Link': link
            })
    return rows_data

def parse_details_page(html, components_to_check):
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table', id='ErrorHistory')
    if not table:
        return {} 

    headers = [th.get_text(strip=True).lower() for th in table.find_all('th')]
    try:
        component_idx = headers.index('component')
    except ValueError:
        return {}  

    component_counts = {}

    for row in table.find_all('tr')[1:]:
        cols = row.find_all('td')
        if not cols or len(cols) <= component_idx:
            continue
        comp_name = cols[component_idx].get_text(strip=True)

        for c in components_to_check:
            if comp_name.strip().lower() == c.strip().lower():
                comp_key = c.strip()
                component_counts[comp_key] = component_counts.get(comp_key, 0) + 1

    return component_counts 
 

