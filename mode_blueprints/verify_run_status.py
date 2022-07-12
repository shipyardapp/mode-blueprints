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
    parser.add_argument('--account-id', dest='account_id', required=True)
    parser.add_argument('--report-id', dest='report_id', required=True)
    parser.add_argument('--token-id', dest='token_id', required=True)
    parser.add_argument('--token-password', dest='token_password', required=True)
    parser.add_argument('--run-id', dest='run_id', required=False)
    args = parser.parse_args()
    return args


def get_report_run_data(account_id, report_id, run_id, token_id, token_password):
    """Gets a Run Report Object
    see:https://mode.com/developer/api-reference/analytics/report-runs/#getReportRun
    """
    mode_api_base = f"https://app.mode.com/api/{account_id}"
    get_run_endpoint = mode_api_base + f"/reports/{report_id}/runs/{run_id}"
    headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/hal+json'
    }
    report_request = requests.get(get_run_endpoint,
                                  headers=headers,
                                  auth=HTTPBasicAuth(token_id, token_password))
    
    status_code = report_request.status_code

    run_report_data = report_request.json()
    
    if status_code == 200: # Report get successful
        print("Get run report for ID: {report_id} successful")
        return run_report_data
    
    elif status_code == 401: # Invalid credentials
        print("Mode API returned an Unauthorized response,",
              "check if credentials are correct and try again")
        sys.exit(errors.EXIT_CODE_INVALID_CREDENTIALS)
        
    elif status_code == 404: # Invalid report id
        print("Mode report: report id or run id not found")
        sys.exit(errors.EXIT_CODE_INVALID_REPORT_ID)
        
    else: # some other error
        print(f"Mode run report returned an unknown status {status_code}/n",
              f"returned data: {report_request.text}")
        sys.exit(errors.EXIT_CODE_UNKNOWN_ERROR)

    
    
def handle_run_data(run_report_data):
    run_id = run_report_data['token']
    state = run_report_data['state']
    completed_at = run_report_data['completed_at']
    # handle the various run states
    if state == "succeeded":
        print(f"Report run: {run_id} completed successfully at {completed_at}")
        exit_code = errors.EXIT_CODE_FINAL_STATUS_SUCCESS
    elif state == "completed":
        print(f"Report run {run_id} was completed. completed time: {completed_at}")
        exit_code = errors.EXIT_CODE_FINAL_STATUS_SUCCESS
        
    elif state == "pending":
        print(f"Report run {run_id} is currently pending.")
        exit_code = errors.EXIT_CODE_FINAL_STATUS_PENDING
        
    elif state == "enqueued":
        print(f"Report run {run_id} is enqueued to be run.")
        exit_code = errors.EXIT_CODE_FINAL_STATUS_NOT_STARTED
        
    elif state == "cancelled":
        print(f"Report run {run_id} was cancelled.")
        exit_code = errors.EXIT_CODE_FINAL_STATUS_CANCELLED
    elif state == "failed":
        print(f"Report run {run_id} failed.")    
        exit_code = errors.EXIT_CODE_FINAL_STATUS_FAILED
        
    elif state == "running_notebook":
        print(f"Report run {run_id} is currently running a notebook process.")
        exit_code = errors.EXIT_CODE_FINAL_STATUS_PENDING
        
    else:
        print(f"Unknown status: {state}. check response data for details")
        exit_code = errors.EXIT_CODE_UNKNOWN_ERROR
        
    return exit_code


def main():
    args = get_args()
    token_id = args.token_id
    token_password = args.token_password
    account_id = args.account_id
    report_id = args.report_id
    if args.run_id:
        report_run_id = args.run_id
    else:
        report_run_id = shipyard.logs.read_pickle_file(artifact_subfolder_paths, 
                                                       'report_run_id')
    run_data = get_report_run_data(account_id, 
                        report_id, 
                        report_run_id, 
                        token_id, 
                        token_password)
    
    run_report_file_name = shipyard.files.combine_folder_and_file_name(
        artifact_subfolder_paths['responses'],
        f'verify_run_{report_run_id}_response.json')
    shipyard.files.write_json_to_file(run_data, run_report_file_name)
    
    exit_code = handle_run_data(run_data)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()