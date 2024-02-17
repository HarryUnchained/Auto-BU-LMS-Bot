import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import NoSuchElementException
import json
import os
import hashlib
import threading


class LMSUploader:
    def __init__(self):
        self.assignment_uploader = None
        self.institute = None
        self.password = None
        self.enrollment = None
        self.credentials_file = "credentials.json"
        self.current_user = None
        self.courses = {}

        self.root = tk.Tk()
        self.root.title("LMS Uploader")
        self.root.geometry("500x400")

        # Login Frame
        self.login_frame = tk.Frame(self.root)
        self.login_frame.pack(padx=10, pady=10)
        tk.Label(self.login_frame, text="Institute:").grid(row=0, column=0)
        self.institute_var = tk.StringVar()
        self.institute_var.set("Select Institute")
        self.institute_dropdown = tk.OptionMenu(self.login_frame, self.institute_var,
                                                "Health Sciences Campus (Karachi)",
                                                "IPP (Karachi)",
                                                "Islamabad E-8 Campus",
                                                "Islamabad H-11 Campus",
                                                "Karachi Campus",
                                                "Lahore Campus",
                                                "NCMPR",
                                                "PN Nursing College",
                                                "PN School Of Logistics")
        self.institute_dropdown.grid(row=0, column=1)
        tk.Button(self.login_frame, text="Login", command=self.login).grid(row=3, column=0, columnspan=2)

        # Main Menu Frame
        self.main_menu_frame = tk.Frame(self.root)
        tk.Button(self.main_menu_frame, text="Add/Edit Courses", command=self.edit_courses).pack(pady=10)
        tk.Button(self.main_menu_frame, text="Upload Assignment", command=self.upload_assignment).pack(pady=10)
        tk.Button(self.main_menu_frame, text="Logout", command=self.logout).pack(pady=10)
        self.main_menu_frame.pack_forget()

        self.root.mainloop()

    def login(self):
        self.institute = self.institute_var.get()

        if not self.institute:
            messagebox.showerror("Error", "Please select an institute.")
            return

        # For simplicity, using hardcoded enrollment and password
        self.enrollment = "02-134212-019"
        self.password = "Machine&1"

        self.current_user = hashlib.sha256((self.enrollment + self.password).encode()).hexdigest()

        self.show_main_menu()

    def show_main_menu(self):
        self.login_frame.pack_forget()
        self.load_courses()
        self.main_menu_frame.pack(padx=10, pady=10)

    def load_courses(self):
        if os.path.exists(self.credentials_file):
            with open(self.credentials_file, "r") as f:
                all_data = json.load(f)

            if self.current_user in all_data:
                user_data = all_data[self.current_user]
                if "courses" in user_data:
                    self.courses = user_data["courses"]
                else:
                    self.courses = {}

    def edit_courses(self):
        self.course_editor = CourseEditor(self.root, self.courses, self.update_courses)

    def update_courses(self, new_courses):
        self.courses = new_courses
        all_data = {}
        if os.path.exists(self.credentials_file):
            with open(self.credentials_file, "r") as f:
                all_data = json.load(f)

        user_data = {"courses": new_courses}
        all_data[self.current_user] = user_data

        with open(self.credentials_file, "w") as f:
            json.dump(all_data, f)

    def upload_assignment(self):
        if not self.courses:
            messagebox.showerror("Error", "Please add/edit courses first.")
            return

        self.assignment_uploader = AssignmentUploader(self.root, self.courses, self.current_user, self.enrollment,
                                                      self.password, self.institute)

    def logout(self):
        self.current_user = None
        self.courses = {}
        self.institute_var.set("Select Institute")
        self.login_frame.pack()


class CourseEditor:
    def __init__(self, master, current_courses, callback):
        self.master = master
        self.current_courses = current_courses
        self.callback = callback

        self.editor_window = tk.Toplevel(master)
        self.editor_window.title("Edit Courses")

        self.course_listbox = tk.Listbox(self.editor_window, selectmode=tk.MULTIPLE)
        self.course_listbox.pack(padx=10, pady=10)

        self.populate_listbox()

        tk.Button(self.editor_window, text="Add Course", command=self.add_course).pack(pady=5)
        tk.Button(self.editor_window, text="Delete Selected", command=self.delete_selected).pack(pady=5)
        tk.Button(self.editor_window, text="Save", command=self.save).pack(pady=10)

    def populate_listbox(self):
        for course, alias in self.current_courses.items():
            self.course_listbox.insert(tk.END, f"{course} ({alias})")

    def add_course(self):
        course = simpledialog.askstring("Add Course", "Enter Course Name:")
        if course:
            alias = simpledialog.askstring("Add Alias", "Enter Alias:")
            if alias:
                self.current_courses[course] = alias
                self.course_listbox.insert(tk.END, f"{course} ({alias})")

    def delete_selected(self):
        selected_indices = self.course_listbox.curselection()
        for index in reversed(selected_indices):
            del self.current_courses[list(self.current_courses.keys())[index]]
            self.course_listbox.delete(index)

    def save(self):
        self.callback(self.current_courses)
        self.editor_window.destroy()


class AssignmentUploader:
    def __init__(self, master, courses, current_user, enrollment, password, institute):
        self.institute = institute
        self.password = password
        self.enrollment = enrollment
        self.master = master
        self.courses = courses
        self.current_user = current_user

        self.upload_window = tk.Toplevel(master)
        self.upload_window.title("Upload Assignment")

        tk.Label(self.upload_window, text="Select a Course:").pack(pady=10)
        self.course_var = tk.StringVar()
        self.course_var.set("Select Course")
        self.course_dropdown = tk.OptionMenu(self.upload_window, self.course_var, *self.courses.keys())
        self.course_dropdown.pack(pady=10)

        tk.Button(self.upload_window, text="Upload Manually", command=self.upload_manually).pack(pady=5)
        tk.Button(self.upload_window, text="Back", command=self.upload_window.destroy).pack(pady=5)

    def upload_manually(self):
        course = self.course_var.get()

        if course not in self.courses:
            messagebox.showerror("Error", "Invalid course name.")
            return

        file_path = filedialog.askopenfilename(title="Select a File")

        if file_path:
            self.upload_window.destroy()
            self.upload_thread = threading.Thread(target=self.upload_file, args=(course, file_path))
            self.upload_thread.start()

    def upload_file(self, course, file_path):
        # Use Selenium to log in and upload the file
        chrome_options = Options()
        chrome_options.add_argument("start-maximized")
        driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=chrome_options)
        driver.get("https://cms.bahria.edu.pk/Logins/Student/Login.aspx")

        def wait_for_page(t_seconds):
            waiting = WebDriverWait(driver, t_seconds)
            waiting.until(lambda drive: drive.execute_script("return document.readyState") == "complete")

        enrollment_input = driver.find_element(By.ID, "BodyPH_tbEnrollment")
        enrollment_input.send_keys(self.enrollment)

        password_input = driver.find_element(By.ID, "BodyPH_tbPassword")
        password_input.send_keys(self.password)

        institute_select = Select(driver.find_element(By.ID, "BodyPH_ddlInstituteID"))
        institute_select.select_by_visible_text(self.institute)

        driver.find_element(By.ID, "BodyPH_btnLogin").click()
        # Wait for the element to be clickable
        element = WebDriverWait(driver, 30).until(
            ec.element_to_be_clickable(
                (By.CSS_SELECTOR, 'a.list-group-item[href="https://cms.bahria.edu.pk/Sys/Common/GoToLMS.aspx"]'))
        )

        # Click the element
        element.click()

        # Switch to the new tab with LMS
        driver.switch_to.window(driver.window_handles[-1])

        # Open the LMS Assignments page
        driver.get("https://lms.bahria.edu.pk/Student/Assignments.php")

        wait_for_page(15)

        # Select the course
        try:
            course_dropdown = Select(driver.find_element(By.ID, "courseId"))
            course_dropdown.select_by_visible_text(course)
        except NoSuchElementException:
            print(f"Course '{course}' not found.")
            driver.quit()
            return

        # Click on the "Upload" button
        try:
            button = WebDriverWait(driver, 3).until(
                ec.presence_of_element_located((By.LINK_TEXT, "Submit"))
            )

            if button:
                button.click()
        except Exception as e:
            print(f"An error occurred: {e}")
            driver.quit()
            messagebox.showerror("Error", "No submission available")
            return

        # Choose the file to upload
        file_input = driver.find_element(By.ID, "exampleInputFile")
        file_input.send_keys(file_path)

        # Wait for the submission to complete
        wait = WebDriverWait(driver, 30)  # Adjust the timeout as needed

        # Wait for the modal to appear
        modal_footer = wait.until(ec.visibility_of_element_located((By.CLASS_NAME, "modal-footer")))

        # Find the submit button within the modal footer
        submit_button = modal_footer.find_element(By.CSS_SELECTOR, "button[type='submit']")
        # Check if the submit button is enabled
        if submit_button.is_enabled():
            # Click the submit button
            submit_button.click()
            messagebox.showinfo("File Uploaded Successfully!", "Exit Chrome")
        else:
            messagebox.showerror("Error", "Submit Button is disabled.")

        # Implement the file comparison logic here
        # Verify the uploaded assignment
        submission_buttons = wait.until(ec.visibility_of_all_elements_located((By.LINK_TEXT, "Submission")))
        submission_buttons[-1].click()


if __name__ == "__main__":
    app = LMSUploader()

