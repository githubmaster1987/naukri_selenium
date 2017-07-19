import config
from scrapex import *
from scrapex import common
from scrapex.node import Node
from scrapex.excellib import *
from scrapex.http import Proxy
from proxy_list import random_proxy
import common_lib
import os
import argparse
import csv, random
import json
from time import sleep
from datetime import datetime
import sys  
from agent import random_agent
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common import exceptions as EX
from selenium.common.exceptions import *
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

reload(sys)  
sys.setdefaultencoding('utf8')

lock = threading.Lock()

global_s = Scraper(
    use_cache=False, #enable cache globally
    retries=2,
    timeout=240,
    delay=0.5,
    #proxy_file = 'proxy.txt',
    #proxy_auth= 'silicons:1pRnQcg87F',
    use_cookie=True
    )

output_file = "output.csv"
total_cnt = 0

DRIVER_WAITING_SECONDS                  = 60
DRIVER_MEDIUM_WAITING_SECONDS           = 10
DRIVER_SHORT_WAITING_SECONDS            = 5

driver = None

start_url = "https://www.naukri.com/browse-jobs"

username = config.username
userpwd = config.userpwd

keywords = config.keywords

class AnyEc:
    """ Use with WebDriverWait to combine expected_conditions
        in an OR.
    """

    def __init__(self, *args):
        self.ecs = args

    def __call__(self, driver):
        for fn in self.ecs:
            try:
                if fn(driver): return True
            except:
                pass
def wait():
    sleep(random.randrange(1, DRIVER_SHORT_WAITING_SECONDS))

def wait_medium():
    offset_time = random.randrange(DRIVER_SHORT_WAITING_SECONDS +1 ,
        DRIVER_MEDIUM_WAITING_SECONDS)

    # print("Sleep Time: {} ".format(offset_time))
    sleep(offset_time)

def show_exception_detail(e):
    print (e)
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print("{}, {}, {}".format(exc_type, fname, str(exc_tb.tb_lineno)))

def create_url():
    global driver, start_url, total_cnt
    
    # @todo Check to make sure that we have the information needed for this retailer in the DB
    try:
        # @TODO Timeout does not seem to be working here
        
        print('loading url... , {}'.format(start_url))

        driver.get(start_url)
        wait()

        print "Login with user"
        driver.find_element_by_xpath("//a[@id='login_Layer']").click()
        wait()
        
        driver.find_element_by_xpath("//input[@id='eLogin']").send_keys(username)
        wait()

        pwd_obj = driver.find_element_by_xpath("//input[@id='pLogin']")
        pwd_obj.send_keys(userpwd)
        wait()

        pwd_obj.send_keys(Keys.ENTER)
        wait_medium()
        
        driver.get(start_url)
        wait()

        search_div = driver.find_element_by_xpath("//div[@class='qsbfield']")

        #finance, mumbai, 5, 8
        skill_item = search_div.find_element_by_xpath("//div[@id='skill']//input")
        skill_item.click()
        skill_item.send_keys(keywords[0]["Skill"])
        wait()

        location_item = search_div.find_element_by_xpath("//div[@id='location']//input")
        location_item.click()
        location_item.send_keys(keywords[0]["Location"])
        wait()

        experience_item = search_div.find_element_by_xpath("//div[@id='exp_dd']//input")
        experience_item.click()

        li_divs = search_div.find_elements_by_xpath("//div[@id='exp_dd']/div[@class='sDrop']//ul/li")
        print "Experience Len=", len(li_divs)

        for li_div in li_divs:
            if li_div.text.strip() == str(keywords[0]["Experience"]):
                print "Select", li_div.text
                li_div.click()

        wait()

        salary_item = search_div.find_element_by_xpath(".//div[@id='salary_dd']//input")
        salary_item.click()
        li_divs = search_div.find_elements_by_xpath("//div[@id='salary_dd']/div[@class='sDrop']//ul/li")
        print "Experience Len=", len(li_divs)

        for li_div in li_divs:
            if li_div.text.strip() == str(keywords[0]["Salary"]):
                print "Select", li_div.text
                li_div.click()

        wait()
        
        print "Click submit to search"
        driver.find_element_by_xpath("//button[@id='qsbFormBtn']").click()
        wait_medium()

        print "Sory by date"        
        sort_div = driver.find_element_by_xpath("//div[@class='sortBy']")
        sort_div.click()
        wait()
        sort_div.find_element_by_xpath("//ul[@class='list']/li[contains(text(), 'Date')]").click()

        print "Loading job listing"
        job_listings = driver.find_elements_by_xpath("//div[contains(@class, 'srp_container fl')]//div[@type='tuple']")
        stop_find_job = False

        main_window_handle = driver.window_handles[0]
        
        print "Jobs = ", len(job_listings)
        for job_ind, job_listing in enumerate(job_listings):
            driver.switch_to.window(main_window_handle)
            post_date_str = job_listing.find_element_by_xpath("//div[@class='rec_details']/span").text

            print "Job Index=", job_ind, " Post Date =", post_date_str
            # if ("Today" in post_date_str) or ("day ago" in post_date_str):
            #     stop_find_job = True
            #     break

            job_listing.click()
            driver.switch_to.window(driver.window_handles[1])
            wait_medium()

            # url = "https://www.naukri.com/job-listings-Strategic-Account-Manager-Japanese-Clients-Dimension-Data-India-Pvt-Ltd-Mumbai-4-to-9-years-040717003261?src=sortby&sid=15004307983089&xp=2&qp=finance&srcPage=s"
            # driver.get(url)
            # wait_medium()

            WebDriverWait(driver, DRIVER_WAITING_SECONDS).until(
                AnyEc(
                    EC.presence_of_element_located(
                        (By.XPATH, "//button[contains(text(), 'Apply')]")
                    ),
                    EC.presence_of_element_located(
                        (By.XPATH, "//a[contains(text(), 'Apply')]")
                    )
                )
            )

            print "Find Apply Button"
            apply_btn = None
            try:
                apply_btn = driver.find_element_by_xpath("//button[contains(text(), 'Apply')]")
            except Exception as e:
                #print e
                try:
                    apply_btn = driver.find_element_by_xpath("//a[contains(text(), 'Apply')]")
                except Exception as e:
                    #print e
                    pass
            
            #print apply_btn

            if apply_btn != None:
                actions = ActionChains(driver)
                actions.move_to_element(apply_btn)
                actions.click(apply_btn)
                actions.perform()
                #apply_btn.click()
                wait_medium()
                   
            else:
                print "Not found apply button"
                continue

            print "Find Skip Link Button"
            try:
                WebDriverWait(driver, DRIVER_WAITING_SECONDS).until(
                    AnyEc(
                        EC.presence_of_element_located(
                            (By.XPATH, "//a[@id='skip_qup']")
                        ),
                        EC.presence_of_element_located(
                            (By.XPATH, "//a[@id='qup_skip']")
                        ),
                        EC.presence_of_element_located(
                            (By.XPATH, "//button[@id='qupSubmit']")
                        ),
                        EC.presence_of_element_located(
                            (By.XPATH, "//button[@id='qusSubmit']")
                        ),
                    )
                )
            except TimeoutException as t:
                #print t
                driver.close()
                continue
            
            if skip_and_apply(driver) == True:
                continue
            
            # Skip and apply not found
            print "Update and Apply button detect"
            update_and_apply(driver) 
               
            driver.close()
       
    except TimeoutException as ex:
        print('***********Exception1*************')
        show_exception_detail(ex)

    # except Exception, e:
    #     print('***********Exception2*************')
    #     show_exception_detail(e)

def skip_and_apply(self_driver):
    driver = self_driver
    skip_link = None

    try:
        skip_link = driver.find_element_by_xpath("//a[@id='skip_qup']")
    except Exception as e:
        #print e
        try:
            skip_link = driver.find_element_by_xpath("//a[@id='qup_skip']")
        except Exception as e:
            #print e
            pass

    if skip_link != None:
        actions = ActionChains(driver)
        actions.move_to_element(skip_link)
        actions.click(skip_link)
        actions.perform()
        wait_medium()
        return True

    return False

def question_apply(self_driver):
    submit_btn = driver.find_element_by_xpath("//button[@id='qusSubmit']")

    question_divs = driver.find_elements_by_xpath("//div[@class='row txtL']")
    print "Question Div Length = ", len(question_divs)

    for quetion_div in question_divs:
        input_options = quetion_div.find_elements_by_xpath(".//ul[@class='ans']/li/input")
        # print "Len = ", len(input_options)
        random_value = random.randrange(0, len(input_options))
        
        for i, li_div in enumerate(input_options):
            if i == random_value:
                actions = ActionChains(driver)
                actions.move_to_element(li_div)
                actions.click(li_div)
                actions.perform()

                print "Select Answer", li_div.get_attribute("value")
                # li_div.click()
                wait()

    print "Click Submit Button"
    actions = ActionChains(driver)
    actions.move_to_element(submit_btn)
    actions.click(submit_btn)
    actions.perform()
    wait_medium()

    skip_and_apply(driver)

def update_and_apply(self_driver):
    driver = self_driver

    button_value_str = ""
    try:
        submit_btn = driver.find_element_by_xpath("//button[@id='qupSubmit']")
        button_value_str = submit_btn.text.strip()
    except:
        submit_btn = driver.find_element_by_xpath("//button[@id='qusSubmit']")
        button_value_str = submit_btn.text.strip()

    print "Button Value = '", button_value_str ,"'"
    if button_value_str == "Submit and Apply":
        question_apply(driver)
        return

    apply_div = driver.find_element_by_xpath("//div[@id='imsLBMain']")
    
    print "Select Preferred Job Location"
    try:    
        preferred_job_location = apply_div.find_elements_by_xpath("//select[@id='prfLoc']/option")
        
        select_job_location = False
        for i, li_div in enumerate(preferred_job_location):
            if li_div.text.lower().strip() == keywords[0]["Location"].lower():
                print "Select Location", li_div.text
                li_div.click()
                select_job_location = True
                break

            if (i == len(preferred_job_location)) and  (select_job_location == False):
                print "Select Location", li_div.text
                li_div.click()
    except:
        print "Not found preferred job location"

    print "Input resume headline"
    try:
        resume_headline = apply_div.find_element_by_xpath("//textarea[@id='resHd']")
    
        resume_headline.send_keys(Keys.CONTROL + "a");
        resume_headline.send_keys(Keys.DELETE);
        resume_headline.send_keys("I have 5 years of experience in Finance")
    except:
        print "Not found resume"

    
    print "Try to find Current Salary Min"    
    try:
        current_salary_div = apply_div.find_element_by_xpath("//div[@id='qupMinSal_dd']")
        current_salary_input = current_salary_div.find_element_by_xpath("//input[@id='qupMinSal']")
        current_salary_input.click()
        wait()
        current_salary_drop = current_salary_div.find_elements_by_xpath(".//div[@class='sDrop']//ul/li")

        for li_div in current_salary_drop:
            if li_div.text.strip() == str(keywords[0]["Salary"]):
                actions = ActionChains(driver)
                actions.move_to_element(li_div)
                actions.click(li_div)
                actions.perform()

                print "Select Current Salary Min", li_div.text
                # li_div.click()
                wait()
    except:
        print "Not Found Current Salary Min"

    print "Try to find Current Salary Max"    
    try:
        current_salary1_div = apply_div.find_element_by_xpath("//div[@id='qupMaxSal_dd']")
        current_salary1_input = current_salary1_div.find_element_by_xpath("//input[@id='qupMaxSal']")
        current_salary1_input.click()
        wait()
        current_salary1_drop = current_salary1_div.find_elements_by_xpath(".//div[@class='sDrop']//ul/li")

        print "Len = ", len(current_salary1_drop)
        random_value = random.randrange(2, len(current_salary1_drop))
        for i, li_div in enumerate(current_salary1_drop):
            if i == random_value:
                actions = ActionChains(driver)
                actions.move_to_element(li_div)
                actions.click(li_div)
                actions.perform()

                print "Select Current Salary Max", li_div.text
                # li_div.click()
                wait()
    except:
        print 'Not found current salary max'

    print "Try to find course"
    try:
        course_div = apply_div.find_element_by_xpath("//div[@id='courCja']")
        course_input = course_div.find_element_by_xpath("//input[@id='inp_courCja']")
        course_input.click()
        wait()
        course_drop = course_div.find_elements_by_xpath(".//div[@id='dp_courCja']//ul/li/a")
        print "Len = ", len(course_drop)
        random_value = random.randrange(1, len(course_drop))
        for i, li_div in enumerate(course_drop):
            if i == random_value:
                actions = ActionChains(driver)
                actions.move_to_element(li_div)
                actions.click(li_div)
                actions.perform()

                print "Select Course", li_div.text
                # li_div.click()
                wait()

        print "Try to find specialization"
        try:
            specialization_div = apply_div.find_element_by_xpath("//div[@id='specCja']")
            specialization_input = specialization_div.find_element_by_xpath("//input[@id='inp_specCja']")
            specialization_input.click()
            wait()
            specialization_drop = specialization_div.find_elements_by_xpath(".//div[@id='dp_specCja']//ul/li/a")

            print "Len = ", len(specialization_drop)
            random_value = random.randrange(1, len(specialization_drop))

            for i, li_div in enumerate(specialization_drop):
                if i == random_value:
                    actions = ActionChains(driver)
                    actions.move_to_element(li_div)
                    actions.click(li_div)
                    actions.perform()

                    print "Select Specialization", li_div.text
                    # li_div.click()
                    wait()
        except:
            print "Not Found Specialization"

    except:
        print "Not Found Course Part"

    print "Try to find institute"
    try:
        institute = apply_div.find_element_by_xpath("//input[@id='Sug_ugInst']")
        institute.send_keys("Mumbai Science Institute")
        wait()
    except:
        print "Not Found Institute Part"

    print "Try to find passing year"
    try:
        passing_year_div = apply_div.find_element_by_xpath("//div[@id='quppasY_dd']")
        passing_year_input = passing_year_div.find_element_by_xpath("//input[@id='qupPasY']")
        passing_year_input.click()
        wait()
        passing_year_drop = passing_year_div.find_elements_by_xpath(".//div[@class='sDrop']//ul/li")

        print "Len = ", len(passing_year_drop)

        random_value = random.randrange(1, len(passing_year_drop))
        for i, li_div in enumerate(passing_year_drop):
            if i == random_value:
                actions = ActionChains(driver)
                actions.move_to_element(li_div)
                actions.click(li_div)
                actions.perform()
                # li_div.click()

                print "Select Passing Year", li_div.text
                wait()
    except:
        print "Not Found Passing Year Part"

    print "Click Submit Button"
    actions = ActionChains(driver)
    actions.move_to_element(submit_btn)
    actions.click(submit_btn)
    actions.perform()
    wait_medium()

    html = Doc(html = driver.page_source)
    passing_year_err = html.x("//i[@id='qupPasY_err']/text()").strip()
    institute_err = html.x("//i[@id='Sug_ugInst_err']/text()").strip()
    salary_min_err = html.x("//i[@id='qupMinSal_err']/text()").strip()
    resume_err = html.x("//i[@id='resHd_err']/text()").strip()
    
    if passing_year_err != "" or institute_err == "" or salary_min_err == "" or resume_err == "":
        print "manadatory field is required"

if __name__ == '__main__':
    #create_url()
    parser = argparse.ArgumentParser(description="Do something.")
    parser.add_argument('-t', '--threads', type=int, required=False, default=10, help='Number of threads, defaults to 5')
    parser.add_argument('-p', '--proxy', type=int, required=False, default=0, help='Proxy type: 0(standard), 1(Micro leave), 2(Rotating)')
    
    args = parser.parse_args()

    threads_number = args.threads
    proxy_type = args.proxy

    driver = common_lib.create_chrome_driver(None)
    create_url() 
    common_lib.phantom_Quit(driver)