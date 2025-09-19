from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.action_chains import ActionChains
import platform
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
    
    def take_debug_screenshot(self, step_name):
        """Take a screenshot for debugging purposes"""
        try:
            screenshot_path = f"/tmp/debug_{step_name}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"Debug screenshot saved: {screenshot_path}")
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")

    def calculate(self):
        try:
            logger.info("Initializing Chrome driver...")
            # Send initial progress update
            self.send_progress_update("Connecting to Skyward...", 5)
            
            try:
                # Set up Chrome options
                options = webdriver.ChromeOptions()
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                options.add_argument('--disable-extensions')
                options.add_argument('--disable-infobars')
                options.add_argument('--disable-notifications')
                options.add_argument('--disable-popup-blocking')
                options.add_argument('--ignore-certificate-errors')
                options.add_argument('--window-size=1920,1080')
                
                # Only run headless on production (Render) or when explicitly set
                # Set HEADLESS=false to debug visually
                if os.environ.get('HEADLESS', 'true').lower() == 'true':
                    options.add_argument('--headless=new')
                else:
                    logger.info("Running in NON-HEADLESS mode for debugging")
                
                # Use system chromedriver (installed by Dockerfile)
                system_chromedriver = "/usr/local/bin/chromedriver"
                logger.info(f"Using system chromedriver at: {system_chromedriver}")
                service = ChromeService(system_chromedriver)
                # Set Chrome binary location
                options.binary_location = '/usr/bin/google-chrome'
                
                self.driver = webdriver.Chrome(service=service, options=options)
            except Exception as e:
                logger.error(f"Failed to initialize Chrome driver: {str(e)}")
                logger.error(f"Chrome driver traceback: {traceback.format_exc()}")
                raise Exception(
                    f"Failed to initialize Chrome driver: {str(e)}"
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
            self.send_progress_update("Connecting to Skyward...", 10)
            self.driver.get("https://skyward-alvinprod.iscorp.com/scripts/wsisa.dll/WService=wsedualvinisdtx/fwemnu01.w")
            
            # Take screenshot of initial login page
            self.take_debug_screenshot("01_initial_login_page")
            
            # First, click the link to open the username/password fields
            logger.info("Clicking to open username/password fields...")
            self.send_progress_update("Opening login form...", 15)
            
            # Try the original XPath first
            try:
                login_link = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '/html/body/form[1]/div/div/div[4]/div[2]/div[1]/div[2]/div/table/tbody/tr[7]/td/a'))
                )
                logger.info("Found login link with original XPath")
            except:
                # If original XPath fails, try alternative approaches
                logger.info("Original XPath failed, trying alternatives...")
                self.take_debug_screenshot("02_login_page_failed_xpath")
                
                # Try to find any clickable link that might open login form
                try:
                    # Look for common login button text patterns
                    login_link = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Login') or contains(text(), 'Sign In') or contains(text(), 'Enter')]"))
                    )
                    logger.info("Found login link with text-based search")
                except:
                    # Try to find any link in the form
                    try:
                        login_link = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, "//form//a"))
                        )
                        logger.info("Found login link with form-based search")
                    except:
                        raise Exception("Could not find login link - Skyward may have changed their login page layout")
            login_link.click()
            
            # Take screenshot after clicking login link
            self.take_debug_screenshot("03_after_login_click")
            
            logger.info("Waiting for username input...")
            self.send_progress_update("Logging in...", 20)
            username_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '/html/body/form[1]/div/div/div[4]/div[2]/div[1]/div[2]/div/table/tbody/tr[1]/td[2]/input'))
            )
            
            # Click, clear, and enter username
            username_input.click()
            username_input.clear()
            username_input.send_keys(self.username)
            logger.info(f"Username entered successfully: '{self.username}'")

            # Enter password
            password_input = self.driver.find_element(By.XPATH, '/html/body/form[1]/div/div/div[4]/div[2]/div[1]/div[2]/div/table/tbody/tr[2]/td[2]/input')
            
            # Click, clear, and enter password
            password_input.click()
            password_input.clear()
            password_input.send_keys(self.password)
            logger.info("Password entered successfully")
            
            # Take screenshot after filling credentials
            self.take_debug_screenshot("04_credentials_filled")

            # Wait for loading overlay to disappear before clicking sign-in button
            logger.info("Waiting for loading overlay to disappear...")
            try:
                WebDriverWait(self.driver, 10).until(
                    lambda d: not d.find_element(By.ID, "lockDiv").is_displayed()
                )
                logger.info("Loading overlay disappeared")
            except:
                logger.info("Loading overlay not found or already gone")

            # Click sign-in button
            sign_in_button = self.driver.find_element(By.XPATH, '/html/body/form[1]/div/div/div[4]/div[2]/div[1]/div[2]/div/table/tbody/tr[7]/td/a')
            sign_in_button.click()

            # Wait for either new window to appear OR page to load in same tab
            logger.info("Waiting for login to complete...")
            try:
                # First, wait a bit for the page to process
                WebDriverWait(self.driver, 5).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                
                # Check if a new window opened (old Skyward behavior)
                if len(self.driver.window_handles) > 1:
                    logger.info("New window detected - switching to it")
                    self.driver.switch_to.window(self.driver.window_handles[1])
                else:
                    logger.info("No new window - staying in same tab")
                    # Wait for the main page to load in the same tab
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    
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
            logger.error(f"Login error: {str(e)}")
            logger.error(f"Login traceback: {traceback.format_exc()}")
            if "Incorrect username or password" in str(e) or "Login failed" in str(e):
                raise e
            raise Exception(f"Login failed: {str(e)}")

    def navigate_to_gradebook(self):
        try:
            # Check if we need to switch windows or if we're already in the main window
            if len(self.driver.window_handles) > 1:
                logger.info("Switching to main window...")
                self.send_progress_update("Switching to main window...", 25)
                WebDriverWait(self.driver, 20).until(lambda d: len(d.window_handles) > 1)
                self.driver.switch_to.window(self.driver.window_handles[1])
                logger.info("Successfully switched to new window")
            else:
                logger.info("Already in main window - no switching needed")

            # Wait for the main page to load
            logger.info("Waiting for main page to load...")
            self.send_progress_update("Loading main page...", 30)
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            logger.info("Looking for gradebook button...")
            self.send_progress_update("Navigating to gradebook...", 35)
            
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
            self.send_progress_update("Fetching gradebook...", 40)
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
                    # Update progress during grade extraction
                    progress = 40 + int((class_index / len(class_rows)) * 10)  # 40-50%
                    self.send_progress_update(f"Getting grades ({class_index}/{len(class_rows)})...", progress)
                    
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
                        if "APA" in class_name or "Academic Dec 1" in class_name:
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
