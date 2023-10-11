import re
import time
import os
import glob
from filecmp import cmp

# selenium 4
from selenium import webdriver
import selenium.webdriver.chrome.service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import Select

# Hardcoded login credentials
enrollment = "02-134212-019"  # Replace with your enrollment number
password = "Machine&1"  # Replace with your password
institute = "Karachi Campus"  # Replace with your institute option

# Course Names
courses = {
    "Operating Systems"
    "Operating Systems Lab"
    "Software Engineering"
    "Compiler Construction"
    "Compiler Construction Lab"
    "Design & Analysis of Algorithms"
    "Linear Algebra"
    "Islamic Studies"
}

# Assignment file names
assignment_files = {
    "Operating Systems": ["OS.pdf", "OS.docx"],
    "Operating Systems Lab": ["OS_Lab.pdf", "OS_Lab.docx"],
    "Software Engineering": ["SE.pdf", "SE.docx"],
    "Compiler Construction": ["CC.pdf", "CC.docx"],
    "Compiler Construction Lab": ["CC_Lab.pdf", "CC_Lab.docx"],
    "Design & Analysis of Algorithms": ["DAA.pdf", "DAA.docx"],
    "Linear Algebra": ["LA.pdf", "LA.docx"],
    "Islamic Studies": ["ISL.pdf", "ISL.docx"]
    # Add more courses and assignment file names as needed
}
# Specify the path to the ChromeDriver executable
# chrome_driver_path = "chromedriver.exe"

# Create a Service object
# service = Service(chrome_driver_path)

# Create Chrome options
# chrome_options = webdriver.ChromeOptions()

# Add options as needed
# chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)

# Create a webdriver instance
driver = webdriver.Chrome(service=selenium.webdriver.chrome.service.Service(ChromeDriverManager().install()))
# driver = webdriver.Chrome(service=service, options=chrome_options)

# Login to the student management system
driver.get("https://cms.bahria.edu.pk/Logins/Student/Login.aspx")

enrollment_input = driver.find_element(By.ID, "BodyPH_tbEnrollment")
enrollment_input.send_keys(enrollment)

password_input = driver.find_element(By.ID, "BodyPH_tbPassword")
password_input.send_keys(password)

institute_select = Select(driver.find_element(By.ID, "BodyPH_ddlInstituteID"))
institute_select.select_by_visible_text(institute)

driver.find_element(By.ID, "BodyPH_btnLogin").click()

time.sleep(1)  # Wait for the page to load

# Open the LMS
driver.find_element(By.LINK_TEXT, "Go To LMS").click()

# Wait until the page has finished loading completely
wait = WebDriverWait(driver, 30)  # Adjust the timeout as needed

wait.until(lambda drive: drive.execute_script("return document.readyState") == "complete")

# Switch to the new tab with LMS
driver.switch_to.window(driver.window_handles[-1])

# Open the LMS Assignments page
driver.get("https://lms.bahria.edu.pk/Student/Assignments.php")

wait.until(lambda drive: drive.execute_script("return document.readyState") == "complete")

# Iterate over the courses and assignment files
for course in courses:
    if course in assignment_files:
        assignment_file = assignment_files[course]
        for file_name in assignment_file:
            file_path = os.path.abspath(file_name)
            if os.path.exists(file_path):
                # Locate the Course Dropdown menu
                course_dropdown = Select(driver.find_element(By.ID, "courseId"))
                # Select the desire course by visible text
                course_dropdown.select_by_visible_text(course)
                wait.until(lambda drive: drive.execute_script("return document.readyState") == "complete")

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
                driver.get("https://lms.bahria.edu.pk/Student/Assignments.php")
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
                print(f"Assignment file '{file_name}' does not exist for '{course}'.")
    else:
        print(f"No assignment files specified for '{course}'.")

# Close the browser
driver.quit()
