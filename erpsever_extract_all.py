from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import csv
import time

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

def extract_interruption_data(driver, area):
    data = []
    wait = WebDriverWait(driver, 60)
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul#interruption_areas li[data-interruption="for_next_48_hours"]')))
        interruptions = driver.find_elements(By.CSS_SELECTOR, 'ul#interruption_areas li[data-interruption="for_next_48_hours"]')
        for interruption in interruptions:
            period = interruption.find_element(By.CSS_SELECTOR, 'div.period').text
            text = interruption.find_element(By.CSS_SELECTOR, 'div.text').text
            data.append([area, period, text])
    except Exception as e:
        print(f"Failed to extract interruption data for area {area}: {e}")
    return data

def main():
    url = 'https://www.energo-pro.bg/bg/planirani-prekysvanija'
    driver = setup_driver()
    driver.get(url)

    csv_file = open('interruption_data.csv', mode='w', newline='', encoding='utf-8')
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['Area', 'Period', 'Text'])

    try:
        # Wait for the sidebar to load and then find all area items
        wait = WebDriverWait(driver, 60)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.map-interruptions > div.sidebar > div.areas')))
        
        area_items = driver.find_elements(By.CSS_SELECTOR, 'div.map-interruptions > div.sidebar > div.areas > div.item')

        for item in area_items:
            area = item.find_element(By.TAG_NAME, 'strong').text
            print(f"Processing area: {area}")
            driver.execute_script("arguments[0].click();", item)
            time.sleep(10)  # Wait for the data to load

            # Extract and write interruption data to CSV
            interruption_data = extract_interruption_data(driver, area)
            for row in interruption_data:
                csv_writer.writerow(row)

    finally:
        csv_file.close()
        driver.quit()

if __name__ == "__main__":
    main()
