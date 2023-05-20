import re
import time
import os
import glob
from filecmp import cmp

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import Select

# Hardcoded login credentials
enrollment = "02-134212-019"  # Replace with your enrollment number
password = "QuantumX@1"  # Replace with your password
institute = "Karachi Campus"  # Replace with your institute option

# Subject URLs and assignment file names
subject_urls = {
    "Critical Thinking": "https://lms.bahria.edu.pk/Student/Assignments.php?s=MjAyMzE%3D&oc=MTA2NzY2",
    "Database Management Systems": "https://lms.bahria.edu.pk/Student/Assignments.php?s=MjAyMzE%3D&oc=MTA2NzY4",
    "Database Management Systems Lab": "https://lms.bahria.edu.pk/Student/Assignments.php?s=MjAyMzE%3D&oc=MTA2Nzcw",
    "Data Communication & Networking": "https://lms.bahria.edu.pk/Student/Assignments.php?s=MjAyMzE%3D&oc=MTA2Nzcy",
    "Data Communication & Networking Lab": "https://lms.bahria.edu.pk/Student/Assignments.php?s=MjAyMzE%3D&oc=MTA2Nzc0",
    "Theory of Automata": "https://lms.bahria.edu.pk/Student/Assignments.php?s=MjAyMzE%3D&oc=MTA2Nzc2",
    "Differential Equations": "https://lms.bahria.edu.pk/Student/Assignments.php?s=MjAyMzE%3D&oc=MTA2Nzc4"
}

assignment_files = {
    "Critical Thinking": ["CT.pdf", "CT.docx"],
    "Database Management Systems": ["DBMS.pdf", "DBMS.docx"],
    "Database Management Systems Lab": ["DBMS_Lab.pdf", "DBMS_Lab.docx"],
    "Data Communication & Networking": ["DCN.pdf", "DCN.docx"],
    "Data Communication & Networking Lab": ["DCN_Lab.pdf", "DCN_Lab.docx"],
    "Theory of Automata": ["Automata.pdf", "Automata.docx"],
    "Differential Equations": ["DE.pdf", "DE.docx"]
    # Add more subjects and assignment file names as needed
}
# Specify the path to the ChromeDriver executable
chrome_driver_path = "chromedriver.exe"

# Create a Service object
service = Service(chrome_driver_path)

# Create Chrome options
chrome_options = webdriver.ChromeOptions()

# Add options as needed
# chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)

# Create a webdriver instance
driver = webdriver.Chrome(service=service, options=chrome_options)

# Login to the student management system
driver.get("https://cms.bahria.edu.pk/Logins/Student/Login.aspx")

enrollment_input = driver.find_element(By.ID, "BodyPH_tbEnrollment")
enrollment_input.send_keys(enrollment)

password_input = driver.find_element(By.ID, "BodyPH_tbPassword")
password_input.send_keys(password)

institute_select = Select(driver.find_element(By.ID, "BodyPH_ddlInstituteID"))
institute_select.select_by_visible_text(institute)

driver.find_element(By.ID, "BodyPH_btnLogin").click()

time.sleep(2)  # Wait for the page to load

# Open the LMS
driver.find_element(By.LINK_TEXT, "Go To LMS").click()

# Wait until the page has finished loading completely
wait = WebDriverWait(driver, 30)  # Adjust the timeout as needed

wait.until(lambda drive: drive.execute_script("return document.readyState") == "complete")

# Switch to the new tab with LMS
driver.switch_to.window(driver.window_handles[-1])

# Iterate over the subject URLs and assignment files
for subject, url in subject_urls.items():
    if subject in assignment_files:
        assignment_file = assignment_files[subject]
        for file_name in assignment_file:
            file_path = os.path.abspath(file_name)
            if os.path.exists(file_path):
                # Open the subject URL
                driver.get(url)

                time.sleep(2)  # Wait for the page to load
                # Wait for the submit button to be clickable
                submit_button = wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, "td a.text-red")))

                # Click the submit button
                submit_button.click()
                # Select the file to upload
                file_input = driver.find_element(By.ID, "exampleInputFile")
                file_input.send_keys(file_path)

                # Wait for the modal footer to be visible
                modal_footer = wait.until(ec.visibility_of_element_located((By.CLASS_NAME, "modal-footer")))

                # Find the submit button within the modal footer
                submit_button = modal_footer.find_element(By.CSS_SELECTOR, "button[type='submit']")

                # Check if the submit button is enabled
                if submit_button.is_enabled():
                    # Click the submit button
                    submit_button.click()
                else:
                    print("Submit button is disabled.")

                # Verify the uploaded assignment
                submission_buttons = wait.until(ec.visibility_of_all_elements_located((By.LINK_TEXT, "Submission")))
                submission_buttons[-1].click()
                time.sleep(5)
                # # Determine the file extension
                # uploaded_file_extension = os.path.splitext(file_path)[1].lower()
                # file_type_to_wait = None
                # # Determine the file type to wait for
                # # the file to finish downloading
                # if uploaded_file_extension == ".pdf":
                #     file_type_to_wait = ".pdf"
                # elif uploaded_file_extension == ".docx":
                #     file_type_to_wait = ".docx"
                # else:
                #     print(f"Unsupported file extension: {uploaded_file_extension}")
                #     file_type_to_wait = None
                # if file_type_to_wait:
                #     # Define a custom expected condition to wait for the file to finish downloading
                #     def file_downloaded(d):
                #         files = d.find_elements(By.XPATH, f"//a[contains(@href, '{file_type_to_wait}')]")
                #         return len(files) != 0
                #     # Wait for the file to finish downloading
                #     wait.until(lambda d: file_downloaded(driver))
                # Specify the pattern to match for the downloaded file
                file_pattern = r"02-134212-019-\d+-\d{8}-\d{6}[ap]m"

                # Find the downloaded file based on the pattern
                downloads_folder = os.path.expanduser("~") + "/Downloads/"
                matching_files = [file for file in glob.glob(downloads_folder + "*") if
                                  re.match(file_pattern, os.path.basename(file))]

                if matching_files:
                    matching_files.sort(key=lambda file: os.path.getmtime(file), reverse=True)
                    downloaded_file_path = matching_files[0]  # Get the most recently downloaded file
                    # Compare the uploaded file and the downloaded file
                    if cmp(file_path, downloaded_file_path):
                        print(f"The uploaded file and the downloaded file are the same: {file_name}")
                    else:
                        print(f"The uploaded file and the downloaded file are different: {file_name}")
                        os.startfile(downloaded_file_path)  # Open the file
                else:
                    print(f"No matching file found for pattern '{file_pattern}'.")

            else:
                print(f"Assignment file '{file_name}' does not exist for subject '{subject}'.")
    else:
        print(f"No assignment files specified for subject '{subject}'.")

# Close the browser
driver.quit()
