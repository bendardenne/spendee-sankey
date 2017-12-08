#!/usr/bin/env python3

# http://sankeymatic.com/build/

import pandas

# Regroup several Spendee categories to more general categories.
# Spendee categories become subcategories here.
# Don't use category names that conflict with the Spendee categories.
CATEGORIES = {
    "Housing": ["Rent", "Utilities"],
    "Living": ["Groceries", "Healthcare", "Clothing" ],
    "Leisure": ["Entertainment", "Brewing", "Music", "Reading", "Drinks", "Take Away & Restaurant", "Cinema"],
}

# Spendee categories not explicitely listedd in the above map will be joined in this category
DEFAULT_CATEGORY = "Others"


# Print a line suitable for Sankeymatic
def sankey(source, flow, dest):
    print(source + " [" + str(flow) + "] " + dest)

# Write flows from category to all subcategories and return the total of flow created from category to subcategories
def divide(df, category, subcategories):
    divided = 0
    for subcategory in df[df['Category Name'].isin(subcategories)].groupby('Category Name').sum().sort_values("Amount").iterrows():
        flow = abs(subcategory[1][0])
        divided += flow
        sankey(category, flow, subcategory[0])

    return divided


def merge(df, subcategories, category):
    merged = 0
    for subcategory in df[df['Category Name'].isin(subcategories)].groupby('Category Name').sum().sort_values("Amount").iterrows():
        flow = abs(subcategory[1][0])
        merged += flow
        sankey(subcategory[0], flow, category)

    return merged


def total_amount_in(df, categories):
    return df[df["Category Name"].isin(categories)].groupby("Category Name").sum().sum()["Amount"]




df = pandas.read_csv("test.csv")

# Remove useless data just clean up output when printing
for col in ['Surname', 'First Name', 'Place', 'Address', 'Wallet', 'Currency']:
    del df[col]

# Aggregate expenses and incomes
balances = df.groupby('Category Type').sum()

# Savings is expenses + incomes
savings = balances.sum().loc['Amount']

# Also add savings listed as expenses (e.g. savings accounts)
savings -= df.groupby('Category Name').sum().loc['Savings', 'Amount']


income_types = df[(df['Category Type'] == "income")]
merge(income_types, ["Salary", "Bonuses" ], "Income")

sankey("Income", savings, "Savings")
sankey("Income", balances.loc['income', 'Amount'] - savings, "Disposable")

# expenses without incomes or savings
actual_expenses = df[(df['Category Type'] == "expense") & (df['Category Name'] != 'Savings')]

# Sort categories by largest first
for category, subcategories in sorted(CATEGORIES.items(), key= lambda category : total_amount_in(actual_expenses, category[1])):
    flow = divide(actual_expenses, category, subcategories)
    sankey("Disposable", flow, category)


# Unassigned categories should go to Disposable directly
# Or should they all go to an "Other" Category?
assigned_subcategories = [i for x in CATEGORIES.values() for i in x]
all_categories = actual_expenses["Category Name"].unique()

filter = actual_expenses["Category Name"].isin(assigned_subcategories)


flow = divide(actual_expenses[-filter], DEFAULT_CATEGORY, [x for x in all_categories if x not in assigned_subcategories])
sankey("Disposable", flow, DEFAULT_CATEGORY)


# test
pie = actual_expenses.groupby("Category Name").sum().abs().plot.pie("Amount")
pie.get_figure().savefig("test.pdf")
