import time
import urllib.parse

from bs4 import BeautifulSoup
from selenium import webdriver


def parse(html_content):
    soup = BeautifulSoup(html_content, "lxml")

    for style_tag in soup.find_all("style"):
        style_tag.decompose()

    for tag in soup.find_all(has_attr="style"):
        if "style" in tag.attrs:
            del tag["style"]

    for em_tag in soup.find_all("em"):
        em_tag.unwrap()

    job_list = []

    job_cards = soup.find_all(
        "div",
        class_="job-card"
    )

    top_5_cards = job_cards[:5]

    for card in top_5_cards:
        try:
            title_anchor = card.find(
                "a",
                href=lambda x: x and "/job/" in x
            )

            job_title = (
                title_anchor.get_text(strip=True)
                if title_anchor
                else "資訊缺失"
            )

            job_link = ""

            if title_anchor and "href" in title_anchor.attrs:
                job_link = (
                    "https://www.1111.com.tw"
                    + title_anchor["href"].split("?")[0]
                )

            corp_anchor = card.find(
                "a",
                href=lambda x: x and "/corp/" in x
            )

            company_name = "資訊缺失"

            if corp_anchor:
                company_h2 = corp_anchor.find("h2")

                company_name = (
                    company_h2.get_text(strip=True)
                    if company_h2
                    else corp_anchor.get_text(strip=True)
                )

            condition_texts = [
                item.get_text(strip=True)
                for item in card.find_all(
                    class_="job-card-condition__text"
                )
            ]

            location = "資訊缺失"
            salary = "資訊缺失"
            education = "資訊缺失"
            experience = "資訊缺失"

            for text in condition_texts:

                if any(
                    c in text
                    for c in ["市", "縣", "區", "鄉", "鎮"]
                ):
                    location = text

                elif any(
                    s in text
                    for s in ["薪", "元", "萬", "面議"]
                ):
                    salary = text

                elif any(
                    e in text
                    for e in [
                        "大專",
                        "大學",
                        "高中",
                        "職",
                        "碩",
                        "博",
                        "不限"
                    ]
                ):
                    education = text

                elif "經驗" in text or "年" in text:
                    experience = text

            desc_p = card.find(
                "p",
                class_=lambda x: x and "line-clamp-2" in x
            )

            description = (
                desc_p.get_text(strip=True)
                if desc_p
                else ""
            )

            job_list.append(
                {
                    "job_title": job_title,
                    "company_name": company_name,
                    "location": location,
                    "salary": salary,
                    "education": education,
                    "experience": experience,
                    "description": description,
                    "link": job_link
                }
            )

        except Exception:
            continue

    return job_list


def crawler(ks_input=""):

    if not ks_input:
        print("No Keyword")
        return []

    base_url = "https://www.1111.com.tw/search/job"

    params = {
        "ks": ks_input,
        "sortCss": "datechange"
    }

    url = (
        f"{base_url}?"
        f"{urllib.parse.urlencode(params)}"
    )

    options = webdriver.ChromeOptions()

    options.add_argument(
        "--disable-blink-features=AutomationControlled"
    )

    options.add_experimental_option(
        "excludeSwitches",
        ["enable-automation"]
    )

    options.add_experimental_option(
        "useAutomationExtension",
        False
    )

    driver = webdriver.Chrome(
        options=options
    )

    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source":
            "Object.defineProperty("
            "navigator,"
            "'webdriver',"
            "{get: () => undefined})"
        }
    )

    try:
        driver.get(url)

        time.sleep(6)

        raw_html_source = driver.page_source

        driver.quit()

        return parse(raw_html_source)

    except Exception as e:

        print(f"Fail: {str(e)}")

        try:
            driver.quit()
        except:
            pass

        return []


def run_batch_crawler(keywords: list) -> list:

    if not keywords:
        print("No Keyword")
        return []

    raw_combined_jobs = []

    for kw in keywords:

        results = crawler(
            ks_input=kw
        )

        raw_combined_jobs.extend(results)

        time.sleep(2)

    seen_links = set()

    unique_jobs = []

    for job in raw_combined_jobs:

        if job["link"] not in seen_links:

            seen_links.add(job["link"])

            unique_jobs.append(job)

    for index, job in enumerate(
        unique_jobs,
        start=1
    ):
        unique_jobs[index - 1] = {
            "id": index,
            **job
        }

    return unique_jobs