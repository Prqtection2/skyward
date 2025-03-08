from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class SkywardGPA:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.driver = None
        self.grades_raw = {}
        self.grades = {}
        self.period_gpas = {}
        self.weighted_period_gpas = {}
        # Define the correct order of periods
        self.period_order = ['1U1', '1U2', 'NW1', '2U1', '2U2', 'NW2', 'EX1', 'SM1', 
                            '3U1', '3U2', 'NW3', '4U1', '4U2', 'NW4', 'EX2', 'SM2', 'YR']
        self.ordered_periods = []

    def calculate(self):
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            self.driver = webdriver.Chrome(options=chrome_options)
            self.login()
            self.navigate_to_gradebook()
            self.extract_grades()
            self.calculate_gpas()
            
            return {
                'grades_raw': self.grades_raw,
                'grades': self.grades,
                'unweighted_gpas': self.period_gpas,
                'weighted_gpas': self.weighted_period_gpas,
                'ordered_periods': self.ordered_periods
            }
        finally:
            if self.driver:
                self.driver.quit()

    def login(self):
        try:
            # Access the login page
            self.driver.get("https://skyward-alvinprod.iscorp.com/scripts/wsisa.dll/WService=wsedualvinisdtx/fwemnu01.w")

            # Wait for and enter username
            username_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '/html/body/form[1]/div/div/div[4]/div[2]/div[1]/div[2]/div/table/tbody/tr[1]/td[2]/input'))
            )
            username_input.send_keys(self.username)

            # Enter password
            password_input = self.driver.find_element(By.XPATH, '/html/body/form[1]/div/div/div[4]/div[2]/div[1]/div[2]/div/table/tbody/tr[2]/td[2]/input')
            password_input.send_keys(self.password)

            # Click sign-in button
            sign_in_button = self.driver.find_element(By.XPATH, '/html/body/form[1]/div/div/div[4]/div[2]/div[1]/div[2]/div/table/tbody/tr[7]/td/a')
            sign_in_button.click()

            # Wait for new window to appear or error message
            try:
                WebDriverWait(self.driver, 10).until(lambda d: len(d.window_handles) > 1)
            except:
                # Check for error message
                try:
                    error_element = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'validation-error'))
                    )
                    raise Exception("Incorrect username or password. Please check your credentials and try again.")
                except:
                    raise Exception("Login failed. Please double-check your password and try again. If you're sure your password is correct, try again in a few minutes.")

        except Exception as e:
            if "Incorrect username or password" in str(e) or "Login failed" in str(e):
                raise e
            raise Exception("Login failed. Please double-check your password and try again. If you're sure your password is correct, try again in a few minutes.")

    def navigate_to_gradebook(self):
        # Switch to the new window
        self.driver.switch_to.window(self.driver.window_handles[1])

        # Wait for and click gradebook button
        gradebook_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[2]/div[2]/div[1]/div/ul[2]/li[3]/a'))
        )
        gradebook_button.click()

        # Wait for gradebook to load (wait for the periods header)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[2]/div[2]/div[2]/div/div[4]/div[4]/div[2]/div[1]/div/div[1]/div[1]/table/thead/tr/th'))
        )

    def extract_grades(self):
        # Extract grading periods
        grading_periods_xpath = '/html/body/div[1]/div[2]/div[2]/div[2]/div/div[4]/div[4]/div[2]/div[1]/div/div[1]/div[1]/table/thead/tr/th'
        grading_periods = self.driver.find_elements(By.XPATH, grading_periods_xpath)
        
        # Store period labels
        period_labels = []
        for period in grading_periods:
            try:
                label = period.get_attribute('innerText')
                if label:
                    period_labels.append(label)
                else:
                    period_labels.append('-')
            except:
                period_labels.append('-')

        # Filter periods and maintain the correct order
        self.ordered_periods = [period for period in self.period_order 
                              if period in period_labels and 'C' not in period]

        # Get classes container
        classes_container_xpath = '/html/body/div[1]/div[2]/div[2]/div[2]/div/div[4]/div[4]/div[2]/div[2]/div[2]/table/tbody'
        classes_container = self.driver.find_element(By.XPATH, classes_container_xpath)
        class_rows = classes_container.find_elements(By.XPATH, './tr')

        # Extract grades for each class
        for class_index, class_row in enumerate(class_rows, 1):
            try:
                # Get class name
                class_name_xpath = f'/html/body/div[1]/div[2]/div[2]/div[2]/div/div[4]/div[4]/div[2]/div[2]/div[2]/table/tbody/tr[{class_index}]/td/div/table/tbody/tr[1]/td[2]/span/a'
                class_name = self.driver.find_element(By.XPATH, class_name_xpath).text
                
                # Get grades
                class_grades = {}
                is_valid_class = True

                row_xpath = f'/html/body/div[1]/div[2]/div[2]/div[2]/div/div[4]/div[4]/div[2]/div[1]/div/div[1]/div[2]/table/tbody/tr[{class_index}]'
                cells = self.driver.find_elements(By.XPATH, f'{row_xpath}/td')

                for cell_index, cell in enumerate(cells):
                    try:
                        text = cell.get_attribute('innerText')
                        if text and text.replace('.', '').isnumeric():
                            if cell_index < len(period_labels):
                                class_grades[period_labels[cell_index]] = float(text)
                        elif text:  # If non-numeric grade found
                            is_valid_class = False
                            break
                    except Exception:
                        continue

                if is_valid_class and class_grades:
                    self.grades_raw[class_name] = class_grades
                    filtered_grades = {period: grade for period, grade in class_grades.items() 
                                    if 'C' not in period}
                    if filtered_grades:
                        self.grades[class_name] = filtered_grades

            except Exception:
                continue

    def calculate_gpas(self):
        # Calculate unweighted GPAs
        for period in self.ordered_periods:
            total_gpa = 0
            num_classes = 0
            
            for class_name, class_grades in self.grades.items():
                if period in class_grades:
                    grade = class_grades[period]
                    gpa = 6.0 - (100 - grade) * 0.1
                    total_gpa += gpa
                    num_classes += 1
            
            if num_classes > 0:
                self.period_gpas[period] = total_gpa / num_classes

        # Calculate weighted GPAs
        for period in self.ordered_periods:
            total_gpa = 0
            num_classes = 0
            
            for class_name, class_grades in self.grades.items():
                if period in class_grades:
                    grade = class_grades[period]
                    
                    # Determine base GPA
                    if "APA" in class_name:
                        base_gpa = 7.0
                    elif "AP" in class_name:
                        base_gpa = 8.0
                    else:
                        base_gpa = 6.0
                    
                    weighted_gpa = base_gpa - (100 - grade) * 0.1
                    total_gpa += weighted_gpa
                    num_classes += 1
            
            if num_classes > 0:
                self.weighted_period_gpas[period] = total_gpa / num_classes
