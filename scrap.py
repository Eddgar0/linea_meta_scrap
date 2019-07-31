from bs4 import BeautifulSoup
import requests
import re
import csv


def scrap_table_header(parser):
    """Scrap page header and return a string
         args:
               parser: BeautifulSoup html.parser instance
         returns: returns a string
    """
    data_header = parser.select("div #ctl00_Content_Main_divGrid table tr th")
    header_text = [header.text for header in data_header]
    header = ",".join(header_text) + "\n"
    return header


def scrap_table(parser):
    """scrap content of the table
        args:
              parser: BeautifulSoup html.parser instance
        returns: A list of strings
    """
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
    """Scrap all races links from main page of lineameta.com creates a file called race_links.csv"""
    # races goes from 1 to 180
    # Need to test if race have subraces inside
    with open("race_links.csv", "w", encoding="utf-8") as races_file:
            races_file.write("name,date,link\n")

    for g in range(1, 182, 20):
        home_page = f"http://results.lineameta.com/StartPage.aspx?CId=17013&From={g}"
        print(f"Retrieving links from {home_page}")
        link_content = requests.get(home_page).content
        parser = BeautifulSoup(link_content, "html.parser")
        all_races_table = parser.select("#tblAllRaces tr")
        for race in all_races_table:
            td = race.findAll("td")
            race_link_part = td[1].a.get("href")  # Get part  of the link without domain
            race_date = td[0].span.text.strip()
            race_name = td[1].a.text.strip()
            race_link = f"http://results.lineameta.com/{race_link_part}"

            # testing link this race have sub_races like 10k, 5k etc.
            race_content = requests.get(race_link).content
            t_parser = BeautifulSoup(race_content, "html.parser")
            sub_races = t_parser.select("ul#ctl00_Content_Main_divEvents li.nav-item" )

            with open("race_links.csv", "a") as races_file:
                if sub_races:
                    for li in sub_races:
                        race_sub_category = li.text
                        race_sub_category = race_sub_category.strip()
                        sub_race_link = f"http://results.lineameta.com/{li.a.get('href')}"
                        # Here name of subraces must be constructed appending the distance to name
                        race_data = f"{race_name}_{race_sub_category},{race_date},{sub_race_link}\n"
                        print(race_data)
                        races_file.write(race_data)
                else:
                    race_data = f"{race_name},{race_date},{race_link}\n"
                    print(race_data)
                    races_file.write(race_data)


def scrap_page_data(url_, file_name="scrapped_file.csv"):
    """scrap all data from races on a given link from lineameta.com creates a csv file
        args:
              url_: url from lineameta.com race
              file_name: name of the given File
    """
    s = requests.Session()
    response = s.get(url_)
    content = response.content
    parser = BeautifulSoup(content, "html.parser")
    print(f"processing {file_name}")
    # Creating File and saving First page

    try:
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(scrap_table_header(parser))
            f.writelines(scrap_table(parser))
    except PermissionError:
        print("file could not be created and program can not continue")
        s.close()
        raise

    navigator = parser.select("#ctl00_Content_Main_grdTopPager")
    numbers = navigator[0].find_all("a")
    numbers = [n.text for n in numbers]
    numbers = [int(n) for n in numbers if n.isdigit()]
    last_number = numbers[-1]
    for page in range(2, last_number + 1):
        page_data = navigator[0].find("a", string=page)
        pattern = r"(ctl00\$Content_Main\$ctl[0-9][0-9])"
        js_method = page_data.get("href")
        event_target = re.findall(pattern, js_method)[0]
        view_state = parser.find("input", id="__VIEWSTATE")["value"]
        print(f"Getting data for page{page}")

        form_data = {"__EVENTTARGET": event_target, "__VIEWSTATE": view_state}
        response = s.post(url_,  data=form_data, )
        content = response.content
        parser = BeautifulSoup(content, "html.parser")
        navigator = parser.select("#ctl00_Content_Main_grdTopPager")

        try:
            with open(file_name, "a", encoding="utf-8") as f:
                f.writelines(scrap_table(parser))
        except (FileNotFoundError, PermissionError):
            print("file could not be written and program can not continue")
            s.close()
            raise
    s.close()


def main(csv_file="race_links.csv"):
    failed_links = ""
    with open(csv_file, "r") as race_file:
        race_reader = csv.DictReader(race_file)
        for row in race_reader:
            try:
                scrap_page_data(row["link"], file_name=f"{row['name']}_{row['date']}.csv")
            except Exception as e :
                failed_links= f"{row['name']},{row['date']},{row['link']}\n"
                print(f"could not process this link{row['name'], row['link']} because{e}")
    print(failed_links)

if __name__ == "__main__":
    main()