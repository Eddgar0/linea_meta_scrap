from bs4 import BeautifulSoup
import requests
import re


def scrap_table_header(parser):
    data_header = parser.select("div #ctl00_Content_Main_divGrid table tr th")
    header_text = [header.text for header in data_header]
    header = ",".join(header_text) + "\n"
    return header


def scrap_table(parser):
    table_row_tags = parser.select("div #ctl00_Content_Main_divGrid table tr")
    table_rows_tags = table_row_tags[1:-1]
    table_data = []
    for row in table_rows_tags:
        td_tags = row.find_all("td")
        table_row_text = [c.text for c in td_tags]
        table_row = ",".join(table_row_text) + "\n"
        table_data.append(table_row)
    return table_data


def scrap_links_page():
    link_content = requests.get("http://results.lineameta.com/StartPage.aspx?CId=17013&From=1")
    parser = BeautifulSoup(link_content, "html.parser")
    all_races_table = parser.select("#tblAllRaces tr")
    print(all_races_table[0])


def scrap_page_data():
    s = requests.Session()
    url_ = "http://results.lineameta.com/results.aspx?CId=17013&RId=245"
    response = s.get(url_)
    content = response.content
    parser = BeautifulSoup(content, "html.parser")

    # Creating File and saving First page

    try:
        with open("10k_run.csv", "w") as f:
            f.write(scrap_table_header(parser))
            f.writelines(scrap_table(parser))
    except PermissionError:
        print("file could not be created and program can not continue")
        s.close()
        raise

    navigator = parser.select("#ctl00_Content_Main_grdTopPager")
    numbers = navigator[0].find_all("a")
    last_number = int(numbers[-1].text)

    for page in range(2, last_number + 1):
        page_data = navigator[0].find("a", string=page)
        pattern = r"(ctl00\$Content_Main\$ctl[0-9][0-9])"
        js_method = page_data.get("href")
        event_target = re.findall(pattern, js_method)[0]
        view_state = parser.find("input", id="__VIEWSTATE")["value"]
        print(page, event_target)

        form_data = {"__EVENTTARGET": event_target, "__VIEWSTATE": view_state}
        response = s.post(url_,  data=form_data, )
        content = response.content
        parser = BeautifulSoup(content, "html.parser")
        navigator = parser.select("#ctl00_Content_Main_grdTopPager")

        try:
            with open("10k_run.txt", "a") as f:
                f.writelines(scrap_table(parser))
        except (FileNotFoundError, PermissionError):
            print("file could not be written and program can not continue")
            s.close()
            raise
    s.close()


scrap_links_page()
