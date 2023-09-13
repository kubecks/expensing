# Import necessary libraries
import logging
import gspread
from google.oauth2.service_account import Credentials


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

# Now you can work with the worksheet
data = expenses.get_all_values()
print(data)

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
        return float(input("Enter your monthly budget: "))

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

    def save_data(self, sheet, data, column):
        """
        Save data to a specific column in a Google Sheets worksheet.

        Args:
            sheet (gspread.Worksheet): The Google Sheets worksheet.
            data (list): The data to be saved.
            column (str): The name of the column to save data to.
        """
        try:
            # Clear the existing data in the column
            sheet.update(value=[[]], range_name=column)  # Clear the range
            # Append the header
            data.insert(0, [column])
            # Update the column with the new data
            sheet.update(value=data, range_name=column)
        except Exception as e:
            self.logger.error(f"Error saving data to Google Sheets: {e}")

            
    def summarize_expenses(self):
        """
        Summarize expenses and display the total and category-wise totals.
        """
        category_totals = {}
        total_expenses = 0

        for expense in self.expenses:
            total_expenses += expense.amount
            category_totals[expense.category] = category_totals.get(expense.category, 0) + expense.amount

        budget = self.get_user_budget()

        if total_expenses < budget:
            total_expenses_formatted = self.colorize(f'€{total_expenses:.2f}', 'green')
        elif total_expenses > budget:
            total_expenses_formatted = self.colorize(f'€{total_expenses:.2f}', 'red')
        else:
            total_expenses_formatted = self.colorize(f'€{total_expenses:.2f}', 'white')

        print(f"Total Expenses: {total_expenses_formatted}")
        print("Category-wise Expenses:")
        for category, amount in category_totals.items():
            formatted_amount = self.colorize(f'€{amount:.2f}', 'green')
            print(f"{category}: {formatted_amount}")

    def load_expenses(self):
        """
        Load expenses from the Google Sheets "Expenses" worksheet.

        Returns:
            list: A list of Expense objects representing expenses.
        """
        try:
            expense_data = self.load_data(self.expense_sheet, "Expense Name")
            amount_data = self.load_data(self.expense_sheet, "Amount")
            category_data = self.load_data(self.expense_sheet, "Category")

            expenses = []

            for name, amount, category in zip(expense_data, amount_data, category_data):
                expenses.append(Expense(name, float(amount), category))

            return expenses
        except Exception as e:
            self.logger.error(f"Error loading expenses from Google Sheets: {e}")
            return []

    def save_expenses(self):
        """
        Save expenses to the Google Sheets "Expenses" worksheet.
        """
        try:
            expense_names = ["Expense Name"] + [expense.name for expense in self.expenses]
            expense_amounts = ["Amount"] + [str(expense.amount) for expense in self.expenses]
            expense_categories = ["Category"] + [expense.category for expense in self.expenses]

            data_to_save = [expense_names, expense_amounts, expense_categories]

            self.expense_sheet.clear()
            self.expense_sheet.update(data_to_save)
        except Exception as e:
            self.logger.error(f"Error saving expenses to Google Sheets: {e}")
    
    def load_categories(self):
        """
        Load categories from the Google Sheets "Categories" worksheet.

        Returns:
            list: A list of category names.
        """
        try:
            categories = self.load_data(self.categories_sheet, "Category")
            print("Loaded categories:", categories)  # Add this line for debugging
            return categories
        except Exception as e:
            self.logger.error(f"Error loading categories from Google Sheets: {e}")
            return []

    def edit_item(self, items, item_type):
        """
        Edit an item from the list of items.

        Args:
            items (list): The list of items to edit.
            item_type (str): The type of item being edited.
        """
        try:
            self.display_items(items, item_type)
            item_index = int(input(f"Enter the index of the {item_type.lower()} to edit: ")) - 1
            if item_index in range(len(items)):
                new_value = input(f"Enter the new value for '{items[item_index]}': ")
                items[item_index] = new_value
                self.save_data(items, self.categories_file_path)
                print(f"{item_type} updated successfully.")
            else:
                print("Invalid index.")
        except Exception as e:
            self.logger.error(f"Error editing item: {e}")

    def delete_item(self, items, item_type):
        """
        Delete an item from the list of items.

        Args:
            items (list): The list of items to delete from.
            item_type (str): The type of item being deleted.
        """
        try:
            self.display_items(items, item_type)
            item_index = int(input(f"Enter the index of the {item_type.lower()} to delete: ")) - 1
            if item_index in range(len(items)):
                deleted_item = items.pop(item_index)
                self.save_data(items, self.categories_file_path)
                print(f"{item_type} '{deleted_item}' deleted successfully.")
            else:
                print("Invalid index.")
        except Exception as e:
            self.logger.error(f"Error deleting item: {e}")

    def display_items(self, items, item_type):
        """
        Display the list of items.

        Args:
            items (list): The list of items to display.
            item_type (str): The type of items being displayed.
        """
        print(f"{item_type} List:")
        for index, item in enumerate(items, start=1):
            print(f"{index}. {item}")

    def manage_items(self, items, item_type):
        """
        Manage items in the list.

        Args:
            items (list): The list of items to manage.
            item_type (str): The type of items being managed.
        """
        while True:
            print(f"{item_type} Management")
            print("1. Display Items")
            print("2. Add Item")
            print("3. Edit Item")
            print("4. Delete Item")
            print("5. Exit")
            choice = input("Select an option: ")

            if choice == "1":
                self.display_items(items, item_type)
            elif choice == "2":
                new_item = input(f"Enter the new {item_type.lower()}: ")
                if new_item not in items:
                    items.append(new_item)
                    self.save_data(self.categories_sheet, items, "Category")
                    print(f"{item_type} '{new_item}' added successfully.")
                else:
                    print(f"{item_type} already exists.")
            elif choice == "3":
                self.edit_item(items, item_type)
            elif choice == "4":
                self.delete_item(items, item_type)
            elif choice == "5":
                break
            else:
                print("Invalid choice. Please try again.")

    def get_user_expense(self):
        """
        Get an expense input from the user.

        Returns:
            Expense: The expense object.
        """
        print(f"🎯 Getting User Expense")
        expense_name = input("Enter expense name: ")
        expense_amount = float(input("Enter expense amount: "))

        while True:
            print("Select a category: ")
            for i, category_name in enumerate(self.expense_categories, start=1):
                print(f"  {i}. {category_name}")

            value_range = f"[1 - {len(self.expense_categories)}]"
            selected_index = int(input(f"Enter a category number {value_range}: ")) - 1

            if selected_index in range(len(self.expense_categories)):
                selected_category = self.expense_categories[selected_index]
                new_expense = Expense(
                    name=expense_name, category=selected_category, amount=expense_amount
                )
                return new_expense
            else:
                print("Invalid category. Please try again!")

    def display_expenses(self):
        """
        Display the list of expenses.
        """
        print("expenses:")
        for expense in self.expenses:
            print(expense)

    def edit_or_remove_expense(self):
        """
    Edit or remove an existing expense from the list of expenses.

    Args:
        expenses (list): The list of Expense objects representing expenses.
        """

        self.display_expenses()
        expense_index = int(input("Enter the index of the expense to edit/remove: ")) - 1

        if expense_index in range(len(self.expenses)):
            selected_expense = self.expenses[expense_index]

            print(f"Selected Expense: {selected_expense}")
            print("1. Edit Expense")
            print("2. Remove Expense")
            edit_or_remove_choice = input("Select an option (1 or 2): ")

            if edit_or_remove_choice == "1":
                # Edit Expense
                updated_name = input("Enter the updated expense name (or press Enter to keep the current name): ")
                updated_amount = input("Enter the updated expense amount (or press Enter to keep the current amount): ")
                updated_category = input("Enter the updated expense category (or press Enter to keep the current category): ")

                if updated_name:
                    selected_expense.name = updated_name
                if updated_amount:
                    selected_expense.amount = float(updated_amount)
                if updated_category:
                    selected_expense.category = updated_category

                self.save_expenses()
                print("Expense updated successfully.")
            elif edit_or_remove_choice == "2":
                # Remove Expense
                removed_expense = self.expenses.pop(expense_index)
                self.save_expenses()
                print(f"Expense '{removed_expense}' removed successfully.")
            else:
                print("Invalid option.")
        else:
            print("Invalid expense index.")

    def run(self):
        """
        Start the Expense Tracker application.
        """
        self.load_expenses()

        while True:
            print("Expense Tracker Menu")
            print("1. Add Expense")
            print("2. Display Expenses")
            print("3. Edit/Remove Expense")
            print("4. Adjust Monthly Budget")
            print("5. Manage Categories")
            print("6. Summarize Expenses")
            print("7. Exit")

            choice = input("Select an option: ")

            if choice == "1":
                expense = self.get_user_expense()
                self.expenses.append(expense)
                self.save_expenses()
                print("Expense added successfully.")
            elif choice == "2":
                self.display_expenses()
            elif choice == "3":
                self.edit_or_remove_expense()
            elif choice == "4":
                new_budget = self.get_user_budget()
                self.set_user_budget(new_budget)
                print(f"Monthly budget adjusted to €{new_budget:.2f}")
            elif choice == "5":
                self.manage_items(self.expense_categories, "Category")
            elif choice == "6":
                self.summarize_expenses()
            elif choice == "7":
                break
            else:
                print("Invalid choice. Please try again.")

    
    # Main function to initiate the application
    def main(self):
        print(f"🎯 Running Expense Tracker!")
        logging.basicConfig(level=logging.INFO)

        while True:
            print("Expense Tracker Menu")
            print("1. Add Expense")
            print("2. Display Expenses")
            print("3. Edit/Remove Expense")
            print("4. Adjust Monthly Budget")
            print("5. Manage Categories")
            print("6. Summarize Expenses")
            print("7. Exit")

            choice = input("Select an option: ")

            if choice == "1":
                expense = self.get_user_expense()
                self.expenses.append(expense)
                self.save_expenses()
                print("Expense added successfully.")
            elif choice == "2":
                self.display_expenses()
            elif choice == "3":
                self.edit_or_remove_expense()
            elif choice == "4":
                new_budget = self.get_user_budget()
                self.set_user_budget(new_budget)
                print(f"Monthly budget adjusted to €{new_budget:.2f}")
            elif choice == "5":
                self.manage_items(self.expense_categories, "Category")
            elif choice == "6":
                self.summarize_expenses()
            elif choice == "7":
                break
            else:
                print("Invalid choice. Please try again.")

# Create an instance of ExpenseTracker and run the application

if __name__ == "__main__":
    expense_tracker = ExpenseTracker(SHEET)  # Pass the SHEET object directly
    expense_tracker.main()

