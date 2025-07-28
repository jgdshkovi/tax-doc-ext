import decimal
from typing import Dict, Any

# Set the precision for Decimal calculations
decimal.getcontext().prec = 10

def get_numerical_value(data: Dict[str, Any], keys: list) -> decimal.Decimal:
    """
    Safely extracts a numerical value from a nested dictionary.
    Handles missing keys and non-numeric characters.
    """
    current_data = data
    for i, key in enumerate(keys):
        if key not in current_data:
            return decimal.Decimal(0)
        if i == len(keys) - 1:
            raw_value = str(current_data[key]).replace('$', '').replace(',', '')
            try:
                return decimal.Decimal(raw_value)
            except (decimal.InvalidOperation, ValueError):
                return decimal.Decimal(0)
        current_data = current_data[key]
    return decimal.Decimal(0)

def get_string_value(data: Dict[str, Any], keys: list) -> str:
    """
    Safely extracts a string value from a nested dictionary.
    """
    current_data = data
    for i, key in enumerate(keys):
        if key not in current_data:
            return ""
        if i == len(keys) - 1:
            return str(current_data[key])
        current_data = current_data[key]
    return ""

def calculate_owed_tax(taxable_income: decimal.Decimal) -> decimal.Decimal:
    """
    Calculate Tax Based on 2024 Brackets for Single Filers.
    This is a simplified calculation for demonstration purposes.
    A real tax processor would use precise tax tables.
    """
    # 2024 Tax Brackets for Single Filers
    # Source: https://www.irs.gov/newsroom/irs-provides-tax-inflation-adjustments-for-tax-year-2024
    # (Note: This is a simplified representation of the brackets)
    brackets_2024 = [
        (decimal.Decimal('0'), decimal.Decimal('0.10')),
        (decimal.Decimal('11600'), decimal.Decimal('0.12')),
        (decimal.Decimal('47150'), decimal.Decimal('0.22')),
        (decimal.Decimal('100525'), decimal.Decimal('0.24')),
        (decimal.Decimal('191950'), decimal.Decimal('0.32')),
        (decimal.Decimal('243725'), decimal.Decimal('0.35')),
        (decimal.Decimal('609350'), decimal.Decimal('0.37'))
    ]

    owed_tax = decimal.Decimal(0)
    remaining_income = taxable_income

    for i, (bracket_start, rate) in enumerate(brackets_2024):
        if remaining_income <= 0:
            break

        if i == len(brackets_2024) - 1: # Last bracket (top rate)
            owed_tax += remaining_income * rate
            remaining_income = decimal.Decimal(0)
        else:
            next_bracket_start = brackets_2024[i+1][0]
            taxable_in_bracket = min(remaining_income, next_bracket_start - bracket_start)
            owed_tax += taxable_in_bracket * rate
            remaining_income -= taxable_in_bracket

    return owed_tax.quantize(decimal.Decimal("0.01"))


def calculate_form_1040_values(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates and populates Form 1040 fields based on provided tax data.

    Args:
        data (Dict[str, Any]): A dictionary containing extracted data from
                               various tax forms and schedules.

    Returns:
        Dict[str, Any]: A dictionary with calculated Form 1040 fields.
    """
    # Personal Information (from any relevant form)
    # Prioritizing W2 for employee info, then Schedule 1, then 8863
    tax_payer_first_name_and_middle_initial = get_string_value(data, ['form_w2', 'employee_first_name']) or \
                 get_string_value(data, ['schedule_1', 'name_of_the_taxpayer']).split(' ')[0] or \
                 get_string_value(data, ['schedule_2', 'name_of_the_taxpayer']).split(' ')[0] or \
                 get_string_value(data, ['schedule_3', 'name_of_the_taxpayer']).split(' ')[0] or \
                 get_string_value(data, ['form_8863', 'name_shown_on_return']).split(' ')[0]

    tax_payer_last_name = get_string_value(data, ['form_w2', 'employee_last_name']) or \
                get_string_value(data, ['schedule_1', 'name_of_the_taxpayer']).split(' ')[-1] or \
                get_string_value(data, ['schedule_2', 'name_of_the_taxpayer']).split(' ')[-1] or \
                get_string_value(data, ['schedule_3', 'name_of_the_taxpayer']).split(' ')[-1] or\
                get_string_value(data, ['form_8863', 'name_shown_on_return']).split(' ')[-1] 
                

    tax_payer_ssn = get_string_value(data, ['form_w2', 'employee_social_security_number']) or \
          get_string_value(data, ['schedule_1', 'social_security_number']) or \
          get_string_value(data, ['schedule_2', 'social_security_number']) or \
          get_string_value(data, ['schedule_3', 'social_security_number']) or \
          get_string_value(data, ['form_8863', 'social_security_number']) 
          

    # Standard Deduction for Single Filing in 2024
    # Source: https://www.irs.gov/newsroom/irs-provides-tax-inflation-adjustments-for-tax-year-2024
    standard_deduction_2024_single = decimal.Decimal('14600')

    # Initialize 1040 fields dictionary
    form_1040_fields = {
        "tax_payer_first_name_and_middle_initial": tax_payer_first_name_and_middle_initial,
        "tax_payer_last_name": tax_payer_last_name,
        "tax_payer_ssn": tax_payer_ssn.replace('-', ''),
        "tax_year_last_2_digits": "24", # Assuming 2024 for 1040 as per summary
    }

    # Part I: Income
    LINE1a_total_amount_from_w2 = get_numerical_value(data, ['form_w2', 'wages_tips_other_compensation'])
    LINE1h_other_earned_income = get_numerical_value(data, ['form_1099_nec', 'nonemployee_compensation'])
    LINE1z_sum_lines_1a_through_1h_total_ie_from_w2_through_other_income = LINE1a_total_amount_from_w2 + LINE1h_other_earned_income
    LINE8_additional_income_from_schedule1 = get_numerical_value(data, ['schedule_1', 'total_additional_income'])
    LINE9_sum_income_lines_1z_to_8_from_prev_sum_to_additional_income = LINE1z_sum_lines_1a_through_1h_total_ie_from_w2_through_other_income + LINE8_additional_income_from_schedule1 # Assuming other lines (2b, 3b, 4b, 5b, 6b, 7) are 0 for this data
    LINE10_adjustments_to_income_from_sched1 = get_numerical_value(data, ['schedule_1', 'total_adjustments_to_income'])
    LINE11_adjusted_gross_income_equals_total_income_minus_adjustments = LINE9_sum_income_lines_1z_to_8_from_prev_sum_to_additional_income - LINE10_adjustments_to_income_from_sched1

    form_1040_fields.update({
        "LINE1a_total_amount_from_w2": LINE1a_total_amount_from_w2,
        "LINE1h_other_earned_income": LINE1h_other_earned_income,
        "LINE1z_sum_lines_1a_through_1h_total_ie_from_w2_through_other_income": LINE1z_sum_lines_1a_through_1h_total_ie_from_w2_through_other_income,
        "LINE8_additional_income_from_schedule1": LINE8_additional_income_from_schedule1,
        "LINE9_sum_income_lines_1z_to_8_from_prev_sum_to_additional_income": LINE9_sum_income_lines_1z_to_8_from_prev_sum_to_additional_income,
        "LINE10_adjustments_to_income_from_sched1": LINE10_adjustments_to_income_from_sched1,
        "LINE11_adjusted_gross_income_equals_total_income_minus_adjustments": LINE11_adjusted_gross_income_equals_total_income_minus_adjustments,
    })

    # Part II: Tax and Credits
    LINE12_standard_deductions_or_itemized_deductions = standard_deduction_2024_single # Assuming single filing status
    LINE13_qbi_deduction_form_8995 = decimal.Decimal(0) # Not provided in input
    LINE14_total_deductions_add_line12_and_line13 = LINE12_standard_deductions_or_itemized_deductions + LINE13_qbi_deduction_form_8995
    LINE15_taxable_income = max(decimal.Decimal(0), LINE11_adjusted_gross_income_equals_total_income_minus_adjustments - LINE14_total_deductions_add_line12_and_line13)
    LINE16_calculated_tax = calculate_owed_tax(LINE15_taxable_income) # Using the simplified tax calculation
    LINE17_amount_tax_schedule2_line3 = get_numerical_value(data, ['schedule_2', 'total_part1_tax'])
    LINE18_SUM_LINE16_AND_17 = LINE16_calculated_tax + LINE17_amount_tax_schedule2_line3
    LINE19_child_and_dependent_tax_credit_from_schedule_8812 = get_numerical_value(data, ['schedule_8812', 'child_tax_credit_and_credit_for_other_dependents'])
    LINE20_amount_from_sched3_line8 = get_numerical_value(data, ['schedule_3', 'total_nonrefundable_credits'])
    LINE21_SUM_LINE19_AND_20 = LINE19_child_and_dependent_tax_credit_from_schedule_8812 + LINE20_amount_from_sched3_line8
    LINE22_equals_line18_minus_line21_if_positive_else_0 = max(decimal.Decimal(0), LINE18_SUM_LINE16_AND_17 - LINE21_SUM_LINE19_AND_20)
    LINE23_other_taxes_from_sched2_line21 = get_numerical_value(data, ['schedule_2', 'total_other_taxes'])
    LINE24_total_tax_add_line22_and_line23 = LINE22_equals_line18_minus_line21_if_positive_else_0 + LINE23_other_taxes_from_sched2_line21

    form_1040_fields.update({
        "LINE12_standard_deductions_or_itemized_deductions": LINE12_standard_deductions_or_itemized_deductions,
        "LINE13_qbi_deduction_form_8995": LINE13_qbi_deduction_form_8995,
        "LINE14_total_deductions_add_line12_and_line13": LINE14_total_deductions_add_line12_and_line13,
        "LINE15_taxable_income": LINE15_taxable_income,
        "LINE16_calculated_tax": LINE16_calculated_tax,
        "LINE17_amount_tax_schedule2_line3": LINE17_amount_tax_schedule2_line3,
        "LINE18_SUM_LINE16_AND_17": LINE18_SUM_LINE16_AND_17,
        "LINE19_child_and_dependent_tax_credit_from_schedule_8812": LINE19_child_and_dependent_tax_credit_from_schedule_8812,
        "LINE20_amount_from_sched3_line8": LINE20_amount_from_sched3_line8,
        "LINE21_SUM_LINE19_AND_20": LINE21_SUM_LINE19_AND_20,
        "LINE22_equals_line18_minus_line21_if_positive_else_0": LINE22_equals_line18_minus_line21_if_positive_else_0,
        "LINE23_other_taxes_from_sched2_line21": LINE23_other_taxes_from_sched2_line21,
        "LINE24_total_tax_add_line22_and_line23": LINE24_total_tax_add_line22_and_line23,
    })

    # Part III: Payments
    LINE25a_fed_withholding_w2 = get_numerical_value(data, ['form_w2', 'federal_income_tax_withheld'])
    LINE25b_fed_withholding_1099 = get_numerical_value(data, ['form_1099_nec', 'federal_income_tax_withheld'])
    LINE25c_fed_withholding_other_forms = decimal.Decimal(0) # Not provided in input
    LINE25d_fed_total_withholding_payments_sum_25a_25b_25c = LINE25a_fed_withholding_w2 + LINE25b_fed_withholding_1099 + LINE25c_fed_withholding_other_forms
    LINE26_estimated_tax_payments = decimal.Decimal(0) # Not provided in input (EIC)
    LINE27_earned_income_credit = decimal.Decimal(0) # Not provided in input (Estimated tax payments)
    LINE28_additional_child_tax_credit_from_schedule_8812 = get_numerical_value(data, ['schedule_8812', 'additional_child_tax_credit'])
    LINE29_american_opportunity_credit_from_schedule_8863_line8 = get_numerical_value(data, ['form_8863', 'refundable_american_opportunity_credit'])
    LINE31_amount_from_sched3_line15 = get_numerical_value(data, ['schedule_3', 'total_payments_and_refundable_credits'])
    LINE32_total_other_payments_or_refundable_credits_sum_lines_27_28_29_31 = LINE26_estimated_tax_payments + LINE27_earned_income_credit + LINE28_additional_child_tax_credit_from_schedule_8812 + LINE29_american_opportunity_credit_from_schedule_8863_line8 + LINE31_amount_from_sched3_line15
    LINE33_total_payments_add_lines_25d_26_32 = LINE25d_fed_total_withholding_payments_sum_25a_25b_25c + LINE26_estimated_tax_payments + LINE32_total_other_payments_or_refundable_credits_sum_lines_27_28_29_31

    form_1040_fields.update({
        "LINE25a_fed_withholding_w2": LINE25a_fed_withholding_w2,
        "LINE25b_fed_withholding_1099": LINE25b_fed_withholding_1099,
        "LINE25c_fed_withholding_other_forms": LINE25c_fed_withholding_other_forms,
        "LINE25d_fed_total_withholding_payments_sum_25a_25b_25c": LINE25d_fed_total_withholding_payments_sum_25a_25b_25c,
        "LINE26_estimated_tax_payments": LINE26_estimated_tax_payments, # This was EIC in the previous mapping, but now it's estimated tax payments
        "LINE27_earned_income_credit": LINE27_earned_income_credit, # This was estimated tax payments in the previous mapping, but now it's EIC
        "LINE28_additional_child_tax_credit_from_schedule_8812": LINE28_additional_child_tax_credit_from_schedule_8812,
        "LINE29_american_opportunity_credit_from_schedule_8863_line8": LINE29_american_opportunity_credit_from_schedule_8863_line8,
        "LINE31_amount_from_sched3_line15": LINE31_amount_from_sched3_line15,
        "LINE32_total_other_payments_or_refundable_credits_sum_lines_27_28_29_31": LINE32_total_other_payments_or_refundable_credits_sum_lines_27_28_29_31,
        "LINE33_total_payments_add_lines_25d_26_32": LINE33_total_payments_add_lines_25d_26_32,
    })

    # Part IV: Refund or Amount You Owe
    LINE34_overpayment_amount_line33_minus_line24_if_positive_else_0 = decimal.Decimal(0)
    LINE35a_wanted_refund_amount = decimal.Decimal(0)
    LINE36_amount_from_line_34_you_want_applied_to_next_year_credit = decimal.Decimal(0)
    LINE37_amount_you_owe_line24_minus_line33 = decimal.Decimal(0)

    if LINE33_total_payments_add_lines_25d_26_32 > LINE24_total_tax_add_line22_and_line23:
        LINE34_overpayment_amount_line33_minus_line24_if_positive_else_0 = LINE33_total_payments_add_lines_25d_26_32 - LINE24_total_tax_add_line22_and_line23
        LINE35a_wanted_refund_amount = LINE34_overpayment_amount_line33_minus_line24_if_positive_else_0 # Assuming full refund unless specified otherwise
    else:
        LINE37_amount_you_owe_line24_minus_line33 = LINE24_total_tax_add_line22_and_line23 - LINE33_total_payments_add_lines_25d_26_32

    form_1040_fields.update({
        "LINE34_overpayment_amount_line33_minus_line24_if_positive_else_0": LINE34_overpayment_amount_line33_minus_line24_if_positive_else_0,
        "LINE35a_wanted_refund_amount": LINE35a_wanted_refund_amount,
        "LINE36_amount_from_line_34_you_want_applied_to_next_year_credit": LINE36_amount_from_line_34_you_want_applied_to_next_year_credit, # Not specified, assuming 0
        "LINE37_amount_you_owe_line24_minus_line33": LINE37_amount_you_owe_line24_minus_line33,
    })

    return form_1040_fields

# Example Usage with your provided data:
final_forms_data = {
    'form_1099_nec': {
        'calendar_year': '2025',
        'federal_income_tax_withheld': '764',
        'form_name': 'Form 1099-NEC',
        'payer_name_and_address': 'John Doe, 2201 E 6th St, Bloomington, IL 61701',
        'payer_tin': '98723123450',
        'nonemployee_compensation': '322'
    },
    'form_8863': {
        'form_name': 'Form 8863',
        'name_shown_on_return': 'Jane Doe',
        'refundable_american_opportunity_credit': '0',
        'social_security_number': '123\n45 1234',
        'tax_year': '2024'
    },
    'form_w2': {
        'employee_first_name': 'Jane',
        'employee_last_name': 'Doe',
        'employee_social_security_number': '123-45-1234',
        'federal_income_tax_withheld': '7500',
        'form_name': 'W-2 Wage and Tax Statement',
        'tax_year': '2025',
        'wages_tips_other_compensation': '50000'
    },
    'schedule_1': {
        'form_name': 'SCHEDULE 1\n(Form 1040)',
        'name_of_the_taxpayer': 'Jane Doe',
        'social_security_number': '123-45-1234',
        'tax_year': '2024',
        'total_additional_income': '4427',
        'total_adjustments_to_income': '190'
    },
    'schedule_2': {
        'form_name': 'SCHEDULE 2 (Form 1040)',
        'name_of_the_taxpayer': 'Jane Doe',
        'social_security_number': '123-45-1234',
        'tax_year': '2024',
        'total_other_taxes': '2500',
        'total_part1_tax': '0'
    },
    'schedule_3': {
        'form_name': 'SCHEDULE 3\n(Form 1040)',
        'name_of_the_taxpayer': 'Jane Doe',
        'social_security_number': '123-45-1234',
        'tax_year': '2024',
        'total_nonrefundable_credits': '250',
        'total_payments_and_refundable_credits': '0'
    },
    'schedule_8812': {
        'additional_child_tax_credit': '0',
        'child_tax_credit_and_credit_for_other_dependents': '4500',
        'form_name': 'Schedule 8812 (Form 1040)',
        'name_shown_on_return': 'Jane Doe',
        'social_security_number': '123-45-1234',
        'tax_year': '2024'
    }
}

# Example usage - only runs when file is executed directly
if __name__ == '__main__':
    # Calculate the 1040 values using the final_forms_data
    calculated_1040_data = calculate_form_1040_values(final_forms_data)

    # Print the results
    print(type(calculated_1040_data))
    for line, value in calculated_1040_data.items():
        print(f"{line}: {value}")
