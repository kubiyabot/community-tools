import os

ALLOWED_VENDORS = os.getenv('ALLOWED_VENDORS', 'aws')

SYSTEM_PROMPT_TEMPLATE = """
Your primary task is to extract key details from a given given user input. You should make sure you have CAREFULLY reviewed the user request. 
The following are the ONLY allowed vendors (providers) the user can request resources for: {allowed_vendors}.
If the request is invalid or missing details, respond with an appropriate error message.
** NEVER MAKE UP DETAILS, ATTRIBUTE VALUES, OR VENDORS. **
Put the original user request in the 'natural_language_description' field.

Return a VALID JSON response with the following structure:
{{
    "resource_details": {{}},
    "vendor": "string",
    "natural_language_description": "string",
    "missing_details_message": ""
}}
If there is an error, set the 'missing_details_message' field with the error message.
Request: {user_input}
"""

TERRAFORM_CODE_PROMPT_TEMPLATE = """
Your task is to CAREFULLY review given infrastructure details in a structured format and to return best practice Terraform code that creates the resource(s).
** Make sure your Terraform code follows best practices and can be executed without errors **
Key points to consider:
-> For provider configuration: the execution environment already has access to AWS, so use the default provider configuration from the environment variables.
-> For resource attributes: use the provided resource details to populate the resource attributes.
-> For resource names: use the provided resource details to populate the resource names, don't hardcode them or use random values. Use common naming conventions and common sense.
-> For resource dependencies: ensure that the Terraform code is structured in a way that handles dependencies between resources.
-> For resource outputs: ensure that the Terraform code includes outputs for the created resources. OUTPUTS SHOULD BE UNIQUE - CANNOT USE THE SAME OUTPUT TWICE.
-> For resource tags: ensure that the Terraform code includes tags for the created resources. Only include tags if they are provided in the resource details and if they are relevant to the resource.
-> Make sure to include terraform.tfvars with the fixed values for the variables based on the resource details.
->> TERRAFORM CODE SHOULD BE VALID AND EXECUTABLE WITHOUT ERRORS <<-
Here's the resource details you should convert to Terraform code:
{resource_details}
Your response should include:
1. A dictionary where the keys are filenames and the values are the corresponding file contents.
2. An explanation of what the project contains.
Return A VALID JSON response with the following structure:
{{
    "tf_files": {{}},
    "tf_code_explanation": "string"
}}
"""

TERRAFORM_CODE_FIX_PROMPT_TEMPLATE = """
The following Terraform code did not work due to the error provided. Please correct the code and ensure it is valid.
The definition of what the user requested is as follows:
{resource_details}
The original error message is:
{error_message}
The Terraform code is as follows:
{tf_code}
Return the corrected Terraform code, ensuring it is valid and can be executed without errors.
Make sure the Terraform code you return ARE THE CORRECTED VERSIONS OF THE ORIGINAL CODE. DO NOT MAKE UP LOGIC OR CHANGE THE CODE SIGNIFICANTLY.
Return A VALID JSON response with the following structure:
{{
    "tf_files": {{}},
    "tf_code_explanation": "string"
}}
"""
