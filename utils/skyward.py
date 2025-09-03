import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import platform
import time
import os
import subprocess
import traceback
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SkywardGPA:
    def __init__(self, username, password, progress_callback=None):
        self.username = username
        self.password = password
        self.progress_callback = progress_callback
        self.driver = None
        self.grades_raw = {}
        self.grades = {}
        self.period_gpas = {}
        self.weighted_period_gpas = {}
        # Define the correct order of periods
        self.period_order = ['1U1', '1U2', 'NW1', '2U1', '2U2', 'NW2', 'EX1', 'SM1', 
                            '3U1', '3U2', 'NW3', '4U1', '4U2', 'NW4', 'EX2', 'SM2', 'YR']
        self.ordered_periods = []
        
        # Only start Xvfb on Linux (Render)
        if platform.system() == 'Linux' and not os.environ.get('DISPLAY'):
            subprocess.Popen(['Xvfb', ':99', '-screen', '0', '1024x768x24'])
            os.environ['DISPLAY'] = ':99'
    
    def send_progress_update(self, message, progress):
        """Send progress update to frontend"""
        logger.info(f"Progress: {progress}% - {message}")
        if self.progress_callback:
            self.progress_callback(message, progress)

    def calculate(self):
        try:
            logger.info("Initializing Chrome driver...")
            # Send initial progress update
            self.send_progress_update("Connecting to Skyward...", 5)
            
            try:
                # Use undetected-chromedriver which handles Chrome installation automatically
                if platform.system() == 'Linux':
                    # On Linux (Render), use undetected-chromedriver
                    self.driver = uc.Chrome(
                        headless=os.environ.get('HEADLESS', 'true').lower() == 'true'
                    )
                else:
                    # On Windows (local development), use regular selenium with local chromedriver
                    options = webdriver.ChromeOptions()
                    options.add_argument('--no-sandbox')
                    options.add_argument('--disable-dev-shm-usage')
                    options.add_argument('--disable-gpu')
                    
                    system_chromedriver = "/usr/local/bin/chromedriver"
                    if os.path.isfile(system_chromedriver):
                        logger.info(f"Using system chromedriver at: {system_chromedriver}")
                        service = ChromeService(system_chromedriver)
                    else:
                        # Fallback to local bin folder
                        driver_path = os.environ.get('CHROMEDRIVER')
                        if not driver_path:
                            candidate_paths = []
                            if platform.system() == 'Windows':
                                candidate_paths.append(os.path.join('bin', 'chromedriver.exe'))
                            candidate_paths.append(os.path.join('bin', 'chromedriver'))
                            for candidate in candidate_paths:
                                if os.path.isfile(candidate):
                                    driver_path = candidate
                                    break
                        
                        if driver_path and os.path.isfile(driver_path):
                            logger.info(f"Using local chromedriver at: {driver_path}")
                            service = ChromeService(driver_path)
                        else:
                            logger.info("No local chromedriver found; attempting webdriver-manager download...")
                            service = ChromeService(ChromeDriverManager().install())
                    
                    self.driver = webdriver.Chrome(service=service, options=options)
            except Exception as e:
                logger.error(f"Failed to initialize Chrome driver: {str(e)}")
                raise Exception(
                    "Failed to initialize Chrome driver. Please check your setup."
                )
            logger.info("Chrome driver initialized successfully")
            
            # Send progress update before login
            self.send_progress_update("Logging into Skyward...", 20)
            self.login()
            
            # Send progress update before gradebook navigation
            self.send_progress_update("Accessing gradebook...", 35)
            self.navigate_to_gradebook()
            
            # Send progress update before grade extraction
            self.send_progress_update("Extracting grades...", 50)
            self.extract_grades()
            
            # Send progress update before GPA calculation
            self.send_progress_update("Analyzing class data...", 65)
            self.calculate_gpas()
            
            # Send final progress update
            self.send_progress_update("Calculating GPAs...", 80)
            
            return {
                'grades_raw': self.grades_raw,
                'grades': self.grades,
                'unweighted_gpas': self.period_gpas,
                'weighted_gpas': self.weighted_period_gpas,
                'ordered_periods': self.ordered_periods
            }
        except Exception as e:
            logger.error(f"Error in calculate: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except Exception as e:
                    logger.error(f"Error closing driver: {str(e)}")

    def login(self):
        try:
            logger.info("Attempting to access login page...")
            self.driver.get("https://skyward-alvinprod.iscorp.com/scripts/wsisa.dll/WService=wsedualvinisdtx/fwemnu01.w")
            
            logger.info("Waiting for username input...")
            username_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '/html/body/form[1]/div/div/div[4]/div[2]/div[1]/div[2]/div/table/tbody/tr[1]/td[2]/input'))
            )
            username_input.send_keys(self.username)
            logger.info("Username entered successfully")

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
        try:
            logger.info("Attempting to switch to new window...")
            

            
            WebDriverWait(self.driver, 20).until(lambda d: len(d.window_handles) > 1)
            self.driver.switch_to.window(self.driver.window_handles[1])
            logger.info("Successfully switched to new window")

            # Wait for the main page to load instead of static sleep
            logger.info("Waiting for main page to load...")
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            

            
            logger.info("Looking for gradebook button...")
            
            # First check if sidebar needs expansion
            try:
                logger.info("Checking if sidebar needs expansion...")
                sidebar_xpath = '/html/body/div[1]/div[2]/div[2]/div[1]/div/ul[1]/li/a'
                sidebar_button = self.driver.find_element(By.XPATH, sidebar_xpath)
                
                if sidebar_button.is_displayed():
                    logger.info("Sidebar expansion button found, clicking...")
                    self.driver.execute_script("arguments[0].click();", sidebar_button)
                    # Wait for sidebar animation to complete
                    WebDriverWait(self.driver, 5).until(
                        lambda d: d.find_element(By.XPATH, '/html/body/div[1]/div[2]/div[2]/div[1]/div/ul[2]').is_displayed()
                    )
            except Exception as e:
                logger.info(f"No sidebar expansion needed or not found: {str(e)}")

            # Now try gradebook button with updated XPath and text fallback
            try:
                logger.info("Attempting to find gradebook button...")
                
                # Try the updated XPath first
                gradebook_xpath = '/html/body/div[1]/div[2]/div[2]/div[1]/div/ul[2]/li[2]/a'
                try:
                    gradebook_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, gradebook_xpath))
                    )
                    logger.info("Found gradebook button using updated XPath")
                except:
                    # Fallback: look for any link with "Gradebook" text
                    logger.info("XPath not found, trying text-based search...")
                    gradebook_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Gradebook')]"))
                    )
                    logger.info("Found gradebook button using text search")
                
                logger.info("Found gradebook button, attempting to click...")
                
                # Try different click methods
                try:
                    self.driver.execute_script("arguments[0].click();", gradebook_button)
                    logger.info("JavaScript click successful")
                except:
                    try:
                        gradebook_button.click()
                        logger.info("Regular click successful")
                    except:
                        ActionChains(self.driver).move_to_element(gradebook_button).click().perform()
                        logger.info("ActionChains click successful")
                

                
            except Exception as e:
                logger.error(f"Failed to click gradebook button: {str(e)}")
                raise

            # Wait for gradebook to load - using exact XPath
            logger.info("Waiting for gradebook to load...")
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, 
                        '/html/body/div[1]/div[2]/div[2]/div[2]/div/div[4]/div[4]/div[2]/div[1]/div/div[1]/div[1]/table/thead/tr/th'
                    ))
                )
                logger.info("Gradebook loaded successfully")
                
            except Exception as e:
                logger.error("Gradebook failed to load")
                raise

        except Exception as e:
            logger.error(f"Error in navigate_to_gradebook: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def extract_grades(self):
        try:
            logger.info("Starting grade extraction...")
            # Extract grading periods
            logger.info("Finding grading periods...")
            grading_periods_xpath = '/html/body/div[1]/div[2]/div[2]/div[2]/div/div[4]/div[4]/div[2]/div[1]/div/div[1]/div[1]/table/thead/tr/th'
            grading_periods = self.driver.find_elements(By.XPATH, grading_periods_xpath)
            logger.info(f"Found {len(grading_periods)} grading periods")
            
            # Store period labels
            period_labels = []
            for period in grading_periods:
                try:
                    label = period.get_attribute('innerText')
                    if label:
                        period_labels.append(label)
                    else:
                        period_labels.append('-')
                except Exception as e:
                    logger.error(f"Error getting period label: {str(e)}")
                    period_labels.append('-')
            
            logger.info(f"Period labels: {period_labels}")

            # Filter periods and maintain the correct order
            self.ordered_periods = [period for period in self.period_order 
                                  if period in period_labels and 'C' not in period]
            logger.info(f"Ordered periods: {self.ordered_periods}")

            # Get classes container
            logger.info("Finding classes container...")
            classes_container_xpath = '/html/body/div[1]/div[2]/div[2]/div[2]/div/div[4]/div[4]/div[2]/div[2]/div[2]/table/tbody'
            classes_container = self.driver.find_element(By.XPATH, classes_container_xpath)
            class_rows = classes_container.find_elements(By.XPATH, './tr')
            logger.info(f"Found {len(class_rows)} class rows")

            # Extract grades for each class
            for class_index, class_row in enumerate(class_rows, 1):
                try:
                    logger.info(f"Processing class {class_index}/{len(class_rows)}")
                    # Get class name
                    class_name_xpath = f'/html/body/div[1]/div[2]/div[2]/div[2]/div/div[4]/div[4]/div[2]/div[2]/div[2]/table/tbody/tr[{class_index}]/td/div/table/tbody/tr[1]/td[2]/span/a'
                    class_name = self.driver.find_element(By.XPATH, class_name_xpath).text
                    logger.info(f"Processing class: {class_name}")
                    
                    # Get grades
                    class_grades = {}
                    is_valid_class = True

                    row_xpath = f'/html/body/div[1]/div[2]/div[2]/div[2]/div/div[4]/div[4]/div[2]/div[1]/div/div[1]/div[2]/table/tbody/tr[{class_index}]'
                    cells = self.driver.find_elements(By.XPATH, f'{row_xpath}/td')
                    logger.info(f"Found {len(cells)} grade cells for {class_name}")

                    for cell_index, cell in enumerate(cells):
                        try:
                            text = cell.get_attribute('innerText')
                            if text and text.replace('.', '').isnumeric():
                                if cell_index < len(period_labels):
                                    class_grades[period_labels[cell_index]] = float(text)
                            elif text:  # If non-numeric grade found
                                is_valid_class = False
                                break
                        except Exception as e:
                            logger.error(f"Error processing grade cell {cell_index} for {class_name}: {str(e)}")
                            continue

                    if is_valid_class and class_grades:
                        logger.info(f"Adding grades for {class_name}: {class_grades}")
                        self.grades_raw[class_name] = class_grades
                        filtered_grades = {period: grade for period, grade in class_grades.items() 
                                        if 'C' not in period}
                        if filtered_grades:
                            self.grades[class_name] = filtered_grades

                except Exception as e:
                    logger.error(f"Error processing class {class_index}: {str(e)}")
                    logger.error(traceback.format_exc())
                    continue
            
            logger.info("Grade extraction completed successfully")
            logger.info(f"Total classes processed: {len(self.grades)}")
            
        except Exception as e:
            logger.error(f"Error in extract_grades: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def calculate_gpas(self):
        # First, count how many valid classes we have total
        total_valid_classes = len(self.grades)
        
        # Calculate unweighted GPAs
        for period in self.ordered_periods:
            total_gpa = 0
            num_classes = 0
            
            # Check if all classes have grades for this period
            classes_with_grades = sum(1 for class_grades in self.grades.values() if period in class_grades)
            
            # Only calculate GPA if all classes have grades
            if classes_with_grades == total_valid_classes:
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
            
            # Check if all classes have grades for this period
            classes_with_grades = sum(1 for class_grades in self.grades.values() if period in class_grades)
            
            # Only calculate GPA if all classes have grades
            if classes_with_grades == total_valid_classes:
                for class_name, class_grades in self.grades.items():
                    if period in class_grades:
                        grade = class_grades[period]
                        
                        # Determine base GPA
                        if "APA" in class_name:
                            base_gpa = 7.0
                        elif "AP" in class_name or "Ind Study Tech Applications" in class_name:
                            base_gpa = 8.0
                        else:
                            base_gpa = 6.0
                        
                        weighted_gpa = base_gpa - (100 - grade) * 0.1
                        total_gpa += weighted_gpa
                        num_classes += 1
                
                if num_classes > 0:
                    self.weighted_period_gpas[period] = total_gpa / num_classes
