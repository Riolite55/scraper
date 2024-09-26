from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time
import pandas as pd
from utils_consts import *
import os 

chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument("--headless")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
# chrome_options.binary_location= 'new_chromedriver'
driver = webdriver.Chrome(options=chrome_options)
driver.maximize_window()

def post_process_results(term, tenders, term_tenders):

    records = []
    for key, values in tenders.items():
        for value in values:
            record = {'key': key}
            for i, v in enumerate(value):
                record[f'value_{i+1}'] = v
            # print("=====record=====", record)
            records.append(record)
    
    # Create a DataFrame from the list of dictionaries
    df = pd.DataFrame(records)
    df.columns = ["search_term", "publish_date", "competition_type", "subject", "stakeholder", "details", "main_activity", "time_left", "reference_number", "questions_deadline", "proposal_deadline", "proposal_start_date","useless_text","competition_documents_cost","link"]
    df = df.drop(columns = ["details", "useless_text"])
    df['publish_date'] = df['publish_date'].str.replace('تاريخ النشر :', '')
    df["publish_date"] = pd.to_datetime(df["publish_date"])
    df['main_activity'] = df['main_activity'].str.replace('النشاط الأساسي', '')
    df['reference_number'] = df['reference_number'].str.replace('الرقم المرجعي', '')
    df['questions_deadline'] = df['questions_deadline'].str.replace('اخر موعد لإستلام الاستفسارات', '')
    df['proposal_deadline'] = df['proposal_deadline'].str.replace('آخر موعد لتقديم العروض', '')
    df['proposal_start_date'] = df['proposal_start_date'].str.replace('تاريخ ووقت فتح العروض', '')
    df.to_csv(f"tenders_{term}.csv", index=False, encoding='utf-8-sig')
    return df

def get_tenders_from_page(term_tenders):
    parent_tender_divs = driver.find_element(By.XPATH, '//*[@id="cardsresult"]/div[1]')
    child_tender_divs = parent_tender_divs.find_elements(By.CLASS_NAME, "row")
    links = parent_tender_divs.find_elements(By.XPATH,"//a[contains(text(), 'التفاصيل')]")
    links_arr = [el.get_property("href") for el in links]
    # filter divs of interest 
    filtered_child_divs = []
    for div in child_tender_divs:
        if 'الرقم المرجعي' in div.text and 'تاريخ النشر' in div.text:
            filtered_child_divs.append(div)
    i = 0
    for div in filtered_child_divs:
        el = div.text.split('\n')
        el.append(links_arr[i])
        # print("--->length:",len(el))
        term_tenders.append(el)
        if 'تاريخ ووقت فتح العروض' not in div.text:
            el.insert(-3, "N/A")            
        i+=1
        
def start_parsing(term, tenders, term_tenders):
    current_page = 1
    try:
        pages_elements = driver.find_element(By.XPATH, '//*[@id="cardsresult"]/div[2]/div/nav/ul')
    except Exception as e:
        return e.__class__.__name__
    pages = [int(el) for el in pages_elements.text.split('\n') if el.isdigit()]
    pages_passed = {0}
    print(f"parsing results for term: {term}")
    while len(pages)>0:
        # print(current_page)
        pages_passed.add(current_page)
        # print('--')
        # print("pages detected", pages)
        if current_page in pages:
            pages_elements = driver.find_element(By.XPATH, '//*[@id="cardsresult"]/div[2]/div/nav/ul')
            buttons = pages_elements.find_elements(By.TAG_NAME, 'a')
            for button in buttons:
                if int(button.text) == current_page:
                    # print(button.text)
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1.5)
                    button.click()
                    # print(current_page, " clicked")
                    time.sleep(4)
                    pages_elements = driver.find_element(By.XPATH, '//*[@id="cardsresult"]/div[2]/div/nav/ul')
                    pages = [int(el) for el in pages_elements.text.split('\n') if el.isdigit()]
                    
        get_tenders_from_page(term_tenders)
        pages = set(pages)-pages_passed
        # print(pages)
        current_page+=1
        # print("current page:", current_page)
    return 

def setup_search(term, tenders, term_tenders):
    print("getting etimad website..")
    website_url = "https://tenders.etimad.sa/Tender/AllTendersForVisitor?PageNumber=1"
    driver.get(website_url)
    print("got etimad website successfully!!!")
    # expand search
    search_button = driver.find_element(By.XPATH, "//*[@id='searchBtnColaps']")  # Replace 'button_id' with the actual ID or XPath of the button
    search_button.click()

    # click choose tender status
    driver.execute_script("window.scrollBy(0, 500);")
    time.sleep(1)
    status_button = driver.find_element(By.XPATH,"//*[@id='basicInfo']/div/div[2]/div/div/button")
                                                  
    status_button.click()

    # choose active tenders
    driver.execute_script("window.scrollBy(0, 50);")
    time.sleep(1)
    span_element = driver.find_element(By.XPATH,'//*[@id="basicInfo"]/div/div[2]/div/div/div/ul/li[2]/a')                                                                     
    span_element.click()

    driver.execute_script("window.scrollBy(0, 175);")
    time.sleep(1)
    main_activity = driver.find_element(By.XPATH, '//*[@id="basicInfo"]/div/div[4]/div/div/button')
    main_activity.click()

    
    # type اتص to filter results
    
    input_element = driver.find_element(By.XPATH, '//*[@id="basicInfo"]/div/div[4]/div/div/div/div/input')
    input_element.clear()
    input_element.send_keys('اتص')


    # choose ICT
    ICT = driver.find_element(By.XPATH, '//*[@id="basicInfo"]/div/div[4]/div/div/div/ul/li[10]/a')
    ICT.click()

    driver.execute_script("window.scrollBy(0, 50);")
    input_element = driver.find_element(By.XPATH, '//*[@id="txtMultipleSearch"]')
    input_element.clear()

    input_element.send_keys(term)

    # finally hit search
    driver.execute_script("window.scrollBy(0, 35);")
    final_search_button = driver.find_element(By.XPATH,'//*[@id="searchBtn"]') 
    final_search_button.click()
    time.sleep(3)
    res = start_parsing(term, tenders, term_tenders)
    # print("~~",res)
    if res == 'NoSuchElementException':
        return
    else:
        tenders[term] = term_tenders
        post_process_results(term, tenders, term_tenders)
        
        
def get_terms_files(keywords):
    for term in keywords:
        print("--term--: ", term)
        tenders = {}
        term_tenders = []
        try:
            setup_search(term, tenders, term_tenders)
        except Exception as e:
            print(f"Exception encountered: {e}..")
            print(f"skipping term {term}..")
            continue
        
def agg_files():
    directory = os.getcwd()
    dfs = []
    for filename in os.listdir(directory):
        if filename.endswith('.csv'):
            # Read the CSV file into a DataFrame and append to the list
            filepath = os.path.join(directory, filename)
            df = pd.read_csv(filepath)
            dfs.append(df)

    # Concatenate the DataFrames vertically
    combined_df = pd.concat(dfs, axis=0, ignore_index=True)
    combined_df = combined_df.drop_duplicates(subset=["reference_number"])
    combined_df = combined_df[combined_df["search_term"]!="search_term"]
    combined_df = combined_df.sort_values(by=['publish_date', 'stakeholder','subject'])
    pattern = '|'.join(to_exclude)
    filtered_df = combined_df[~combined_df['subject'].str.contains(pattern)]
    filtered_df.to_csv(f"tenders_{today_date}_filtered.csv", index=False, encoding='utf-8-sig')
    filtered_df = pd.read_csv(f"tenders_{today_date}_filtered.csv")
    filtered_df["main_activity"] = filtered_df["main_activity"].apply(lambda x: x.strip())
    filtered_df = filtered_df[filtered_df["main_activity"].isin(["تقنية المعلومات","الإتصالات"])] 
    filtered_df.to_excel(f"tenders_{today_date}_filtered.xlsx", index=False)

