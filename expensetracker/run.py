# Import necessary libraries
import logging
import gspread
from google.oauth2.service_account import Credentials

# Define the scope for Google Sheets API access
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

# Load Google Sheets credentials from the JSON file
CREDS = Credentials.from_service_account_file('creds.json') 
SCOPED_CREDS= CREDS.with_scopes(SCOPE)
GSPREAD_CLIENT = gspread.authorize(SCOPED_CREDS)
SHEET = GSPREAD_CLIENT.open_by_url('https://docs.google.com/spreadsheets/d/1TR5G47Vod-z4LYL8L5ptrYjAFKCOhmeneQodZjO19qE')

# Define a worksheet for logging data (create if it doesn't exist)
expenses = SHEET.worksheet('expenses')

# Define the Expense class
class Expense:
    def __init__(self, name, amount, category):
        self.name = name
        self.amount = amount
        self.category = category

    def __str__(self):
        return f"{self.name} - {self.category} - €{self.amount:.2f}"

# Create a class named ExpenseTracker to manage expenses and interactions
class ExpenseTracker:
    def __init__(self, spreadsheet):
        self.expense_sheet = spreadsheet.worksheet('expenses')
        self.categories_sheet = spreadsheet.worksheet('categories')
        self.expenses = []
        self.expense_categories = self.load_categories()  # Initialize categories from Google Sheets
        self.user_budget = self.get_user_budget() 
        self.setup_logger()  # Call the setup_logger method to initialize the logger

    def setup_logger(self):
        """
        Set up and configure a logger for logging application events.
        """
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler = logging.FileHandler('expense_tracker.log')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def set_user_budget(self, budget):
        """
        Set the user's monthly budget.

        :param budget: Monthly budget amount.
        """
        self.user_budget = budget

    def get_user_budget(self):
        """
        Prompt the user to input monthly budget and return it.

        :return: Monthly budget amount.
        """
        try:
            budget = float(input("Enter your monthly budget: "))
            return budget
        except ValueError:
            print("Invalid input. Please enter a valid number.")
            return self.get_user_budget()

    def colorize(self, text, color):
        """
        Apply color to the text for console output.

        :param text: Text to be colored.
        :param color: Color name (e.g., 'red', 'green', 'white').
        :return: Colored text.
        """
        colors = {
            "red": "\033[91m",
            "green": "\033[92m",
            "white": "\033[0m",
        }
        return f"{colors[color]}{text}{colors['white']}"
    
    def load_data(self, sheet, column):
        """
        Load data from a specific column in a Google Sheets worksheet.

        Args:
            sheet (gspread.Worksheet): The Google Sheets worksheet.
            column (str): The name of the column to load data from.

        Returns:
            list: A list containing loaded data from the specified column.
        """
        try:
            column_obj = sheet.find(column)
            if column_obj:
                data = sheet.col_values(column_obj.col)
                data.pop(0)  # Remove the header
                return data
            else:
                return []  # Column not found
        except Exception as e:
            self.logger.error(f"Error loading data from Google Sheets: {e}")
            return []

