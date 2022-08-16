import argparse
import sys
import requests
from requests.auth import HTTPBasicAuth
import shipyard_utils as shipyard
try:
    import errors
except BaseException:
    from . import errors

# create Artifacts folder paths
base_folder_name = shipyard.logs.determine_base_artifact_folder(
    'mode')
artifact_subfolder_paths = shipyard.logs.determine_artifact_subfolders(
    base_folder_name)
shipyard.logs.create_artifacts_folders(artifact_subfolder_paths)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--account-name', dest='account_name', required=True)
    parser.add_argument('--report-id', dest='report_id', required=True)
    parser.add_argument('--token-id', dest='token_id', required=True)
    parser.add_argument(
        '--token-password',
        dest='token_password',
        required=True)
    args = parser.parse_args()
    return args


def execute_run_report(account_name, report_id, token_id, token_password):
    """Executes a mode report run
    see: https://mode.com/developer/api-reference/analytics/report-runs/#runReport
    """
    mode_api_base = f"https://app.mode.com/api/{account_name}"
    run_report_endpoint = mode_api_base + f"/reports/{report_id}/runs"
    parameters = {}

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/hal+json'
    }
    report_request = requests.post(
        run_report_endpoint,
        data=parameters,
        headers=headers,
        auth=HTTPBasicAuth(
            token_id,
            token_password))
    status_code = report_request.status_code

    # save report data
    run_report_data = report_request.json()

    run_report_file_name = shipyard.files.combine_folder_and_file_name(
        artifact_subfolder_paths['responses'],
        f'sync_run_{report_id}_response.json')
    shipyard.files.write_json_to_file(run_report_data, run_report_file_name)

    # handle reponse codes
    if status_code == 202:  # Report run successful
        print(f"Run report for ID: {report_id} was successfully triggered.")
        return run_report_data

    elif status_code == 400:  # Bad request
        print("Bad request sent to Mode. Response data: {report_request.text}")
        sys.exit(errors.EXIT_CODE_BAD_REQUEST)

    elif status_code == 401:  # Invalid credentials
        print("Mode API returned an Unauthorized response,",
              "check if credentials are correct and try again")
        sys.exit(errors.EXIT_CODE_INVALID_CREDENTIALS)

    elif status_code == 404:  # Invalid report id
        if 'account not found' in report_request.text:
            print("Mode reports: account not found")
            sys.exit(errors.EXIT_CODE_INVALID_ACCOUNT)
        elif 'report not found' in report_request.text:
            print("Mode reports: report not found")
            sys.exit(errors.EXIT_CODE_INVALID_REPORT_ID)
        sys.exit(errors.EXIT_CODE_UNKNOWN_ERROR)

    elif status_code == 403:  # Account not accessible
        print(
            "Mode Account provided is not accessible,"
            "Check if account is correct and try again")
        sys.exit(errors.EXIT_CODE_INVALID_CREDENTIALS)
    elif status_code == 500:
        print("Mode encountered an Error trying your request.",
              f"Check if Report ID: {report_id} is correct")
        sys.exit(errors.EXIT_CODE_BAD_REQUEST)
    else:  # some other error
        print(f"Mode run report returned an unknown status {status_code}/n",
              f"returned data: {report_request.text}")
        sys.exit(errors.EXIT_CODE_UNKNOWN_ERROR)


def main():
    args = get_args()
    token_id = args.token_id
    token_password = args.token_password
    account_name = args.account_name
    report_id = args.report_id

    # execute run report
    report_data = execute_run_report(account_name,
                                     report_id,
                                     token_id,
                                     token_password)

    # get run report id and save as pickle
    report_run_id = report_data['token']
    print(f"Report run id is: {report_run_id}")

    shipyard.logs.create_pickle_file(artifact_subfolder_paths,
                                     'report_run_id', report_run_id)


if __name__ == "__main__":
    main()
