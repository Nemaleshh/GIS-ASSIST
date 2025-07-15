from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time


import yaml
import os

# ✅ Load config
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

DOWNLOADS_DIR = config["downloads_dir"]
DATA_DIR = config["data_dir"]


import os
import time
from datetime import datetime
def wait_for_download_completion(download_dir, timeout=120, move_to_data_folder=False, target_dir=None):
    import shutil

    start_time = time.time()
    print(f"⏳ Waiting for downloads in: {download_dir}")
    
    while any(f.endswith(".crdownload") for f in os.listdir(download_dir)):
        if time.time() - start_time > timeout:
            print("❌ Timeout: Download did not complete in time.")
            return None
        time.sleep(1)

    downloaded_files = sorted(
        [os.path.join(download_dir, f) for f in os.listdir(download_dir)],
        key=os.path.getmtime,
        reverse=True
    )

    if downloaded_files:
        last_file = downloaded_files[0]
        file_time = datetime.fromtimestamp(os.path.getmtime(last_file)).strftime('%Y-%m-%d %H:%M:%S')
        print(f"✅ Download completed: {last_file}")
        print(f"⏱️ Download finished at: {file_time}")

        if move_to_data_folder and target_dir:
            os.makedirs(target_dir, exist_ok=True)
            new_path = os.path.join(target_dir, os.path.basename(last_file))
            shutil.move(last_file, new_path)
            print(f"📁 Moved to: {new_path}")
            return new_path

        return last_file
    else:
        print("⚠️ No downloaded files found.")
        return None


def login_and_enter_location(username: str, password: str, latitude: str, longitude: str, start_date: str, end_date: str):
    options = Options()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(), options=options)

    try:
        driver.get("https://bhoonidhi.nrsc.gov.in/bhoonidhi/login.html")

        # Step 1: Login
        driver.find_element(By.ID, "login").send_keys(username)
        driver.find_element(By.ID, "password").send_keys(password)
        driver.find_element(By.CSS_SELECTOR, "button.btn.sbtn").click()

        # Step 2: Checkbox
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input.chk[value='AC02']"))
        ).click()

        # Step 3: First Submit
        driver.find_element(By.ID, "buttonFeedBackClass").click()

        # Step 4: Handle Secondary Popup & Dropdown
        try:
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.bootbox-accept"))
            ).click()
            print("⚠️ 'OK' clicked from secondary popup.")

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "SUB_AC02"))
            )
            dropdown = Select(driver.find_element(By.ID, "SUB_AC02"))
            dropdown.select_by_value("Forest cover and type mapping_AC02#05")
            print("✅ Selected dropdown option.")

            driver.find_element(By.ID, "buttonFeedBackClass").click()
            print("✅ Submitted dropdown form.")

        except Exception as e:
            print("⚠️ Skipping secondary popup or dropdown:", e)

        # Step 5: HOME button
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'HOME')]"))
        ).click()
        print("🏠 HOME button clicked.")

        # Step 6: Wait for index.html
        WebDriverWait(driver, 10).until(
            lambda d: "/bhoonidhi/index.html" in d.current_url
        )
        print("✅ Redirected to:", driver.current_url)

        # Step 7: Handle popup in index.html
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.bootbox-accept"))
        ).click()
        print("✅ Index popup 'OK' clicked.")
        time.sleep(2)

        # Step 8: Click on Location tab
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "locPanelLink"))
        ).click()
        print("📍 'Location' tab opened.")

        # Step 9: Enter latitude
        lat_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "LatDeci"))
        )
        lat_input.clear()
        lat_input.send_keys(latitude)
        print(f"✅ Latitude entered: {latitude}")

        # Step 10: Enter longitude
        lng_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "LngDeci"))
        )
        lng_input.clear()
        lng_input.send_keys(longitude)
        print(f"✅ Longitude entered: {longitude}")

        # Step 11: Click Map Location button
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "MapLoc"))
        ).click()
        print("🗺️ 'Map Location' button clicked.")


                
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "sdate")))
            driver.execute_script("document.getElementById('sdate').value = arguments[0];", start_date)
            print(f"📅 Start date set to {start_date}")
        except Exception as e:
            print("❌ Failed to set start date:", e)

        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "edate")))
            driver.execute_script("document.getElementById('edate').value = arguments[0];", end_date)
            print(f"📅 End date set to {end_date}")
        except Exception as e:
            print("❌ Failed to set end date:", e)








        open_data_checkbox = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='checkbox' and contains(@class, 'tw-control')]/following-sibling::text()[contains(., 'OpenData_DirectDownload')]/preceding-sibling::input"))
        )
        driver.execute_script("arguments[0].click();", open_data_checkbox)
        print("✅ 'OpenData_DirectDownload' checkbox selected.")

        # Step:12 Select 'ResourceSat-2_LISS3_L2' checkbox after OpenData_DirectDownload is expanded
        try:
            resource_liss3_checkbox = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@type='checkbox' and @value='ResourceSat-2_LISS3_L2']"))
            )
            driver.execute_script("arguments[0].click();", resource_liss3_checkbox)
            print("✅ 'ResourceSat-2_LISS3_L2' checkbox selected.")
        except Exception as e:
            print("❌ Failed to select 'ResourceSat-2_LISS3_L2':", e)


                    
        try:
            submit_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "getProdButton"))
            )
            submit_button.click()
            print("✅ Submit button clicked.")
        except Exception as e:
            print("❌ Failed to click Submit button:", e)

        #search resuts            
        try:
            search_results_tab = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Search-Results')]"))
            )
            search_results_tab.click()
            print("✅ 'Search-Results' tab clicked.")
        except Exception as e:
            print("❌ Failed to click 'Search-Results' tab:", e)


        try:
            # Wait for the table body to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "resTBody"))
            )

            # Get all rows in the results table
            rows = driver.find_elements(By.CSS_SELECTOR, "#resTBody > tr")
            print(f"📦 Total rows found: {len(rows)}")

            # Loop through each row and click the "Add to Cart" button
            for index, row in enumerate(rows, start=0):
                try:
                    add_button = row.find_element(
                        By.XPATH,
                        ".//button[@id='cartId' and @value='add' and contains(@style, '#337AB7')]"
                    )
                    driver.execute_script("arguments[0].click();", add_button)
                    print(f"🛒 Row {index}: Add to Cart clicked.")
                except Exception as e:
                    print(f"⚠️ Row {index}: No 'Add to Cart' button or failed to click - {e}")

        except Exception as e:
            print("❌ Error processing result rows:", e)


        try:
            cart_tab = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Cart') and @href='#cartDiv']"))
            )
            cart_tab.click()
            print("🛒 'Cart' tab clicked.")
        except Exception as e:
            print("❌ Failed to click 'Cart' tab:", e)

        try:
            confirm_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "confirmCartButton"))
            )
            driver.execute_script("arguments[0].click();", confirm_button)
            print("✅ 'Confirm Cart' button clicked via JS.")
            time.sleep(2)  # Allow backend to process confirmation
        except Exception as e:
            print("❌ Failed to click 'Confirm Cart' button:", e)


        try:
            # Wait for the cart table body to load
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "cartBody")))
            rows = driver.find_elements(By.CSS_SELECTOR, "#cartBody > tr")
            print(f"📦 Total cart items found: {len(rows)}")

            for index, row in enumerate(rows, start=0):
                try:
                    # Check if the button is not marked as already downloaded (i.e., has class 'btn-success')
                    download_button = row.find_element(
                        By.XPATH, ".//button[@id='downloadId' and contains(@class, 'btn-success')]"
                    )

                    # Optional: also check that the title does not say 'already downloaded'
                    title = download_button.get_attribute("title")
                    if "already downloaded" not in title.lower():
                        driver.execute_script("arguments[0].click();", download_button)
                        print(f"⬇️ Row {index}: Download started.")
                        downloaded_file = wait_for_download_completion(
                                        DOWNLOADS_DIR,
                                        move_to_data_folder=True,
                                        target_dir=DATA_DIR
                                    )

                        time.sleep(1)  # Wait a bit between clicks to avoid overwhelming server
                    else:
                        print(f"⏩ Row {index}: Already downloaded, skipping.")

                except Exception as e:
                    print(f"⚠️ Row {index}: Could not click download - {e}")

        except Exception as e:
            print("❌ Error processing download buttons:", e)

        # Optional: wait to see the map loaded
        time.sleep(5)

        # Inject JavaScript to isolate only the map path
        
        # Inject custom SVG into a clean view
        js_hide_left_pane = '''
        const leftPane = document.getElementById("left-pane");
        if (leftPane) {
            leftPane.style.display = "none";
            console.log("✅ Left panel hidden.");
        } else {
            console.log("❌ Left panel not found.");
        }
        '''
        driver.execute_script(js_hide_left_pane)
        print("✅ Left panel (#left-pane) is now hidden.")
        return driver  # you can use driver to proceed further

    except Exception as e:
        print("❌ Error during full automation flow:", e)
        driver.quit()
        return None, None 


