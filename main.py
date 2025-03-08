from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

# Set up the web driver (make sure to specify the path to your ChromeDriver)
driver = webdriver.Chrome()

# Dictionaries to store grade data
grades_raw = {}  # All numeric grades
grades = {}      # Filtered grades (no 'C' in period names)

try:
    # Step 1: Access the login page
    driver.get("https://skyward-alvinprod.iscorp.com/scripts/wsisa.dll/WService=wsedualvinisdtx/fwemnu01.w")

    # Step 2: Enter username
    username_input = driver.find_element(By.XPATH, '/html/body/form[1]/div/div/div[4]/div[2]/div[1]/div[2]/div/table/tbody/tr[1]/td[2]/input')
    username_input.send_keys("301803")

    # Step 3: Enter password
    password_input = driver.find_element(By.XPATH, '/html/body/form[1]/div/div/div[4]/div[2]/div[1]/div[2]/div/table/tbody/tr[2]/td[2]/input')
    password_input.send_keys("Aditi1612!")

    # Step 4: Click the sign-in button
    sign_in_button = driver.find_element(By.XPATH, '/html/body/form[1]/div/div/div[4]/div[2]/div[1]/div[2]/div/table/tbody/tr[7]/td/a')
    sign_in_button.click()

    # Wait for the new page to load
    time.sleep(5)  # Adjust the sleep time as necessary

    # Step 5: Switch to the new window
    driver.switch_to.window(driver.window_handles[1])  # Switch to the new window

    # Step 6: Navigate to the gradebook
    gradebook_button = driver.find_element(By.XPATH, '/html/body/div[1]/div[2]/div[2]/div[1]/div/ul[2]/li[3]/a')
    gradebook_button.click()

    # Wait for the gradebook page to load
    time.sleep(5)  # Adjust the sleep time as necessary

    # Step 7: Extract grading periods from the header row
    grading_periods_xpath = '/html/body/div[1]/div[2]/div[2]/div[2]/div/div[4]/div[4]/div[2]/div[1]/div/div[1]/div[1]/table/thead/tr/th'
    grading_periods = driver.find_elements(By.XPATH, grading_periods_xpath)
    
    # Store the grading period labels
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

    # Print grading period labels for reference
    print("Grading Periods:", ' | '.join(period_labels))
    print("---------------------")

    # Step 8: Get the container for all classes
    classes_container_xpath = '/html/body/div[1]/div[2]/div[2]/div[2]/div/div[4]/div[4]/div[2]/div[2]/div[2]/table/tbody'
    classes_container = driver.find_element(By.XPATH, classes_container_xpath)

    # Find all class rows
    class_rows = classes_container.find_elements(By.XPATH, './tr')

    # Step 9: Iterate through each class
    for class_index, class_row in enumerate(class_rows, 1):  # Start enumeration from 1
        try:
            # Extract class name using the provided XPath structure
            class_name_xpath = f'/html/body/div[1]/div[2]/div[2]/div[2]/div/div[4]/div[4]/div[2]/div[2]/div[2]/table/tbody/tr[{class_index}]/td/div/table/tbody/tr[1]/td[2]/span/a'
            class_name = driver.find_element(By.XPATH, class_name_xpath).text
            
            # Dictionary to store grades for this class
            class_grades = {}
            is_valid_class = True

            # Construct the XPath for the specific row of grades
            row_xpath = f'/html/body/div[1]/div[2]/div[2]/div[2]/div/div[4]/div[4]/div[2]/div[1]/div/div[1]/div[2]/table/tbody/tr[{class_index}]'
            cells = driver.find_elements(By.XPATH, f'{row_xpath}/td')

            # Extract and store every grade in the row
            for cell_index, cell in enumerate(cells):
                try:
                    text = cell.get_attribute('innerText')
                    if text:
                        # Check if the grade is numeric
                        if text.replace('.', '').isnumeric():  # Allow decimal points in numbers
                            if cell_index < len(period_labels):
                                class_grades[period_labels[cell_index]] = float(text)
                        else:
                            # If we find a non-numeric grade, mark the class as invalid
                            is_valid_class = False
                            break
                except Exception as e:
                    continue

            # Only print and store data if it's a valid class
            if is_valid_class and class_grades:  # Make sure we have some grades
                print(f"Class name: {class_name}")
                grades_raw[class_name] = class_grades
                
                # Create filtered grades dictionary (excluding periods with 'C')
                filtered_grades = {period: grade for period, grade in class_grades.items() 
                                if 'C' not in period}
                
                if filtered_grades:  # Only add to grades if there are grades after filtering
                    grades[class_name] = filtered_grades
                
                # Print the grades
                for period, grade in class_grades.items():
                    print(f"{period}: {grade}", end=' | ')
                print()  # New line after each class row
                print("---------------------")
            else:
                print(f"Not a real class: {class_name}")
                print("---------------------")

        except Exception as e:
            continue  # Skip if there's an error processing this class

    # Print the final stored data structures
    print("\nRaw Grades Data (including periods with 'C'):")
    for class_name, grades_dict in grades_raw.items():
        print(f"\n{class_name}:")
        for period, grade in grades_dict.items():
            print(f"  {period}: {grade}")

    print("\nFiltered Grades Data (excluding periods with 'C'):")
    for class_name, grades_dict in grades.items():
        print(f"\n{class_name}:")
        for period, grade in grades_dict.items():
            print(f"  {period}: {grade}")

    # Calculate unweighted GPA for each grading period
    print("\nUnweighted GPA Calculations:")
    
    # Use period_labels instead of collecting from grades to maintain order
    # Filter out periods with 'C' in them to match our filtered grades
    ordered_periods = [period for period in period_labels if 'C' not in period]
    
    # Calculate GPA for each period
    period_gpas = {}
    for period in ordered_periods:
        total_gpa = 0
        num_classes = 0
        
        print(f"\nGrading Period: {period}")
        print("------------------------")
        
        for class_name, class_grades in grades.items():
            if period in class_grades:
                grade = class_grades[period]
                # Calculate GPA: Start with 6.0 and subtract 0.1 for each point below 100
                gpa = 6.0 - (100 - grade) * 0.1
                total_gpa += gpa
                num_classes += 1
                print(f"{class_name}: Grade = {grade}, GPA = {gpa:.2f}")
        
        if num_classes > 0:
            period_gpa = total_gpa / num_classes
            period_gpas[period] = period_gpa
            print(f"\nPeriod {period} Average GPA: {period_gpa:.2f}")
        else:
            print(f"\nNo grades available for period {period}")

    print("\nSummary of Unweighted GPAs by Grading Period:")
    print("----------------------------------------")
    for period in ordered_periods:
        if period in period_gpas:
            print(f"Period {period}: {period_gpas[period]:.2f}")

    # Calculate weighted GPA for each grading period
    print("\nWeighted GPA Calculations:")
    
    # Calculate GPA for each period
    weighted_period_gpas = {}
    for period in ordered_periods:
        total_gpa = 0
        num_classes = 0
        
        print(f"\nGrading Period: {period}")
        print("------------------------")
        
        for class_name, class_grades in grades.items():
            if period in class_grades:
                grade = class_grades[period]
                
                # Determine the base GPA scale based on class name
                if "APA" in class_name:  # Must check APA first since it contains "AP"
                    base_gpa = 7.0
                    class_type = "APA"
                elif "AP" in class_name:
                    base_gpa = 8.0
                    class_type = "AP"
                else:
                    base_gpa = 6.0
                    class_type = "Regular"
                
                # Calculate GPA: Start with base_gpa and subtract 0.1 for each point below 100
                weighted_gpa = base_gpa - (100 - grade) * 0.1
                total_gpa += weighted_gpa
                num_classes += 1
                print(f"{class_name} ({class_type}): Grade = {grade}, Weighted GPA = {weighted_gpa:.2f}")
        
        if num_classes > 0:
            period_gpa = total_gpa / num_classes
            weighted_period_gpas[period] = period_gpa
            print(f"\nPeriod {period} Average Weighted GPA: {period_gpa:.2f}")
        else:
            print(f"\nNo grades available for period {period}")

    print("\nComparison of Unweighted vs Weighted GPAs by Grading Period:")
    print("--------------------------------------------------------")
    for period in ordered_periods:
        if period in period_gpas and period in weighted_period_gpas:
            print(f"Period {period}:")
            print(f"  Unweighted: {period_gpas[period]:.2f}")
            print(f"  Weighted:   {weighted_period_gpas[period]:.2f}")
            print("  Difference: {:.2f}".format(weighted_period_gpas[period] - period_gpas[period]))
            print("--------------------------------------------------------")

finally:
    # Close the driver
    driver.quit()
