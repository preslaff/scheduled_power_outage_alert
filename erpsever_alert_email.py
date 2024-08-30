import subprocess
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import schedule

LAST_MESSAGE_FILE = "last_message.txt"

def setup_driver():
    # Set up the Chrome driver using WebDriverManager
    driver_path = ChromeDriverManager().install()
    service = Service(driver_path)
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def check_element_presence(driver, css_selector, description):
    element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector)))
    print(f"{description} found: {element.tag_name}")
    return element

def send_email(subject, body, recipient_email):
    try:
        # Prepare the message
        message = f"Subject: {subject}\n\n{body}"
        
        # Use sendmail to send the email
        process = subprocess.Popen(['sendmail', recipient_email], stdin=subprocess.PIPE)
        process.communicate(message.encode('utf-8'))
        
        print(f"Email sent to {recipient_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

def get_last_sent_message():
    if os.path.exists(LAST_MESSAGE_FILE):
        with open(LAST_MESSAGE_FILE, 'r', encoding='utf-8') as file:
            return file.read().strip()
    return None

def set_last_sent_message(message):
    with open(LAST_MESSAGE_FILE, 'w', encoding='utf-8') as file:
        file.write(message)

def check_interruptions(driver, municipality, target_text, recipient_email):
    try:
        url = 'https://www.energo-pro.bg/bg/planirani-prekysvanija'
        driver.get(url)

        # Wait and check for each element in the hierarchy
        check_element_presence(driver, 'div.map-interruptions', 'Map Interruptions div')
        time.sleep(2)  # Give additional time for dynamic content to load

        
        check_element_presence(driver, 'body > div.table.site-table > main', 'Main tag')
        check_element_presence(driver, 'body > div.table.site-table > main > section:nth-of-type(2)', 'Second section')
        check_element_presence(driver, 'body > div.table.site-table > main > section:nth-of-type(2) > div.wrapper', 'Wrapper div')

       # Check for the modal overlay and close it if it exists
        try:
            modal_overlay = driver.find_element(By.CSS_SELECTOR, 'div.modal-overlay')
            if modal_overlay.is_displayed():
                print("Modal overlay detected. Attempting to close.")
                driver.execute_script("arguments[0].click();", modal_overlay)
                time.sleep()  # Give some time for the modal to close
        except Exception as e:
            print(f"No modal overlay found or error occurred: {e}")

                
        # Find and click the desired municipality
        area_items = driver.find_elements(By.CSS_SELECTOR, 'div.item')

        clicked = False
        for item in area_items:
            area_text = item.get_attribute('innerText').strip()  # Get the inner text of the item
            print(f"Found area: {area_text}")  # Debug: Print the area name
            if municipality in area_text:  # Check if the municipality name is part of the text
                print(f"Found and clicking on municipality: {area_text}")
                driver.execute_script("arguments[0].click();", item)
                clicked = True
                break

        if not clicked:
            print(f"Municipality '{municipality}' not found.")
            return

        # Wait for the interruption data to load
        time.sleep(5)  # Wait for the page to load the interruptions

        # Increase the wait time and add a retry mechanism for waiting for the interruption data
        wait = WebDriverWait(driver, 30)
        for attempt in range(3):
            try:
                wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'body > div.table.site-table > main > section:nth-of-type(2) div.wrapper div.interruption-data ul#interruption_areas li[data-interruption="for_next_48_hours"]')
                ))
                print(f"Attempt {attempt + 1}: Found the interruption data.")  # Debug statement
                break
            except Exception as e:
                print(f"Attempt {attempt + 1}: Failed to find the interruption data: {e}")
                time.sleep(5)  # Wait before retrying

        # Retrieve the interruption data
        interruptions = driver.find_elements(
            By.CSS_SELECTOR, 'body > div.table.site-table > main > section:nth-of-type(2) div.wrapper div.interruption-data ul#interruption_areas li[data-interruption="for_next_48_hours"]'
        )
        
        print(f"Found {len(interruptions)} interruption entries.")  # Debug statement
        
        if not interruptions:
            print("No planned power interruptions found.")  # Message if no interruptions are found

        for interruption in interruptions:
            try:
                interruption_text = interruption.find_element(By.CSS_SELECTOR, 'div.text').text.strip()
                interruption_period = interruption.find_element(By.CSS_SELECTOR, 'div.period').text.strip()
                message_text = f"Period: {interruption_period}\nDetails: {interruption_text}"
                if target_text in interruption_text:
                    print("Match found!")
                    last_message = get_last_sent_message()
                    if message_text != last_message:
                        send_email(f"Interruption Alert for {target_text}", message_text, recipient_email)
                        set_last_sent_message(message_text)
                    else:
                        print("Message already sent. Skipping.")
                    return
            except Exception as e:
                print(f"Failed to retrieve interruption details: {e}")

        print("No matches found.")  # Debug statement

    finally:
        driver.quit()

def job(municipality, target_text, recipient_email):
    driver = setup_driver()
    check_interruptions(driver, municipality, target_text, recipient_email)

if __name__ == "__main__":
    municipality = os.getenv("MUNICIPALITY", "default_municipality")
    target_text = os.getenv("TARGET_TEXT", "default_target_text")
    recipient_email = os.getenv("RECIPIENT_EMAIL", "default_recipient_email")

    # Schedule the job to run every 5 minutes
    schedule.every(1).minutes.do(job, municipality, target_text, recipient_email)
    
    print("Service started...")

    while True:
        schedule.run_pending()
        time.sleep(1)
