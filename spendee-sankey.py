#!/usr/bin/env python3

# http://sankeymatic.com/build/

import pandas

# Regroup several Spendee categories to more general categories.
# Spendee categories become subcategories here.
# Don't use category names that conflict with the Spendee categories.
CATEGORIES = {
    "Housing": ["Rent", "Utilities"],
    "Living": ["Groceries", "Healthcare", "Clothing"],
    "Leisure": ["Entertainment", "Brewing", "Music", "Reading", "Drinks", "Take Away & Restaurant", "Cinema"],
}

# Spendee categories not explicitely listedd in the above map will be joined in this category
DEFAULT_CATEGORY = "Misc"

# This is the category that holds all expenses. Savings + expenses = income.
EXPENSES_CATEGORY = "Expenses"


# Print a line suitable for Sankeymatic
def sankey(source, flow, dest):
    print(source + " [" + str(flow) + "] " + dest)


# Write flows from category to all subcategories and return the total of flow created from category to subcategories
def divide(df, category, subcategories):
    divided = 0
    grouped = df.groupby('Category Name').sum().filter(subcategories, axis=0).sort_values("Amount")
    for subcategory in grouped.iterrows():
        flow = abs(subcategory[1][0])
        divided += flow
        sankey(category, flow, subcategory[0])

    return divided


# Same as above, but going from several categories to a single one. Can we use a common function for both things?
def merge(df, subcategories, category):
    merged = 0
    grouped = df.groupby('Category Name').sum().filter(subcategories, axis=0).sort_values("Amount")
    for subcategory in grouped.iterrows():
        flow = abs(subcategory[1][0])
        merged += flow
        sankey(subcategory[0], flow, category)

    return merged


df = pandas.read_csv("test.csv")

# Remove useless data just clean up output when printing
for col in ['Surname', 'First Name', 'Place', 'Address', 'Wallet', 'Currency']:
    del df[col]

# Gifts can be both income and expense in spendee but we need to use another name in sankey, otherwise the two conflict.
df.loc[(df["Category Type"] == "income") & (df["Category Name"] == "Gifts"), "Category Name"] = "Gifted"

# Aggregate expenses and incomes
balances = df.groupby('Category Type').sum()

# Savings is expenses + incomes
savings = balances.sum()['Amount']

# Also add savings listed as expenses (e.g. savings accounts)
savings -= df.groupby('Category Name').sum().loc['Savings', 'Amount']

income_types = df[(df['Category Type'] == "income")]
merge(income_types, income_types["Category Name"].unique(), "Income")

sankey("Income", savings, "Savings")
sankey("Income", balances.loc['income', 'Amount'] - savings, EXPENSES_CATEGORY)

# expenses without incomes or savings
actual_expenses = df[(df['Category Type'] == "expense") & (df['Category Name'] != 'Savings')]

# Sort categories by largest first
categories_total_amount = lambda map_entry: df[df["Category Name"].isin(map_entry[1])]["Amount"].sum()

for category, subcategories in sorted(CATEGORIES.items(), key=categories_total_amount):
    flow = divide(actual_expenses, category, subcategories)
    sankey(EXPENSES_CATEGORY, flow, category)

# Unassigned categories should go to Disposable directly
# Or should they all go to an "Other" Category?
assigned_subcategories = [i for x in CATEGORIES.values() for i in x]
all_categories = actual_expenses["Category Name"].unique()

flow = divide(actual_expenses, DEFAULT_CATEGORY, [x for x in all_categories if x not in assigned_subcategories])
sankey(EXPENSES_CATEGORY, flow, DEFAULT_CATEGORY)

# test
pie = actual_expenses.groupby("Category Name").sum().abs().plot.pie("Amount")
pie.get_figure().savefig("test.pdf")
