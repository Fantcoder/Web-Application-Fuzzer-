import os
import time
import logging
import requests
import uuid
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options
from urllib.parse import urlparse, parse_qs
from selenium.common.exceptions import NoAlertPresentException
import joblib  # Import joblib to load the ML models
import numpy as np  # Import numpy for feature array handling

# Load the ML models
#anomaly_detector = joblib.load("anomaly_model.pkl")
#classifier = joblib.load("classifier_model.pkl")

# Set up general activity logging to fuzz.log
log_file = "fuzz.log"
report_file = "report.log"
dataset_file = "fuzzer_dataset.csv"
# Function to clear existing log files
def clear_logs():
    """Clear the fuzz.log and report.log files."""
    if os.path.exists(log_file):
        open(log_file, 'w').close()  # Clear fuzz.log
    if os.path.exists(report_file):
        open(report_file, 'w').close()  # Clear report.log
    if os.path.exists(dataset_file):
        open(dataset_file, 'w').close()  # Clear dataset file if it exists
# Clear log files at the start
clear_logs()

# Initialize logging for fuzz.log
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(message)s')

class WebFuzzer:
    def __init__(self, target_url, wordlist_file):
        self.target_url = target_url
        self.wordlist_file = wordlist_file
        self.wordlist = []
        self.previous_body = ""
        self.params = {}
        self.selected_params = []
        self.load_wordlist()
        self.driver = None

        self.initialize_dataset()

    def log_activity(self, message):
        """Function to log general activities."""
        logging.info(message)
        print(message)  # Print to console for real-time feedback

    def log_report(self, report_data):
        """Function to log detailed reports to a separate file."""
        with open(report_file, 'a') as report:
            report.write(report_data + "\n")
        self.log_activity("Report written to report.log")

    def load_wordlist(self):
        """Load the wordlist from a file."""
        if not os.path.exists(self.wordlist_file):
            raise ValueError(f"Wordlist file {self.wordlist_file} not found.")

        with open(self.wordlist_file, 'r') as file:
            self.wordlist = [line.strip() for line in file if line.strip()]

        if not self.wordlist:
            raise ValueError("Wordlist is empty or could not be loaded.")
        self.log_activity(f"Loaded {len(self.wordlist)} payloads from wordlist.")

    def initialize_dataset(self):
        """Ensure dataset file has headers with label first."""
        
        # Open file in 'w' mode to overwrite only if it is newly created
        with open(dataset_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            # Writing the header (column names) first
            writer.writerow([
                'label', 'payload', 'response_code', 'alert_detected', 
                'error_detected', 'body_word_count_changed', 'timestamp'
            ])
            
        self.log_activity(f"Dataset file initialized with headers: {dataset_file}")

    def save_to_dataset(self, payload, response_code, alert_detected, error_detected, body_word_count_changed):
        """Save labeled data in CSV, ensuring the label is first and properly formatted."""

        # Assign label based on conditions
        if response_code >= 500 or error_detected:
            label = "malicious"
        elif alert_detected:
            label = "suspicious"
        else:
            label = "safe"

        # Append data to the dataset in the correct format
        with open(dataset_file, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                label,  # Label first
                payload,
                response_code,
                alert_detected,
                error_detected,
                body_word_count_changed,
                time.time()  # Timestamp
            ])

        self.log_activity(f"Data saved: {label}, {payload}, {response_code}, {alert_detected}, {error_detected}, {body_word_count_changed}")

    def start_browser(self, headless=True):
        """Start the Selenium browser and open the target URL."""
        firefox_options = Options()
        firefox_options.headless = headless
        firefox_options.binary_location = r"C:\Program Files\Mozilla Firefox\firefox.exe"
        service = FirefoxService(executable_path=r"C:\geckodriver\geckodriver.exe")

        self.driver = webdriver.Firefox(service=service, options=firefox_options)
     

        self.log_activity(f"Opened browser and navigating to {self.target_url}.")
        self.driver.get(self.target_url)

    def login_to_dvwa(self):
        """Log in to DVWA with default credentials."""
        self.log_activity("Attempting to log in to DVWA.")
        self.driver.get(f"{self.target_url}/login.php")
        time.sleep(3)  # Wait for the page to load

        username_field = self.driver.find_element(By.NAME, 'username')
        password_field = self.driver.find_element(By.NAME, 'password')

        # Input credentials
        username_field.send_keys('admin')
        password_field.send_keys('password')
        self.log_activity("Entered login credentials: admin/password")

        # Click login button
        login_button = self.driver.find_element(By.NAME, 'Login')
        login_button.click()

        time.sleep(3)  # Wait for the page to redirect after login

        # Check if login was successful
        if "index.php" in self.driver.current_url:
            self.log_activity("Successfully logged into DVWA.")
        else:
            self.log_activity("Login failed.")
            self.driver.quit()
            exit()

    def detect_unexpected_alerts(self):
        """Check for any dialog boxes or alerts and log them."""
        try:
            alert = self.driver.switch_to.alert
            alert_text = alert.text
            self.log_activity(f"Alert detected: {alert_text}")
            self.log_report(f"Alert detected: {alert_text}")
            alert.accept()  # Close the alert
            return alert_text
        except NoAlertPresentException:
            return None  # No alert detected

    def detect_unexpected_errors(self):
        """Check for unexpected errors in the response."""
        body = self.driver.page_source
        if "error" in body.lower():  # Adjust according to how errors are displayed
            self.log_activity("Unexpected error detected in the page.")
            self.log_report("Unexpected error detected in the page.")
            return True
        return False

    def get_word_count(self, text):
        """Return the number of words in the provided text."""
        return len(text.split())

    def detect_changes_in_body(self):
        """Detect unexpected changes in the page body."""
        current_body = self.driver.page_source
        word_count_change = False

        if self.previous_body:
            previous_word_count = self.get_word_count(self.previous_body)
            current_word_count = self.get_word_count(current_body)

            if previous_word_count != current_word_count:
                self.log_activity(f"Word count changed from {previous_word_count} to {current_word_count}.")
                report_data = (
                    f"Word count changed: {previous_word_count} -> {current_word_count}\n"
                )
                self.log_report(report_data)
                word_count_change = True

        self.previous_body = current_body
        return word_count_change

    def get_response_code(self):
        """Capture the HTTP response code by sending a request."""
        try:
            response = requests.get(self.driver.current_url)
            return response.status_code
        except requests.RequestException as e:
            self.log_activity(f"Error fetching response code: {e}")
            return "N/A"

    def fuzz_form_fields(self):
        """Fuzz the form fields on the current page with all payloads."""
        for payload in self.wordlist:
            unique_id = str(uuid.uuid4())  # Unique ID for this payload attempt
            payload_report = []  # Collect details for this payload
            try:
                # Get all forms on the current page dynamically
                self.log_activity("Searching for forms on the current page for fuzzing.")
                forms = self.driver.find_elements(By.TAG_NAME, 'form')

                if forms:
                    for form in forms:
                        input_fields = form.find_elements(By.TAG_NAME, 'input')

                        for field in input_fields:
                            if field.get_attribute("type") in ["text", "search"]:
                                field.clear()  # Clear any existing text
                                field.send_keys(payload)  # Inject the payload
                                self.log_activity(f"[{unique_id}] Injected payload: {payload}")

                        form.submit()  # Submit the form
                        self.log_activity(f"[{unique_id}] Form submitted with payload: {payload}")

                        # Allow some time for the page to reload after form submission
                        time.sleep(2)

                        # Check for alerts after form submission
                        alert_text = self.detect_unexpected_alerts()
                        alert_detected = bool(alert_text)

                        # Detect unexpected changes in the page body
                        body_changed = self.detect_changes_in_body()

                        # Check for unexpected errors
                        error_detected = self.detect_unexpected_errors()

                        # Capture the response code
                        response_code = self.get_response_code()

                        # Save data to dataset
                        self.save_to_dataset(payload, response_code, alert_detected, error_detected, body_changed)

                        # Prepare report data
                        payload_report.append(f"Unique ID: {unique_id}")
                        payload_report.append(f"Payload: {payload}")
                        payload_report.append(f"Response Code: {response_code}")
                        payload_report.append(f"Alert Detected: {alert_text if alert_text else 'None'}")
                        payload_report.append(f"Unexpected Error Detected: {'Yes' if error_detected else 'No'}")
                        payload_report.append(f"Body Word Count Changed: {'Yes' if body_changed else 'No'}")
                        payload_report.append("-" * 50)  # Separator for readability

                        # Log the report for this payload
                        self.log_report("\n".join(payload_report))
                else:
                    self.log_activity("No forms found on the current page for fuzzing.")
            except Exception as e:
                self.log_activity(f"[{unique_id}] Error during fuzzing: {e}")


    def extract_params_from_url(self, url):
        """Extract query parameters from the given URL."""
        parsed_url = urlparse(url)
        return parse_qs(parsed_url.query)

    def select_exploit_parameters(self):
        """Select parameters that contain the keyword 'exploit'."""
        self.selected_params = {key: value for key, value in self.params.items() if 'exploit' in key or any('exploit' in v for v in value)}
        return bool(self.selected_params)

    def get_page_url(self):
        """Return the current URL of the page."""
        return self.driver.current_url

    def monitor_for_exploit(self):
        """Monitor input fields for the 'exploit' keyword across any webpage."""
        self.log_activity("Monitoring input fields for 'exploit' keyword.")
        
        while True:
            try:
                # Get all forms on the current page
                forms = self.driver.find_elements(By.TAG_NAME, 'form')
                for form in forms:
                    input_fields = form.find_elements(By.TAG_NAME, 'input')
                    
                    for field in input_fields:
                        # Monitor text or search type input fields
                        if field.get_attribute("type") in ["text", "search"]:
                            value = field.get_attribute("value").lower()
                            if "exploit" in value:
                                self.log_activity(f"Detected 'exploit' keyword in form field: {value}")
                                self.fuzz_form_fields()  # Trigger fuzzing
                                return  # Exit the monitoring loop after triggering fuzzing
                            
                time.sleep(2)  # Avoid overloading the browser with continuous checks
            except Exception as e:
                self.log_activity(f"Error during monitoring: {e}")
                break

    
    def calculate_accuracy(self):
        """Calculate and print accuracy metrics."""
        if self.true_labels:
            print("Accuracy:", accuracy_score(self.true_labels, self.predicted_labels))
            print("Precision:", precision_score(self.true_labels, self.predicted_labels))
            print("Recall:", recall_score(self.true_labels, self.predicted_labels))
            print("F1 Score:", f1_score(self.true_labels, self.predicted_labels))
        else:
            print("No true labels collected for accuracy evaluation.")

    def start_fuzzing(self):
        """Start the fuzzing process."""
        self.start_browser()
        self.login_to_dvwa()
        self.monitor_for_exploit()  # Monitor URL for 'exploit' keyword and trigger fuzzing
        self.log_activity("Fuzzing process completed.")
        

if __name__ == "__main__":
    # Set the DVWA URL and path to the wordlist file
    target_url ="http://localhost:8080"#("Enter the target URL (e.g., http://localhost/dvwa): ")
    wordlist_file = "c:/Users/Siddhant/OneDrive/Desktop/web ap/xss.txt"


    
    # Create the fuzzer object and start fuzzing
    fuzzer = WebFuzzer(target_url, wordlist_file)
    fuzzer.start_fuzzing()
    # fuzzer.calculate_accuracy()
