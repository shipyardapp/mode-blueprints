import argparse
import sys
import os
import requests
from requests.auth import HTTPBasicAuth
import shipyard_utils as shipyard
try:
    import errors
except BaseException:
    from . import errors

# create Artifacts folder paths
base_folder_name = shipyard.logs.determine_base_artifact_folder('mode')
artifact_subfolder_paths = shipyard.logs.determine_artifact_subfolders(
    base_folder_name)
shipyard.logs.create_artifacts_folders(artifact_subfolder_paths)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--account-name', dest='account_name', required=True)
    parser.add_argument('--report-id', dest='report_id', required=True)
    parser.add_argument('--token-id', dest='token_id', required=True)
    parser.add_argument('--token-password',
                        dest='token_password',
                        required=True)
    parser.add_argument('--run-id', dest='run_id', required=False)
    parser.add_argument('--dest-file-name',
                        dest='dest_file_name',
                        required=True)
    parser.add_argument('--dest-folder-name',
                        dest='dest_folder_name',
                        required=False)
    parser.add_argument('--file-type',
                        dest='file_type',
                        choices=['json', 'pdf', 'csv'],
                        type=str.lower,
                        required=True)
    args = parser.parse_args()
    return args


def get_report_results(account_name, report_id, run_id, token_id, token_password,
                       file_type):
    """Download report as file
    see:https://mode.com/developer/api-reference/analytics/report-runs/#getReportRun
    """
    mode_api_base = f"https://app.mode.com/api/{account_name}"
    results_api = mode_api_base + f"/reports/{report_id}/runs/{run_id}/results/"
    results_endpoint = results_api + f'content.{file_type}'
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/hal+json'
    }
    print(results_endpoint)
    report_request = requests.get(results_endpoint,
                                  headers=headers,
                                  auth=HTTPBasicAuth(token_id, token_password),
                                  stream=True)

    status_code = report_request.status_code

    if status_code == 200:
        return report_request

    elif status_code == 401:  # Invalid credentials
        print("Mode API returned an Unauthorized response,",
              "check if credentials are correct and try again")
        sys.exit(errors.EXIT_CODE_INVALID_CREDENTIALS)

    elif status_code == 404:  # Invalid run
        print("Mode report: report id or run id not found")
        sys.exit(errors.EXIT_CODE_INVALID_REPORT_ID)

    else:  # some other error
        print(f"Mode run report returned an unknown status {status_code}/n",
              f"returned data: {report_request.text}")
        sys.exit(errors.EXIT_CODE_UNKNOWN_ERROR)


def get_report_result_as_pdf(account_name, report_id, run_id, token_id,
                             token_password):
    mode_api_base = f"https://app.mode.com/api/{account_name}"
    pdf_data_url = mode_api_base + f"/reports/{report_id}/exports/runs/{run_id}/pdf/download"
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/hal+json'
    }
    report_request = requests.get(pdf_data_url,
                                  headers=headers,
                                  auth=HTTPBasicAuth(token_id, token_password),
                                  stream=True)
    status_code = report_request.status_code
    if status_code == 200:
        return report_request

    elif status_code == 401:  # Invalid credentials
        print("Mode API returned an Unauthorized response,",
              "check if credentials are correct and try again")
        sys.exit(errors.EXIT_CODE_INVALID_CREDENTIALS)

    elif status_code == 404:  # Invalid run
        print("Mode report: report id or run id not found")
        sys.exit(errors.EXIT_CODE_INVALID_REPORT_ID)

    else:  # some other error
        print(f"Mode run report returned an unknown status {status_code}\n",
              f"returned data: {report_request.text}")
        sys.exit(errors.EXIT_CODE_UNKNOWN_ERROR)


def main():
    args = get_args()
    token_id = args.token_id
    token_password = args.token_password
    account_name = args.account_name
    report_id = args.report_id
    file_type = args.file_type
    # get run_id from pickle if not specified
    if args.run_id:
        run_id = args.run_id
    else:
        run_id = shipyard.logs.read_pickle_file(artifact_subfolder_paths,
                                                'report_run_id')
    dest_file_name = args.dest_file_name
    dest_folder_name = args.dest_folder_name

    # get cwd if no folder name is specified
    if not dest_folder_name:
        dest_folder_name = os.getcwd()
    destination_file_path = shipyard.files.combine_folder_and_file_name(
        dest_folder_name, dest_file_name)

    # if the file type specified is pdf, run a fetch pdf after running get results
    if file_type == 'pdf':
        result = get_report_result_as_pdf(account_name, report_id, run_id,
                                          token_id, token_password)
    else:  # csv and json retrieve
        result = get_report_results(account_name, report_id, run_id, token_id,
                                    token_password, file_type)
    with open(destination_file_path, 'wb+') as f:
        f.write(result.content)


if __name__ == "__main__":
    main()
